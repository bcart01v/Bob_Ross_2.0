from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PLACE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"


@app.route("/places", methods=["GET"])
def get_places():
    try:
        # Get the Region
        region = request.args.get("region", "")
        if not region:
            return jsonify({"error": "Region is required"}), 400

        # Fetch data
        params = {
            "query": f"nature in {region}",  # Use 'query' for broader results by region
            "key": GOOGLE_API_KEY
        }
        response = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
        data = response.json()

        places = [
            {
                "name": place.get("name"),
                "location": place.get("formatted_address"),
                "photo_reference": place["photos"][0]["photo_reference"] if "photos" in place else None,
            }
            for place in data.get("results", [])
        ]

        return jsonify(places)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/photo", methods=["GET"])
def get_photo():
    try:
        photo_reference = request.args.get("photo_reference")
        if not photo_reference:
            return jsonify({"error": "Missing photo_reference"}), 400

        # Fetch the photo
        response = requests.get(
            PHOTO_URL,
            params={
                "photoreference": photo_reference,
                "key": GOOGLE_API_KEY,
                "maxwidth": 800,
            },
            stream=True,
        )
        response.raise_for_status()

        return send_file(
            BytesIO(response.content),
            mimetype=response.headers["Content-Type"]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5005, debug=True)