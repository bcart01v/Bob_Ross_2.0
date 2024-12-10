-- Create the Episodes table
CREATE TABLE IF NOT EXISTS Episodes (
    episode_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    air_date DATE NOT NULL,
    broadcast_month TEXT NOT NULL,
    season_episode TEXT UNIQUE
);

-- Create the Subjects table
CREATE TABLE IF NOT EXISTS Subjects (
    subject_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create the Colors table
CREATE TABLE IF NOT EXISTS Colors (
    color_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    hex_code TEXT NOT NULL
);

-- Create the EpisodeSubjects table
CREATE TABLE IF NOT EXISTS EpisodeSubjects (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES Episodes(episode_id),
    subject_id INTEGER NOT NULL REFERENCES Subjects(subject_id)
);

-- Create the EpisodeColors table
CREATE TABLE IF NOT EXISTS EpisodeColors (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES Episodes(episode_id),
    color_id INTEGER NOT NULL REFERENCES Colors(color_id)
);

-- Unified table for Bob Ross episodes with subject and color details
CREATE TABLE IF NOT EXISTS BobRossEpisodes (
    episode_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    air_date DATE NOT NULL,
    subject_id INTEGER NOT NULL REFERENCES Subjects(subject_id),
    color_id INTEGER NOT NULL REFERENCES Colors(color_id)
);