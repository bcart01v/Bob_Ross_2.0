from flask import Flask, jsonify, request, send_file, redirect, send_from_directory
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os
from google.cloud import vision
from google.cloud.vision import Image


app = Flask(__name__, static_folder="../front-facing")  # Adjust static folder to point to "front-facing"
CORS(app)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("service-account-key.json")

# API Constants
PLACE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

# Initialize Google Vision client
vision_client = vision.ImageAnnotatorClient()

@app.route("/")
def root():
    # Adding this because I'm tired of typing it manually...
    return redirect("/index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/places", methods=["GET"])
def get_places():
    try:
        # Get the Region
        region = request.args.get("region", "")
        if not region:
            return jsonify({"error": "Region is required"}), 400

        # Fetch data
        params = {
            "query": f"nature in {region}",
            "key": GOOGLE_API_KEY
        }
        response = requests.get(PLACE_SEARCH_URL, params=params)
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

@app.route("/analyze", methods=["POST"])
def analyze_photo():
    try:
        photo_reference = request.json.get("photo_reference")
        if not photo_reference:
            return jsonify({"error": "Missing photo_reference"}), 400

        photo_response = requests.get(
            PHOTO_URL,
            params={
                "photoreference": photo_reference,
                "key": GOOGLE_API_KEY,
                "maxwidth": 800,
            },
            stream=True,
        )
        photo_response.raise_for_status()

        # Photo Analysis
        image = Image(content=photo_response.content)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations

        # Extract and log labels, this is what we'll use as our search value to the database
        extracted_labels = [label.description for label in labels]
        print(f"Extracted Labels: {extracted_labels}")

        # Return labels to the frontend
        return jsonify({"labels": extracted_labels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5005, debug=True)