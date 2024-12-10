import psycopg2
import pandas as pd
import os
import re

# Helper function to get absolute paths
# I'm hoping this works on all machines, but
# it's the only way I could get it to work
def get_absolute_path(relative_path):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_dir, relative_path)

# Database connection function
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

# Need this for when the subject isn't known...
def get_or_insert_unknown_subject(cursor):
    cursor.execute("SELECT subject_id FROM subjects WHERE name = %s;", ('Unknown',))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("""
            INSERT INTO subjects (name)
            VALUES (%s)
            RETURNING subject_id;
        """, ('Unknown',))
        return cursor.fetchone()[0]

# Function to load data into BobRossEpisodes table
# I feel like this is the only table nessecary, but after
# All the research tells me otherwise.
def load_data_to_bobross_episodes(conn):
    try:
        with conn.cursor() as cursor:
            # Ensure "Unknown" subject exists
            # It will error otherwise
            unknown_subject_id = get_or_insert_unknown_subject(cursor)

            # Insert data into BobRossEpisodes
            cursor.execute(f"""
                INSERT INTO BobRossEpisodes (episode_id, title, air_date, subject_id, color_id)
                SELECT 
                    e.episode_id,
                    e.title,
                    e.air_date,
                    COALESCE(es.subject_id, %s) AS subject_id,
                    ec.color_id
                FROM episodes e
                LEFT JOIN episodesubjects es ON e.episode_id = es.episode_id
                LEFT JOIN episodecolors ec ON e.episode_id = ec.episode_id
                WHERE ec.color_id IS NOT NULL
                ON CONFLICT (episode_id) DO NOTHING;
            """, (unknown_subject_id,))
            conn.commit()
            print("Data loaded into BobRossEpisodes successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error loading data into BobRossEpisodes: {e}")
        raise

# Function to load data into other tables
def load_data_to_table(conn, table_name, data):
    try:
        with conn.cursor() as cursor:
            for _, row in data.iterrows():
                if table_name.lower() == 'episodes':
                    if isinstance(row['air_date'], str):
                        row['air_date'] = pd.to_datetime(row['air_date'])
                    cursor.execute("""
                        INSERT INTO episodes (season_episode, title, air_date, broadcast_month)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (season_episode) DO NOTHING;
                    """, (row['season-episode'], row['title'], row['air_date'], row['air_date'].strftime('%B')))
                elif table_name.lower() == 'subjects':
                    cursor.execute("""
                        INSERT INTO episodesubjects (episode_id, subject_id)
                        SELECT 
                            e.episode_id,
                            s.subject_id
                        FROM episodes e
                        INNER JOIN subjects s ON s.name = %s
                        WHERE e.season_episode = %s
                        ON CONFLICT DO NOTHING;
                    """, (row['subject'], row['season-episode']))
                elif table_name.lower() == 'colors':
                    colors = re.split(r'\s*\|\s*', row['colors'])
                    hex_codes = re.split(r'\s*\|\s*', row['color_hex'])
                    colors = [color.strip() for color in colors]
                    hex_codes = [hex_code.strip() for hex_code in hex_codes]
                    if len(colors) != len(hex_codes):
                        continue
                    cursor.execute("""
                        INSERT INTO episodecolors (episode_id, color_id)
                        SELECT 
                            e.episode_id,
                            c.color_id
                        FROM episodes e
                        INNER JOIN colors c ON c.name = %s AND c.hex_code = %s
                        WHERE e.season_episode = %s
                        ON CONFLICT DO NOTHING;
                    """, (row['season-episode'], row['colors'], row['color_hex']))
        conn.commit()
        print(f"Data loaded into {table_name} successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error loading data into {table_name}: {e}")
        raise

if __name__ == "__main__":
    # Define file paths, I hope it works for you... I couldn't get it 
    # To work otherwise
    subjects_file = get_absolute_path('data/cleaned_up/subjects_cleaned.csv')
    colors_file = get_absolute_path('data/cleaned_up/colors_cleaned.csv')
    episodes_file = get_absolute_path('data/cleaned_up/episodes_cleaned.csv')

    # Connect to the database
    conn = connect_to_db()
    if conn is None:
        exit()

    try:
        # Load cleaned data
        subjects_data = pd.read_csv(subjects_file)
        colors_data = pd.read_csv(colors_file)
        episodes_data = pd.read_csv(episodes_file, parse_dates=['air_date'])

        # Normalize column names
        episodes_data.columns = episodes_data.columns.str.strip().str.lower()
        subjects_data.columns = subjects_data.columns.str.strip().str.lower()
        colors_data.columns = colors_data.columns.str.strip().str.lower()

        # Insert data into tables
        load_data_to_table(conn, 'Episodes', episodes_data)
        load_data_to_table(conn, 'Subjects', subjects_data)
        load_data_to_table(conn, 'Colors', colors_data)
        load_data_to_bobross_episodes(conn)

    except Exception as e:
        print(f"Error during data loading: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()
        print("Database connection closed.")