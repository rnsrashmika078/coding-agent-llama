from typing import TypedDict, Annotated

from langchain.agents import AgentState
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class CustomState(AgentState):
    messages: Annotated[list[BaseMessage], add_messages]
    # rootPath: str
    # fileTree: str
