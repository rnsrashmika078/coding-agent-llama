from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from langchain.agents import AgentState, create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_protocol import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langgraph.graph import add_messages
from langchain.agents.middleware import HumanInTheLoopMiddleware
from secondary_tools import internet_search
from sub_agents import call_research_agent, call_traversal_agent
from model_tools import (
    CustomState,
    get_weather,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = ChatOllama(model="gemma4:e2b", reasoning=False)


@app.post("/api/stream")
async def stream_response(request: Request):
    try:
        body = await request.json()
        print(f"BODY: {body}")

        payload = body.get("input", body)
        thread_id = payload.get("threadId", "chat123")
        interrupt_response = payload.get("interruptResponse")

        config = {
            "configurable": {
                "thread_id": thread_id,
                "rootPath": payload.get("rootPath"),
                "referenceFile": payload.get("referenceFile"),
                "error": payload.get("error"),
            },
            "recursion_limit": 25,
        }

        if interrupt_response:
            input_data = Command(
                resume={"decisions": interrupt_response.get("decisions")}
            )
        else:
            messages = payload.get("messages", [])
            first_msg_content = messages[0].get("content", "") if messages else ""
            input_data = {"messages": [HumanMessage(content=first_msg_content)]}

        agent = create_agent(
            llm,
            tools=[internet_search, get_weather],
            system_prompt="You are an expert React Vite developer. answer in very short. like 1 ",
            state_schema=CustomState,
            checkpointer=MemorySaver(),
        )

        # Replicate the Next.js multi-stream mode generator
        async def generate():
            try:
                async for stream_mode, data in agent.astream(
                    input_data,
                    config=config,
                    stream_mode=["updates", "messages", "values", "tools", "custom"],
                ):

                    print(data)

                    def clean_object(obj):
                        # Handle BaseMessage subclasses explicitly
                        if isinstance(obj, BaseMessage):
                            data = {
                                "type": obj.type,
                                "content": obj.content,
                                "id": getattr(obj, "id", None),
                                "additional_kwargs": getattr(
                                    obj, "additional_kwargs", {}
                                ),
                                "response_metadata": getattr(
                                    obj, "response_metadata", {}
                                ),
                            }
                            # Add ToolMessage specific fields
                            if isinstance(obj, ToolMessage):
                                data["tool_call_id"] = obj.tool_call_id
                                data["artifact"] = obj.artifact
                            # Add AIMessage specific fields
                            if isinstance(obj, AIMessage):
                                data["tool_calls"] = obj.tool_calls
                            return data

                        elif hasattr(obj, "model_dump"):
                            return obj.model_dump()

                        elif isinstance(obj, dict):
                            return {k: clean_object(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)):
                            return [clean_object(item) for item in obj]

                        return obj

                    formatted_data = clean_object(data)

                    yield f"event: {stream_mode}\n"
                    yield f"data: {json.dumps(formatted_data)}\n\n"

            except Exception as e:
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                # "X-Accel-Buffering": "no",
            },
        )

    except Exception as err:
        return {"error": str(err)}, 500
