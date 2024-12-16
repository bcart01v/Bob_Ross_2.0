-- Alter the Episodes table to add youtube_link column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'episodes' AND column_name = 'youtube_link'
    ) THEN
        ALTER TABLE Episodes
        ADD COLUMN youtube_link TEXT;
    END IF;
END $$;

-- Ensure the Episodes table exists and alter it if necessary
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodes') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'episodes' AND column_name = 'youtube_link'
        ) THEN
            ALTER TABLE Episodes
            ADD COLUMN youtube_link TEXT;
        END IF;
    ELSE
        CREATE TABLE Episodes (
            episode_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            air_date DATE NOT NULL,
            broadcast_month TEXT NOT NULL,
            season_episode TEXT UNIQUE,
            youtube_link TEXT  -- Add youtube_link column
        );
    END IF;
END $$;

-- Alter the Subjects table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'subjects') THEN
        -- Add any other alterations if needed
        NULL;
    ELSE
        CREATE TABLE Subjects (
            subject_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
    END IF;
END $$;

-- Alter the Colors table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'colors') THEN
        -- Add any other alterations if needed
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_name = 'colors' AND constraint_name = 'unique_color_name_hex'
        ) THEN
            ALTER TABLE Colors
            ADD CONSTRAINT unique_color_name_hex UNIQUE (name, hex_code);
        END IF;
    ELSE
        CREATE TABLE Colors (
            color_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            hex_code TEXT NOT NULL,
            CONSTRAINT unique_color_name_hex UNIQUE (name, hex_code)
        );
    END IF;
END $$;

-- Alter the EpisodeSubjects table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodesubjects') THEN
        -- Add any other alterations if needed
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_name = 'episodesubjects' AND constraint_name = 'unique_episode_subject'
        ) THEN
            ALTER TABLE EpisodeSubjects
            ADD CONSTRAINT unique_episode_subject UNIQUE (episode_id, subject_id);
        END IF;
    ELSE
        CREATE TABLE EpisodeSubjects (
            id SERIAL PRIMARY KEY,
            episode_id INTEGER NOT NULL REFERENCES Episodes(episode_id),
            subject_id INTEGER NOT NULL REFERENCES Subjects(subject_id),
            CONSTRAINT unique_episode_subject UNIQUE (episode_id, subject_id)
        );
    END IF;
END $$;

-- Alter the EpisodeColors table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodecolors') THEN
        -- Add any other alterations if needed
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_name = 'episodecolors' AND constraint_name = 'unique_episode_color'
        ) THEN
            ALTER TABLE EpisodeColors
            ADD CONSTRAINT unique_episode_color UNIQUE (episode_id, color_id);
        END IF;
    ELSE
        CREATE TABLE EpisodeColors (
            id SERIAL PRIMARY KEY,
            episode_id INTEGER NOT NULL REFERENCES Episodes(episode_id),
            color_id INTEGER NOT NULL REFERENCES Colors(color_id),
            CONSTRAINT unique_episode_color UNIQUE (episode_id, color_id)
        );
    END IF;
END $$;

-- Alter the BobRossEpisodes table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bobrossepisodes') THEN
        -- Add any other alterations if needed
        NULL;
    ELSE
        CREATE TABLE BobRossEpisodes (
            episode_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            air_date DATE NOT NULL,
            subject_id INTEGER NOT NULL REFERENCES Subjects(subject_id),
            color_id INTEGER NOT NULL REFERENCES Colors(color_id)
        );
    END IF;
END $$;