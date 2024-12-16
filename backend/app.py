from flask import Flask, jsonify, request, send_file, redirect, send_from_directory
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os
from google.cloud import vision
from google.cloud.vision import Image
import psycopg2
import logging

# Initialize Flask app
app = Flask(__name__, static_folder="../front-facing")  # Adjust static folder to point to "front-facing"
CORS(app)

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__) 

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
    logger.info("Redirecting to index.html")
    return redirect("/index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    logger.info(f"Serving static file: {filename}")
    return send_from_directory(app.static_folder, filename)

@app.route("/places", methods=["GET"])
def get_places():
    try:
        region = request.args.get("region", "")
        if not region:
            logger.warning("Region is missing in /places request")
            return jsonify({"error": "Region is required"}), 400

        logger.info(f"Fetching places for region: {region}")
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

        logger.info(f"Found {len(places)} places for region {region}")
        return jsonify(places)
    except Exception as e:
        logger.error(f"Error in /places: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/photo", methods=["GET"])
def get_photo():
    try:
        photo_reference = request.args.get("photo_reference")
        if not photo_reference:
            logger.warning("Missing photo_reference in /photo request")
            return jsonify({"error": "Missing photo_reference"}), 400

        logger.info(f"Fetching photo for reference: {photo_reference}")
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

        logger.info(f"Photo fetched successfully for reference: {photo_reference}")
        return send_file(
            BytesIO(response.content),
            mimetype=response.headers["Content-Type"]
        )
    except Exception as e:
        logger.error(f"Error in /photo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/analyze", methods=["POST"])
def analyze_photo():
    try:
        photo_reference = request.json.get("photo_reference")
        if not photo_reference:
            logger.warning("Missing photo_reference in /analyze request")
            return jsonify({"error": "Missing photo_reference"}), 400

        logger.info(f"Analyzing photo with reference: {photo_reference}")
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

        image = Image(content=photo_response.content)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations

        extracted_labels = [label.description.strip().lower() for label in labels]
        logger.info(f"Extracted Labels: {extracted_labels}")

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

        subject_ids = []
        for label in extracted_labels:
            cursor.execute(sql_subjects_query, (label, label))
            result = cursor.fetchone()
            if result and result[0] not in subject_ids:
                subject_ids.append(result[0])
                matched_subjects.append({"subject_id": result[0], "name": result[1]})
        
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
        
        logger.info(f"Matched subjects: {matched_subjects}")
        logger.info(f"Matched episodes: {matched_episodes}")
    
    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

    return jsonify({
        "labels": extracted_labels, 
        "matched_subjects": matched_subjects,
        "matched_episodes": matched_episodes
    })

if __name__ == "__main__":
    logger.info("Starting Flask app")
    app.run(port=5005, debug=True, use_reloader=use_reloader)