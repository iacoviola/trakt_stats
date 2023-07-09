# Trakt Stats

> Get enhanced stats about your Trakt account
> This is still a rudimentary version, your data will be saved in a json file and you will have to use a json viewer to see the results
> Some time in the future, I plan to add an interface to display the results in a more user-friendly way

Warning, you need to have a **public trakt account** in order to use the API.
You will need a version of python >= 3.10 to run this script (I used python 3.11 so I would stick with that).

## Setup

Clone the project and create the .env file

```bash
git clone https://github.com/iacoviola/trakt_stats.git
cd trakt_stats
cp .env.example .env
```

(copy the .env.example file instead of renaming it, otherwise it will be tracked by git)

### Trakt API key

- Create an API key here: https://trakt.tv/oauth/applications/new
  - Fill in the required fields <b>(Name, Description and Redirect URI)</b> and then press <b>SAVE APP</b> at the bottom of the page
- Copy the **Client ID** field inside the .env file

### TMDB API key

- Create an API key here: https://www.themoviedb.org/settings/api
- Copy the **API Read Access Token** field inside the .env file (the API Key will not work since the script is sending the Key to the TMDB servers using HTTP's header `Authorization: Bearer <API_KEY>` instead of the query parameter `api_key=<API_KEY>`)

## Requirements

Setup a venv and install requirements:

```bash
# On linux and macos
python3.11 -m venv ./venv
# On windows using python3.11 installed from scoop
python311 -m venv ./venv

# On linux and macos
source venv/bin/activate
# On windows
venv\Scripts\activate.bat

pip install -r requirements.txt 
```

## Usage

Interactive mode: **WILL BE IMPLEMENTED SOON**

```bash
python3.11 ./trakt_stats.py
```

## Results

The results will be saved in the `results` folder.

This includes:
- `most_watched_actors.json`: Your most watched actors, sorted by number of items (movies or shows) watched
- `most_watched_directors.json`: Your most watched directors, sorted by number of movies watched
- `most_watched_genres.json`: Your most watched genres, sorted by number of items (movies or shows) watched
- `most_watched_countries.json`: Your most watched countries, sorted by number of items (movies or shows) watched
- `most_watched_studios.json`: Your most watched studios, sorted by number of items (movies or shows) watched
- `user_stats.json`: Your stats about movies and shows (time spent watching, number of items watched, etc.)
- `best_of_progress.json`: Your progresses in watching movies from a selection of lists:
    - IMDb Top 250
    - IMDb Bottom 100
    - Trakt Top 250
    - Statistical top 500
    - Reddit top 250 (2019 edition)

