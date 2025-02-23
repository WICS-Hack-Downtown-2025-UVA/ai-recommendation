from flask import Flask, jsonify
from flask_cors import CORS  # ✅ Import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_travel_recommendations(city_name):
    """Fetches top 5 places to visit and 5 restaurants (with ratings) in the given city using OpenAI."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": 
                "You are a travel assistant. When given a city name, you must respond with exactly 5 places to visit and 5 restaurant recommendations (with Google Maps ratings if available) in that city."
                "If a restaurant's rating is unknown, return 'N/A'."
                "The response must follow this exact format:\n\n"
                f"**City: {city_name}**\n"
                "**Top 5 Places to Visit:**\n"
                "1. [Place Name] - [Short Description]\n"
                "2. [Place Name] - [Short Description]\n"
                "3. [Place Name] - [Short Description]\n"
                "4. [Place Name] - [Short Description]\n"
                "5. [Place Name] - [Short Description]\n\n"
                "**Top 5 Restaurants to Try:**\n"
                "1. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "2. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "3. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "4. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "5. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n\n"
                "Ensure each place and restaurant is well-known and worth visiting. Maintain the format strictly."
            },
            {"role": "user", "content": f"Provide travel and restaurant recommendations for {city_name}."}
        ]
    )
    
    content = response.choices[0].message.content
    return extract_recommendations(content)

def extract_recommendations(content):
    """Extracts places & restaurants from OpenAI's response."""
    lines = content.split("\n")

    places = []
    restaurants = []
    is_places = True  # Flag to switch from places to restaurants

    for line in lines:
        if "**Top 5 Restaurants to Try:**" in line:
            is_places = False
            continue

        if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
            if is_places:
                places.append(line.strip())
            else:
                # ✅ Ensure missing ratings get "N/A"
                if "(⭐" not in line:
                    line += " (⭐ N/A)"
                restaurants.append(line.strip())

    return {"places": places, "restaurants": restaurants}

@app.route("/recommendations/<city>", methods=["GET"])
def recommendations(city):
    """API endpoint to return places to visit & restaurants in a given city, with ratings."""
    recommendations = get_travel_recommendations(city)
    return jsonify({"city": city, "places": recommendations["places"], "restaurants": recommendations["restaurants"]})

if __name__ == "__main__":
    app.run(port=5001, debug=True)