import json
from typing import Literal
import os

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.config import get_stream_writer, get_config

# from IPython.display import Image, display
from langchain_ollama import ChatOllama
from model import CustomState
from pydantic import BaseModel, Field

from utils.read_files import recall_project_structure

llm = ChatOllama(model="gemma4:e2b", reasoning=False)


# Graph state
class State(TypedDict):
    task: str
    content: str
    absolute_path: str
    root_path: str
    fileTree: str
    task_status: Literal["Failed", "Success"]
    knowledge_base: str
    loop_count: int
    current_loop_count: int


class FilePathStructuredOutput(BaseModel):
    absolute_path: str = Field(
        ..., description="Suitable Absolute directory path to the file"
    )


class FileContentStructuredOutput(BaseModel):
    content: str = Field(..., description="Suitable file content to the file")


class StandardReactProjectStructure(BaseModel):
    knowledge_base: str = Field(
        ...,
        description="The knowledge you gain from read md file about react project standard structure",
    )


# Nodes
def cleanState() -> dict:
    """clean the state before new request proceed"""

    return {
        "content": "",
        "absolute_path": "",
        "task_status": "",
    }


# Nodes
def recall_standard_structure(
    state: State,
) -> dict:
    """Read and Understand the standard ( NOT USER GIVEN TREE) react project file structure"""

    knowledge = recall_project_structure()

    clean_md = json.dumps(knowledge, indent=2)

    print(f"md fie knowledge: {clean_md}")

    writer = get_stream_writer()
    writer({"status": "Recalling structure.md file..."})
    prompt = f"""
    You are an expert React developer.

    Your task is to extract and understand the STANDARD Vite + React project structure from the provided markdown.
    YOU DO NOT CREATE ANY FILE OR ANY THING HERE.. JUST GAIN KNOWLEDGE ABOUT  React project structure
    Output format:
    {{"knowledge_base": "str"}}

    Task:
    Recall the Below Markdown Content about the React Standard file structure

    Markdown content:
    {clean_md}

    Rules:
    - Only return valid JSON
    - No explanations
    - No extra text
    """

    structured_llm = llm.with_structured_output(StandardReactProjectStructure)
    result: StandardReactProjectStructure = structured_llm.invoke(prompt)
    print("KNOWLEDGE OUTPUT:", result)
    return {"knowledge_base": result.knowledge_base}


# Nodes


def determine_file_path(
    state: State,
) -> dict:
    """decide the suitable project absolute path and return a suitable absolute path/directory according to the task based on user given fileTree and knowledge. NO PREAMBLE"""

    writer = get_stream_writer()
    writer({"status": "Scanning project path ..."})
    prompt = f"""
    YOU ARE ABSOLUTE PATH FINDER
    You MUST return ONLY valid JSON.

    Output format:
    {{"absolute_path": "string"}}
    Task:
    {state['task']}

    ROOT ABSOLUTE PATH : {state['root_path']}
    
    File Tree:
    {state['fileTree']}
    
    Knowledge about standard file tree:
    {state['knowledge_base']}

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


def isLoopDone(state: State):
    """check weather the loop done"""

    writer = get_stream_writer()
    writer({"status": "Checking re run loop state..."})

    if state["current_loop_count"] > state["loop_count"]:
        return "Done"
    cleanState()
    return "Continue"


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
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            writer({"status": "On Generating..."})
            f.write(content)
            count = state.get("current_loop_count", 1) + 1
            return {"task_status": "Success", "current_loop_count": count}
    except Exception as e:
        return {"task_status": "Failed"}


def run_langgraph(
    task: str,
    loop_count: int,
    runtime: ToolRuntime[None, CustomState],
) -> str:
    """Langgraph agent that work with the file system

    Args:
        task (str): Task user given to you
        loop_count: (int): How many times run this task

    Return :
     str:  Only successfully or failed message.
    """

    writer = get_stream_writer()

    workflow = StateGraph(State)
    workflow.add_node("recall_standard_structure", recall_standard_structure)
    workflow.add_node("determine_path", determine_file_path)
    workflow.add_node("content_generate", generate_file_content)
    workflow.add_node("file_generation", generate_file)

    # config = get_config()
    # runtime_state = config.get("configurable", {})
    # path = runtime_state.get("rootPath")

    tree = runtime.state.get("fileTree")
    root_path = runtime.state.get("rootPath")
    # path = runtime.state.get("rootPath")
    tree_str = json.dumps(tree, indent=2)

    if tree_str is None:
        return
    # workflow.add_edge(START, "recall_standard_structure")
    # workflow.add_edge("recall_standard_structure", END)
    workflow.add_edge(START, "recall_standard_structure")
    workflow.add_edge("recall_standard_structure", "determine_path")
    workflow.add_conditional_edges(
        "determine_path", isPathAvailable, {"Fail": END, "Pass": "content_generate"}
    )
    workflow.add_edge("content_generate", "file_generation")
    # workflow.add_edge("file_generation", END)
    workflow.add_conditional_edges(
        "file_generation",
        isLoopDone,
        {"Done": END, "Continue": "determine_path"},
    )

    chain = workflow.compile()
    full_state = {}

    for chunk in chain.stream(
        {
            "task": task,
            "root_path": root_path,
            "fileTree": tree_str,
            "absolute_path": None,
            "content": None,
            "knowledge_base": None,
            "task_status": None,
            "loop_count": loop_count,
            "current_loop_count": 1,
        },
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "updates":
            for node_name, state in chunk["data"].items():
                # print(f"Node {node_name} updated: {state}")
                full_state.update(state)
        if chunk["type"] == "custom":
            # print(f"Status: {chunk['data']['status']}")
            writer(f"{chunk['data']['status']}")

    state = full_state
    # return {
    #     "absolute_path": state.get("absolute_path"),
    #     "content": state.get("content"),
    # }
    return f"file create successful at {state["absolute_path"]}"
