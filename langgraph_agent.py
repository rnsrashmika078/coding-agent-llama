import json
from typing import Literal


from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.config import get_stream_writer, get_config

# from IPython.display import Image, display
from langchain_ollama import ChatOllama
from model import CustomState
from pydantic import BaseModel, Field

llm = ChatOllama(model="gemma4:e2b", reasoning=False)


# Graph state
class State(TypedDict):
    task: str
    content: str
    absolute_path: str
    fileTree: str
    task_status: Literal["Failed", "Success"]


class FilePathStructuredOutput(BaseModel):
    absolute_path: str = Field(
        ..., description="suitable Absolute directory path to the file"
    )


class FileContentStructuredOutput(BaseModel):
    content: str = Field(..., description="suitable file content to the file")


# Nodes
def determine_file_path(
    state: State,
) -> dict:
    """Scan the project absolute path and return a suitable absolute path/directory according to the task. NO PREAMBLE"""

    writer = get_stream_writer()
    writer({"status": "Scanning project path ..."})
    prompt = f"""
    YOU ARE ABSOLUTE PATH FINDER
    You MUST return ONLY valid JSON.

    Output format:
    {{"absolute_path": "string"}}
    Task:
    {state['task']}

    File Tree:
    {state['fileTree']}

    Rules:
    - Only return JSON
    - Do NOT explain
    - Do NOT add extra text
    """

    structured_llm = llm.with_structured_output(FilePathStructuredOutput)
    result: FilePathStructuredOutput = structured_llm.invoke(prompt)
    print("STRUCTURED OUTPUT:", result)
    return {"absolute_path": result.absolute_path}


def isPathAvailable(state: State):
    """check weather the state path available"""

    writer = get_stream_writer()
    writer({"status": "Checking Path Availability..."})

    if state["absolute_path"] is None:
        return "Fail"
    return "Pass"


def generate_file_content(
    state: State,
) -> dict:
    """generate file content according to the task"""

    writer = get_stream_writer()
    writer({"status": "Generating file content..."})
    prompt = f"""
    YOU ARE CONTENT GENERATOR
    Generate file content based on TASK
    You MUST return ONLY valid JSON.
    
     Output format:
    {{"content": "string"}}
    
    Task : {state['task']}
    
    Rules:
    - Only return JSON
    - Do NOT explain
    - GENERATE JUST CONTENT ONLY 
    """

    structured_llm = llm.with_structured_output(FileContentStructuredOutput)
    result: FileContentStructuredOutput = structured_llm.invoke(prompt)
    print("FILE CONTENT:", result)
    return {"content": result.content}


def generate_file(
    state: State,
) -> str:
    """use to create/generate file"""

    writer = get_stream_writer()
    writer({"status": "Generating file ..."})
    path = state["absolute_path"]
    content = state["content"]
    try:
        with open(path, "w") as f:
            f.write(content)
            return {"task_status": "Success"}
    except Exception as e:
        return {"task_status": "Failed"}


def run_langgraph(
    task: str,
    runtime: ToolRuntime[None, CustomState],
):
    """Langgraph agent that work with the file system

    Args:
        task (str): Task user given to you


    """

    writer = get_stream_writer()

    workflow = StateGraph(State)
    workflow.add_node("determine_path", determine_file_path)
    workflow.add_node("content_generate", generate_file_content)
    workflow.add_node("file_generation", generate_file)

    # config = get_config()
    # runtime_state = config.get("configurable", {})
    # path = runtime_state.get("rootPath")

    tree = runtime.state.get("fileTree")
    # path = runtime.state.get("rootPath")
    tree_str = json.dumps(tree, indent=2)
    print(f"Tree: {tree}")

    if tree_str is None:
        return
    workflow.add_edge(START, "determine_path")
    workflow.add_conditional_edges(
        "determine_path", isPathAvailable, {"Fail": END, "Pass": "content_generate"}
    )
    workflow.add_edge("content_generate", "file_generation")
    workflow.add_edge("file_generation", END)

    chain = workflow.compile()
    full_state = {}

    for chunk in chain.stream(
        {"task": task, "fileTree": tree_str},
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, state in chunk["data"].items():
                print(f"Node {node_name} updated: {state}")
                full_state.update(state)
        if chunk["type"] == "custom":
            print(f"Status: {chunk['data']['status']}")
            writer(f"{chunk['data']['status']}")

    state = full_state
    return {
        "absolute_path": state.get("absolute_path"),
        "content": state.get("content"),
    }
