import json
import os

from langchain.agents import AgentState
from langchain_core.tools import tool
from pydantic import BaseModel
from model import CustomState
from typing import List, Optional, Literal
from langchain.tools import ToolRuntime
import subprocess

from utils.common import requestWeatherData


class CommandRequest(BaseModel):
    executable: str
    args: List[str] = []
    cwd: Optional[str] = None
    timeout_sec: int = 60
    mode: Literal["foreground", "background"] = "foreground"


@tool("get_weather")
async def get_weather(
    runtime: ToolRuntime,
    city: str,
) -> str:
    """return weather data on given city"""
    writer = runtime.stream_writer
    writer(f"Waiting for user approval")
    writer(f"Fetching Weather data...!")
    result = await requestWeatherData(city)
    writer(f"Successfully fetch the weather data!")
    return json.dumps({"weather Data": result})


@tool("create_react_app")
async def create_react_app(
    runtime: ToolRuntime[None, CustomState],
    # path: Optional[str] = None,
    name: Optional[str] = None,
):
    """create react application using vite server
    Args:
       path: Directory where the project should be created.
       name: Name of the React app (used if path is not provided).
    """
    path = runtime.state.get("rootPath", None)
    tree = runtime.state.get("fileTree", None)
    # path = getattr(runtime.context, "rootPath", None)
    # tree = getattr(runtime.context, "fileTree", None)

    # writer(f"selectied path {path}")

    writer = runtime.stream_writer
    writer(f"Waiting for user approval")

    writer(f"Looking for best path")

    if not path:
        # writer(f"Create react app in default path: {path}")
        return f"Please select a path for the project and try again"
    if not name:
        # writer(f"Create react app in default path: {path}")
        return f"Please pick a project name and try again"

    try:
        writer(f"Creating react app...")
        process = subprocess.Popen(
            f"npx create-vite@latest {name} --template react",
            cwd=path,
            check=True,
            shell=True,
            # stdin=subprocess.PIPE,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.STDOUT,
            # text=True,
            # bufsize=1,
        )
        for line in process.stdout:
            writer(line)

        return f"app created at {path} with name {name}. do you want to run it ? "

    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"


@tool("run_react_app")
async def run_react_app(
    runtime: ToolRuntime[None, CustomState],
    name: Optional[str] = None,
):
    """run react application using vite server
    Args:
       name: Name of the React app (used if path is not provided).
    """
    path = runtime.state.get("rootPath", None)
    tree = runtime.state.get("fileTree", None)

    writer = runtime.stream_writer
    writer(f"Waiting for user approval")

    writer(f"Looking for best path")

    if not path:
        # writer(f"Create react app in default path: {path}")
        return f"Please select a path for the project and try again"
    if not name:
        # writer(f"Create react app in default path: {path}")
        return f"Please pick a project name and try again"

    try:
        writer(f"Run react app...")
        subprocess.run(f"npm install", cwd=path, check=True, shell=True)
        subprocess.Popen("npm run dev", cwd=path, shell=True)
        # start dev server (non-blocking)

        return f"React vite App started!"

    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"


IGNORED = {"node_modules", ".git", "dist", "build", "__pycache__"}


def build_tree(path):
    tree = {}

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORED]

        rel = os.path.relpath(root, path)
        tree[rel] = {"dirs": dirs, "files": files}

    return tree


@tool("run_terminal_command")
async def run_terminal_command(
    runtime: ToolRuntime[None, CustomState],
    command: str,
    content: Optional[str],
    # task_type: Literal["background", "normal"],
    # name: Optional[str] = None,
):
    #   task_type: the type of the command. weather the command must run on background or not. Example npm run dev is background task

    """run terminal command based on user input.
    USE WINDOWS OS BASED COMMANDS ONLY. LIKE CMD COMMANDS

    Your job:
    1. Summarize the project structure clearly
    2. List out project tree ( 'tree' command)
    3. Ignore irrelevant folders like node_modules
    4. Highlight important folders (src, public, config files)
    5. Point out anything unusual or missing
    6. If user asked something specific, answer it

    REMEMBER:
     IF USER WANT TO CREATE VITE APPLICATION THEN USE npx instead of npm.
     use cd project_folder_name with every command after create the project

    Args:
      command: the command to execute (cmd command : windows operating system commands only): command must decide by you based on user input
      content: content of the file that user need to create if needed!
    """
    path = runtime.state.get("rootPath", None)
    tree = runtime.state.get("fileTree", None)
    # childPath = tree["path"]

    writer = runtime.stream_writer
    writer(f"Waiting for user approval")

    writer(f"setup command..")

    # if not path:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please select a path for the project and try again"
    # if not name:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please pick a project name and try again"

    try:
        writer(f"Executing command: {command}.")
        # if task_type == "background":
        # else:
        process = subprocess.Popen(
            command,
            cwd=path,
            # check=True,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        stdout, stderr = process.communicate()

        # subprocess.Popen(f"{command}", cwd=path, check=True, shell=True)
        # subprocess.Popen("npm run dev", cwd=path, check=True, shell=True)
        # start dev server (non-blocking)
        if process.poll() is None:
            writer("Process still running...")
        if stderr:
            return f"{stderr}"
        return stdout

    except subprocess.CalledProcessError as e:
        return f"Error occurred while excution of the {command}: {e}"


@tool("get_current_working_directory")
async def get_current_working_directory(
    runtime: ToolRuntime[None, CustomState],
    # command: str,
    # name: Optional[str] = None,
):
    """return current working directory to user"""
    cwd = runtime.state.get("cwd", None)
    tree = runtime.state.get("fileTree", None)

    writer = runtime.stream_writer
    # writer(f"Waiting for user approval")

    writer(f"Getting current working directory..")

    # if not path:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please select a path for the project and try again"
    # if not name:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please pick a project name and try again"

    try:
        # writer(f"Executing command: {command}.")
        # subprocess.run(f"{command}", cwd=path, check=True, shell=True)
        # subprocess.Popen("npm run dev", cwd=path, check=True, shell=True)
        # start dev server (non-blocking)

        return f"Current working directory: {cwd}"

    except subprocess.CalledProcessError as e:
        return f"Error occurred while getting working directory: {e}"


@tool("create_files")
async def create_react_files(
    runtime: ToolRuntime[None, CustomState],
    # command: str,
    # name: Optional[str] = None,
):
    """create react file"""
    cwd = runtime.state.get("cwd", None)
    tree = runtime.state.get("fileTree", None)

    writer = runtime.stream_writer
    # writer(f"Waiting for user approval")

    writer(f"Creating files...")

    # if not path:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please select a path for the project and try again"
    # if not name:
    #     # writer(f"Create react app in default path: {path}")
    #     return f"Please pick a project name and try again"
    return f"file created successfully!"

    # try:
    #     # writer(f"Executing command: {command}.")
    #     # subprocess.run(f"{command}", cwd=path, check=True, shell=True)
    #     # subprocess.Popen("npm run dev", cwd=path, check=True, shell=True)
    #     # start dev server (non-blocking)

    #     return f"file created sucessfully!"

    # except subprocess.CalledProcessError as e:
    #     return f"Error occurred while getting working directory: {e}"
