from flask import Flask, jsonify, request, send_file, redirect, send_from_directory
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os
from google.cloud import vision
from google.cloud.vision import Image
import psycopg2


app = Flask(__name__, static_folder="../front-facing")  # Adjust static folder to point to "front-facing"
CORS(app)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("service-account-key.json")
use_reloader = os.getenv("FLASK_USE_RELOADER", "True") == "True"

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
        extracted_labels = [label.description.strip().lower() for label in labels]
        print(f"Extracted Labels: {extracted_labels}")

        # Match extracted labels with subjects in DB
        matched_subjects = []
        matched_episodes = []
        sql_subjects_query = """
            SELECT subject_id, name
            FROM subjects
            WHERE similarity(name, %s) > 0.5
            ORDER BY similarity(name, %s) DESC
            LIMIT 1;
        """
        sql_episodes_query = """
            SELECT e.episode_id, e.title, e.air_date, e.season_episode
            FROM episodes e
            INNER JOIN episodesubjects es ON e.episode_id = es.episode_id
            WHERE es.subject_id = %s
            LIMIT 10;
        """

        conn = psycopg2.connect(
            dbname="painting_db",
            user="postgres",
            password="Juikiuj*88*",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # Find subjects
        subject_ids = []
        for label in extracted_labels:
            cursor.execute(sql_subjects_query, (label, label))
            result = cursor.fetchone()
            if result and result[0] not in subject_ids:
                subject_ids.append(result[0])
                matched_subjects.append({"subject_id": result[0], "name": result[1]})
        
        # Find episodes for matched subjects
        for subject_id in subject_ids:
            cursor.execute(sql_episodes_query, (subject_id,))
            episodes = cursor.fetchall()
            for episode in episodes:
                matched_episodes.append({
                    "episode_id": episode[0],
                    "title": episode[1],
                    "air_date": episode[2],
                    "season_episode": episode[3]
                })
        
        print(f"Matched subjects: {matched_subjects}")
        print(f"Matched episodes: {matched_episodes}")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    # Return labels to the frontend
    return jsonify({
        "labels": extracted_labels, 
        "matched_subjects": matched_subjects,
        "matched_episodes": matched_episodes
    })

if __name__ == "__main__":
    app.run(port=5005, debug=True, use_reloader=use_reloader)
