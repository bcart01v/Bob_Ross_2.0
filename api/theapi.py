from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Database connection function
# I dunno how this would work on other machines with a password?
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname="painting_db",
            user="postgres",
            password="Juikiuj*88*",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

@app.route('/episodes', methods=['GET'])
def get_episodes():
    broadcast_month = request.args.getlist('broadcast_month')
    subjects = request.args.getlist('subject')
    colors = request.args.getlist('color')
    match_all = request.args.get('match_all', 'false').lower() == 'true'

    query = """
        SELECT DISTINCT e.episode_id, e.title, e.air_date, e.broadcast_month
        FROM episodes e
        LEFT JOIN episodesubjects es ON e.episode_id = es.episode_id
        LEFT JOIN subjects s ON es.subject_id = s.subject_id
        LEFT JOIN episodecolors ec ON e.episode_id = ec.episode_id
        LEFT JOIN colors c ON ec.color_id = c.color_id
        WHERE 1=1
    """
    filters = []
    params = []

    # Filters for broadcast_month
    if broadcast_month:
        filters.append(f"e.broadcast_month IN ({', '.join(['%s'] * len(broadcast_month))})")
        params.extend(broadcast_month)

    # Filters for subjects
    if subjects:
        filters.append(f"s.name IN ({', '.join(['%s'] * len(subjects))})")
        params.extend(subjects)

    # Filters for colors
    if colors:
        filters.append(f"c.name IN ({', '.join(['%s'] * len(colors))})")
        params.extend(colors)

    # A Filters to the query
    if filters:
        if match_all:
            # Ensure all filters match the same episode (intersection)
            query += f" AND {' AND '.join(filters)}"
        else:
            # Allow episodes matching any filter (union)
            query += f" AND ({' OR '.join(filters)})"

    query += " ORDER BY e.air_date"

    conn = connect_to_db()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            episodes = [
                {
                    "episode_id": row[0],
                    "title": row[1],
                    "air_date": row[2].strftime('%a, %d %b %Y %H:%M:%S GMT'),
                    "broadcast_month": row[3]
                }
                for row in rows
            ]
            return jsonify({"episodes": episodes})
    except Exception as e:
        print(f"Error executing query: {e}")
        return jsonify({"error": "Failed to fetch episodes"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)