from langchain.agents import AgentState, create_agent
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langgraph.graph import add_messages

from langgraph_agent import run_langgraph
from model_tools import (
    CustomState,
    create_react_app,
    get_current_working_directory,
    get_weather,
    run_react_app,
    run_terminal_command,
    create_react_files,
)
from langchain.agents.middleware import HumanInTheLoopMiddleware
from sub_agents import call_research_agent, call_traversal_agent


llm = ChatOllama(model="gemma4:e2b", reasoning=True)
agent = create_agent(
    llm,
    tools=[
        # get_weather,
        # create_react_app,
        # run_react_app,
        # run_terminal_command,
        # create_react_files,
        # get_current_working_directory,
        # call_research_agent,
        # call_traversal_agent,
        # call_deep_agent,
        run_langgraph,
    ],
    system_prompt="""
You are an expert React Vite developer AI agent inside an Electron app.

You MUST follow this loop:

1. THINK: decide what to do
2. TOOL: call a tool if needed
3. OBSERVE: read the result
4. REPEAT until task is complete
5. FINAL: give final answer

Rules:
- You can call MULTIPLE tools step by step
- After each tool call, you MUST continue reasoning
- DO NOT stop after one tool if task is incomplete
- ALWAYS prefer tools for project-related actions
- Each user request is independent (stateless)

Available tools:
- run_langgraph → for file related operations: example : Create/generate files
""",
    state_schema=CustomState,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                # "get_weather": True,
                # "create_react_app": True,
                # "run_react_app": True,
                "run_terminal_command": True,
                "call_traversal_agent": True,
                # "get_current_working_directory": False,
                # "research": False,
                # "deep_agent": False,
                # "call_traversal_agent": True,
                "run_langgraph": False,
                # "create_files": True,
            }
        ),
    ],
    # checkpointer=MemorySaver(),
)
