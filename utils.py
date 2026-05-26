import os
from dotenv import load_dotenv
import httpx

load_dotenv()

api_key = os.getenv("WEATHER_API_KEY")
os.getenv("WEATHER_API_KEY")


async def requestWeatherData(city: str):
    url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json().get("current", response.json())