import os
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=api_key)


@tool("internet_search")
async def internet_search(
    query: str,
    maxResults=5,
    includeRawContent=False,
) -> str:
    """Run a web search.

    Args:
        query: The search query
        maxResults: Maximum number of results to return
        includeRawContent: True or False
    """

    return tavily_client.search(
        query=query,
        max_results=maxResults,
        include_raw_content=includeRawContent,
    )
