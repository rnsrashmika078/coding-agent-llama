from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from langchain.agents import AgentState, create_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_protocol import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langgraph.graph import add_messages
from langchain.agents.middleware import HumanInTheLoopMiddleware
from model import CustomState
from sub_agents import call_research_agent, call_traversal_agent


# initialize fastapi
app = FastAPI()

# handle cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# import tools
from model_tools import (
    # CustomState,
    get_weather,
)

llm = ChatOllama(model="gemma4:e2b", reasoning=True)


@app.post("/api/stream")
async def stream_response(request: Request):
    try:
        body = await request.json()
        print(f"BODY: {body}")

        # Extract metadata mirroring your Next.js setup
        # Note: adjust the dictionary keys if your frontend payload wraps it inside 'input'
        payload = body.get("input", body)
        thread_id = payload.get("threadId", "chat123")
        interrupt_response = payload.get("interruptResponse")

        # Build configuration state
        config = {
            "configurable": {
                "thread_id": thread_id,
                "rootPath": payload.get("rootPath"),
                "referenceFile": payload.get("referenceFile"),
                "messageId": payload.get("messageId"),
                "error": payload.get("error"),
            },
            "recursion_limit": 25,
        }

        # Replicate input selection: Command resume vs New Human Message
        if interrupt_response:
            # Matches: new Command({ resume: { decisions: ... } })
            input_data = Command(
                resume={"decisions": interrupt_response.get("decisions")}
            )
        else:
            messages = payload.get("messages", [])
            first_msg_content = messages[0].get("content", "") if messages else ""
            input_data = {"messages": [HumanMessage(content=first_msg_content)]}

        # Initialize agent instance
        agent = create_agent(
            llm,
            tools=[get_weather],
            system_prompt="You are an expert React Vite developer.",
            state_schema=CustomState,
            checkpointer=MemorySaver(),
        )

        # Replicate the Next.js multi-stream mode generator
        async def generate():
            try:
                async for stream_mode, data in agent.astream(
                    input_data,
                    config=config,
                    stream_mode=["updates", "messages", "values", "tools", "custom"]
                ):
                    # Inner helper function to clean ANY object recursively
                    def clean_object(obj):
                        # 1. If it's a LangChain Message/Chunk object, strip it to a dictionary
                        if isinstance(obj, BaseMessage):
                            return {
                                "type": obj.type,
                                "content": obj.content,
                                "id": getattr(obj, "id", None),
                                "additional_kwargs": getattr(obj, "additional_kwargs", {}),
                                "response_metadata": getattr(obj, "response_metadata", {})
                            }
                        # 2. If it's a Pydantic object, dump it
                        elif hasattr(obj, "model_dump"):
                            return obj.model_dump()
                        # 3. If it's a dictionary, clean its keys and values
                        elif isinstance(obj, dict):
                            return {k: clean_object(v) for k, v in obj.items()}
                        # 4. If it's a list or tuple, clean every item inside it
                        elif isinstance(obj, (list, tuple)):
                            return [clean_object(item) for item in obj]
                        # 5. Otherwise, it's a primitive (str, int, bool) and is perfectly safe
                        return obj

                    # Clean the entire data block completely
                    formatted_data = clean_object(data)

                    # Send standard SSE streams matching what Next.js sends
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
                "X-Accel-Buffering": "no",  # Prevents Nginx from buffering streams
            },
        )

    except Exception as top_level_e:
        return {"error": str(top_level_e)}, 500
