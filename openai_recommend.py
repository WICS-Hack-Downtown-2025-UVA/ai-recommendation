from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"), 
)

city_name = "New York"

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
    {"role": "system", "content": 
        "You are a travel assistant. When given a city name, you must respond with exactly 5 places to visit in that city. "
        "The response must follow this exact format:\n\n"
        f"**City: {city_name}**\n"
        "**Top 5 Places to Visit:**\n"
        "1. [Place Name] - [Short Description]\n"
        "2. [Place Name] - [Short Description]\n"
        "3. [Place Name] - [Short Description]\n"
        "4. [Place Name] - [Short Description]\n"
        "5. [Place Name] - [Short Description]\n\n"
        "Ensure each place is well-known, popular, and worth visiting. Maintain the format strictly."
    },
    {"role": "user", "content": f"Provide travel recommendations for {city_name}."}
]
)

print(response.choices[0].message.content)