# Trakt Stats

> Get enhanced stats about your Trakt account
>
> This is still a rudimentary version, your data will be saved in a json file and you will have to use a json viewer to see the results
>
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

### Json files

This includes:
- `most_watched_actors.json`: Your most watched actors, sorted by number of items (movies or shows) watched
- `most_watched_directors.json`: Your most watched directors, sorted by number of movies watched
- `most_watched_genres.json`: Your most watched genres, sorted by number of items (movies or shows) watched
- `most_watched_countries.json`: Your most watched countries, sorted by number of items (movies or shows) watched
- `most_watched_studios.json`: Your most watched studios, sorted by number of movies watched
- `most_watched_networks.json`: Your most watched networks, sorted by number of shows watched
- `user_stats.json`: Your stats about movies and shows (time spent watching, number of items watched, etc.)
- `best_of_progress.json`: Your progresses in watching: 
  - movies from a selection of lists:
    - IMDb Top 250
    - IMDb Bottom 100
    - Trakt Top 250
    - Statistical top 500
    - Reddit top 250 (2019 edition)
    - Oscars Best Picture Winners
  - and shows:
    - IMDb Top 250
    - Trakt Top 250
    - Rolling Stone's 100 Greatest TV Shows of All Time

### Pictures

On top of all this the script will also download on your device the pictures of the 10 actors and directors you watched the most, including the 10 most watched movie studios and tv networks, these pictures will be saved in the `results/img` folder.

### Graphs

The script will also generate some graphs using the `plotly` library, these graphs will be saved in the `results/graphs` and `results/maps` folders, the graphs are:
- `movies_genres.html`: A pie chart of your most watched movie genres
- `shows_genres.html`: A pie chart of your most watched show genres
- `ratings_distribution.html`: A stacked bar chart showing the distribution of your ratings by the type of item (movies, shows, seasons, episodes)
- `movies_countries.html`: A choropleth map showing the countries of origin of your most watched movies
- `shows_countries.html`: A choropleth map showing the countries of origin of your most watched shows

All of this graphs can be exported as images using one of the following formats: `png`, `jpeg`, `webp`, `svg` and `pdf`, you'll need to install the `kaleido` library or the `orca` library to do so, you can install them using:

```bash
pip install kaleido
# or
pip install orca
```

| :exclamation: These libraries are not included in the requirements.txt file since they are not required to run the script, you'll have to install them manually. |
| --- |

| :exclamation: I suggest using `kaleido` since it's easier to install and use. |
| --- |
