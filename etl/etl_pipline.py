import os
import pandas as pd
import re

# I originally wanted this to be moduler, but I
# COULD NOT get it to work. But if I had more time
# I could have. (There was plenty of time for the project,
# I'm just way too busy.)

def get_absolute_path(relative_path):
    """
    Get the absolute path for a file based on the project's root directory.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_dir, relative_path)


def remove_special_characters(text):
    """
    Remove special characters from a string, except for '#' characters.
    """
    return re.sub(r"[^a-zA-Z0-9# ]", "", text)


def clean_colors(file_path):
    """
    Clean the colors dataset.
    """
    df = pd.read_csv(file_path)

    # Combine Season and Episode into a single column for better keyability. Is that a word?
    df['Season-Episode'] = df.apply(
        lambda row: f"S{int(row['season']):02d}E{int(row['episode']):02d}", axis=1
    )

    # Clean string columns for painting_title
    df['painting_title'] = df['painting_title'].apply(remove_special_characters)

    # Parse and clean 'colors' and 'color_hex' fields
    def clean_list_field(field):
        try:
            if isinstance(field, str) and field.startswith('[') and field.endswith(']'):
                field = eval(field)
            cleaned_items = [remove_special_characters(str(item).strip()) for item in field]
            return " | ".join(cleaned_items)
        except:
            return remove_special_characters(str(field))

    df['colors'] = df['colors'].apply(clean_list_field)
    df['color_hex'] = df['color_hex'].apply(clean_list_field)

    # Cleaning up leftover quotes, because it's not getting them all somehow?
    df['colors'] = df['colors'].str.replace('"', '', regex=False)
    df['color_hex'] = df['color_hex'].str.replace('"', '', regex=False)

    # Making sure there is no duplicates
    df = df[['painting_index', 'Season-Episode', 'painting_title', 'colors', 'color_hex']]
    df = df.drop_duplicates(subset=['Season-Episode', 'colors', 'color_hex'])
    return df


def clean_subjects(file_path):
    """
    Clean the subjects dataset.
    """
    df = pd.read_csv(file_path)

    # Lowercase column names
    df.columns = [col.lower() for col in df.columns]

    # Pivot the data to get one subject per row
    df = df.melt(id_vars=['episode'], var_name='subject', value_name='has_subject')
    df = df[df['has_subject'] == 1]  # Filter rows where the subject is present

    # Rename for keyability
    df.rename(columns={'episode': 'Season-Episode'}, inplace=True)

    # Deduplicate based on 'Season-Episode' and 'subject'
    df = df.drop_duplicates(subset=['Season-Episode', 'subject'])
    return df[['Season-Episode', 'subject']]


def clean_episodes(file_path):
    """
    Clean the episodes dataset.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    titles, air_dates = [], []
    for line in lines:
        match = re.match(r'"(.+)" \((.+)\)', line.strip())
        if match:
            titles.append(match.group(1))
            air_dates.append(match.group(2))

    df = pd.DataFrame({'title': titles, 'air_date': air_dates})
    df['air_date'] = pd.to_datetime(df['air_date'], format='%B %d, %Y')

    # Generate Season-Episode identifiers based on title order
    df['Season-Episode'] = df.index.map(
        lambda idx: f"S{(idx // 13) + 1:02d}E{(idx % 13) + 1:02d}"
    )

    # Deduplicate based on 'title' and 'air_date'
    df = df.drop_duplicates(subset=['title', 'air_date'])

    return df[['Season-Episode', 'title', 'air_date']]


def save_cleaned_data(cleaned_df, output_path):
    """
    Save the cleaned DataFrame to a CSV file.
    """
    cleaned_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    # Define paths using get_absolute_path
    colors_input_path = get_absolute_path('data/raw/colors_used.csv')
    subjects_input_path = get_absolute_path('data/raw/subject_matter.csv')
    episodes_input_path = get_absolute_path('data/raw/episode_dates.csv')

    colors_output_path = get_absolute_path('data/cleaned_up/colors_cleaned.csv')
    subjects_output_path = get_absolute_path('data/cleaned_up/subjects_cleaned.csv')
    episodes_output_path = get_absolute_path('data/cleaned_up/episodes_cleaned.csv')

    print("Cleaning colors data...")
    try:
        colors_cleaned = clean_colors(colors_input_path)
        save_cleaned_data(colors_cleaned, colors_output_path)
        print(f"Colors data cleaned and saved to {colors_output_path}")
    except Exception as e:
        print(f"Error cleaning colors data: {e}")

    print("\nCleaning subjects data...")
    try:
        subjects_cleaned = clean_subjects(subjects_input_path)
        save_cleaned_data(subjects_cleaned, subjects_output_path)
        print(f"Subjects data cleaned and saved to {subjects_output_path}")
    except Exception as e:
        print(f"Error cleaning subjects data: {e}")

    print("\nCleaning episodes data...")
    try:
        episodes_cleaned = clean_episodes(episodes_input_path)
        save_cleaned_data(episodes_cleaned, episodes_output_path)
        print(f"Episodes data cleaned and saved to {episodes_output_path}")
    except Exception as e:
        print(f"Error cleaning episodes data: {e}")