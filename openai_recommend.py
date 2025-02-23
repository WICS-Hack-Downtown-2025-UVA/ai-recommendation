from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Strict structured format for OpenAI recommendation updates
STRUCTURED_FORMAT = (
    "You are a travel assistant. When given a city name, you must respond with exactly 5 places to visit and 5 restaurant recommendations (search for Google Maps Rating as much as you can, otherwise return N/A) in that city. "
    "Ensure each place and restaurant is well-known and worth visiting. "
    "DO NOT BOLD THE PLACE NAME OR RESTAURANT NAME"
    "The response must strictly follow this format:\n\n"
    "**City: {city_name}**\n"
    "**Top 5 Places to Visit:**\n"
    "1. [Place Name] - [Short Description]\n"
    "2. [Place Name] - [Short Description]\n"
    "3. [Place Name] - [Short Description]\n"
    "4. [Place Name] - [Short Description]\n"
    "5. [Place Name] - [Short Description]\n"
    "**Top 5 Restaurants to Try:**\n"
    "1. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
    "2. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
    "3. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
    "4. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
    "5. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
)

def get_travel_recommendations(city_name, user_request=None, existing_places=None, existing_restaurants=None):
    """Fetches travel recommendations while preserving unchanged sections if needed."""

    # ✅ Ensure lists exist and contain 5 elements to avoid IndexError
    if existing_places is None or len(existing_places) < 5:
        existing_places = ["Placeholder Place - No Data"] * 5

    if existing_restaurants is None or len(existing_restaurants) < 5:
        existing_restaurants = ["Placeholder Restaurant - No Data (⭐ N/A)"] * 5

    # Start with the default system prompt
    system_prompt = STRUCTURED_FORMAT.format(city_name=city_name)

    user_message = f"Provide travel and restaurant recommendations for {city_name}."

    if user_request:
        if "restaurant" in user_request.lower():
            user_message += (
                f" Modify ONLY the restaurant list based on this request: {user_request}. Keep the same format:\n"
                "**Top 5 Restaurants to Try:**\n"
                "1. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "2. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "3. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "4. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "5. [Restaurant Name] - [Short Description] (⭐ [Google Maps Rating])\n"
                "but **DO NOT CHANGE** the places. Keep them exactly as:\n"
                f"{existing_places[0]}\n{existing_places[1]}\n{existing_places[2]}\n"
                f"{existing_places[3]}\n{existing_places[4]}\n"
            )
        elif "place" in user_request.lower():
            user_message += (
                f" Modify ONLY the places list based on this request: {user_request}. Keep the same format:\n"
                "**Top 5 Places to Visit:**\n"
                "1. [Place Name] - [Short Description]\n"
                "2. [Place Name] - [Short Description]\n"
                "3. [Place Name] - [Short Description]\n"
                "4. [Place Name] - [Short Description]\n"
                "5. [Place Name] - [Short Description]\n"
                "but **DO NOT CHANGE** the restaurants. Keep them exactly as:\n"
                f"{existing_restaurants[0]}\n{existing_restaurants[1]}\n{existing_restaurants[2]}\n"
                f"{existing_restaurants[3]}\n{existing_restaurants[4]}\n"
            )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    content = response.choices[0].message.content
    return extract_recommendations(content)


def extract_recommendations(content):
    """Parses OpenAI's response into structured places & restaurants without mixing them up."""
    lines = content.split("\n")

    places = []
    restaurants = []
    is_places = False  # Start with False to prevent accidental misclassification
    is_restaurants = False

    for line in lines:
        line = line.strip()
        if not line or line == "\n":  
            continue  # ✅ Skip empty lines

        # ✅ Detect start of "places to visit"
        if "**Top 5 Places to Visit:**" in line:
            is_places = True
            is_restaurants = False
            continue  # Skip the title line

        # ✅ Detect start of "restaurants"
        if "**Top 5 Restaurants to Try:**" in line:
            is_places = False
            is_restaurants = True
            continue  # Skip the title line

        if is_places:
            places.append(line)
        elif is_restaurants:
            restaurants.append(line)

    return {
        "places": places[:5],  # ✅ Ensure exactly 5 items
        "restaurants": restaurants[:5],  # ✅ Ensure exactly 5 items
    }


@app.route("/recommendations/<city>", methods=["GET"])
def recommendations(city):
    """API endpoint for initial recommendations in structured format."""
    recommendations = get_travel_recommendations(city)
    return jsonify({"city": city, "places": recommendations["places"], "restaurants": recommendations["restaurants"]})


@app.route("/recommendations/chatbot", methods=["POST"])
def chatbot_recommendations():
    """Handles chatbot interaction & updates recommendations if requested."""
    data = request.get_json()
    city = data.get("city")
    message = data.get("message")
    
    # ✅ Ensure current_recommendations always exists
    current_recommendations = data.get("current_recommendations", {"places": [], "restaurants": []})
    
    existing_places = current_recommendations.get("places", [])
    existing_restaurants = current_recommendations.get("restaurants", [])
    print("Received current_recommendations:", current_recommendations)
    print("Existing Places:", existing_places)
    print("Existing Restaurants:", existing_restaurants)
    # ✅ Prevent index errors by ensuring lists have at least 5 elements
    while len(existing_places) < 5:
        existing_places.append("Placeholder Place - No Data")

    while len(existing_restaurants) < 5:
        existing_restaurants.append("Placeholder Restaurant - No Data (⭐ N/A)")

    if not city or not message:
        return jsonify({"error": "Missing city or message"}), 400

    # ✅ Detect if user wants updated recommendations
    if "recommend" in message.lower() or "update" in message.lower():
        new_recommendations = get_travel_recommendations(
            city,
            user_request=message,
            existing_places=existing_places,
            existing_restaurants=existing_restaurants
        )
        return jsonify({"updated": True, "recommendations": new_recommendations})
    
    # ✅ Otherwise, return a normal chatbot response
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Keep responses short (2-3 sentences max). Only provide detailed recommendations if specifically asked."},
            {"role": "user", "content": message}
        ]
    )

    return jsonify({"updated": False, "response": response.choices[0].message.content})


if __name__ == "__main__":
    app.run(port=5001, debug=True)