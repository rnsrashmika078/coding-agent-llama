import json

from langchain.agents import AgentState, create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.tools import ToolRuntime
from model import CustomState


llm = ChatOllama(model="gemma4:e2b", reasoning=False)

subagent = create_agent(
    model=llm,
)


@tool("research", description="Research a topic and return findings")
def call_research_agent(query: str):
    result = subagent.invoke({"messages": [{"role": "user", "content": query}]})
    return (result["messages"][-1].content,)


@tool(
    "call_traversal_agent",
    description="explores the full project file tree and answers questions about files/folders",
)
def call_traversal_agent(
    query: str,
    runtime: ToolRuntime[None, CustomState],
):
    """
    Project Traversal Tool

    This tool allows the AI agent to inspect and reason about the project’s
    file system structure. It provides access to directory paths, file names,
    and hierarchical relationships between files and folders.

    The agent should use this tool whenever it needs to understand the project
    layout, locate files, or verify the existence of directories before taking action.

    Capabilities:
    - Check whether a specific file or directory exists ( use 'tree' command)
    - Retrieve the project root path
    - Get the current working directory
    - List all files and folders within a directory
    - Return file or folder names for a given path
    - Resolve full paths of files or directories
    - Traverse directories recursively
    - Search through the project structure to locate targets

    Usage Guidelines:
    - Use this tool BEFORE modifying or referencing files
    - Prefer this tool over guessing file paths
    - Can be called multiple times for step-by-step traversal
    - Supports iterative exploration (navigate → inspect → refine)

    Args:
        query (str): A natural language instruction describing what to
                     retrieve or inspect within the project structure.

    Returns:
        str: Structured information about files, folders, or paths
             relevant to the query.
    """

    writer = runtime.stream_writer
    tree = runtime.state.get("fileTree")
    tree_str = json.dumps(tree, indent=2)

    # print(f"Tree str {tree_str}")

    if not tree:
        return "No project tree found!. Please open a project and try again..."

    writer("Traversing project files with AI...")

    result = subagent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
You are a project file explorer.

Here is the full project structure:
{tree_str}

User query:
{query}

Rules:
- Only use the given file tree
- If user asks for files in a folder, extract them
- If user asks for structure, summarize clearly
- If user ask about file path, return file paths
- If user ask about file id, return file id
- Return concise answer
""",
                }
            ]
        }
    )

    return result["messages"][-1].content
