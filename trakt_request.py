import requests
import json
import os

import exceptions as ex

class TraktRequest:

    # Trakt api base url
    base_url = "https://api.trakt.tv"

    # Unused for now
    # Additional info to cache
    cached_data = ["certifications", "countries", "genres", "languages"]
    
    # Initialize the TraktRequest class with the api key, the username and the base path for the cache
    def __init__(self, api_key, username, cache_path):
        self.username = username
        self.users_url = f"{self.base_url}/users/{self.username}"
        self.base_cache_path = cache_path

        # Trakt request required headers
        self.headers = {
            # Trakt return a json response
            "Content-Type": "application/json",
            # Trakt api version
            "trakt-api-version": "2",
            # Trakt api key
            "trakt-api-key": api_key,  # Your trakt api key
        }

    # Unused for now
    # Cache in ./cache/ folder the following files:
    # - certifications_movies.json/certifications_shows.json - Ratings guide for movies/shows
    # - countries_movies.json/countries_shows.json - List of countries
    # - genres_movies.json/genres_shows.json - List of genres
    # - languages_movies.json/languages_shows.json - List of languages
    def cache_additional_info(self):
        for file_name in self.cached_data:
            if not os.path.isfile(os.path.join(self.base_cache_path, f"{file_name}_movies.json")):
                self.get(file_name, "movies", cache=True)
            if not os.path.isfile(os.path.join(self.base_cache_path, f"{file_name}_shows.json")):
                self.get(file_name, "shows", cache=True)

    # Unused, see TMDBRequest get_crew
    # Get crew from trakt api given an item id and the type of the item (movie/show)
    def get_crew(self, media_id, media_type):
        return self.get(f"{media_type}/{media_id}", "people")
    
    # Unused, see TMDBRequest get_studio
    # Get studio from trakt api given an item id and the type of the item (movie/show)
    def get_studio(self, media_id, media_type):
        return self.get(f"{media_type}/{media_id}", "studios")
    
    # Get a list of movies from trakt api given a list id
    def get_list(self, list_id):
        return self.get(f"lists/{list_id}", "items")

    # Get the list of all watched movies for the user specified in the env file
    def get_watched_movies(self):
        return self.get("watched", "movies", cache=False, need_user=True)

    # Get the list of all watched shows for the user specified in the env file
    def get_watched_shows(self):
        return self.get("watched", "shows", cache=False, need_user=True)

    # Get some stats for the user specified in the env file
    def get_user_stats(self):
        return self.get("stats", "", cache=False, need_user=True)

    # Cache or get data from trakt api by specifying the action and type of media
    # if cache is True, the data will be cached in ./cache/ folder
    # if cache is False, the data will be returned
    def get(self, action, endpoint_type, cache=False, cache_folder="", need_user=False):
        if need_user:
            tmp_url = f"{self.users_url}/{action}/{endpoint_type}"
        else:
            tmp_url = f"{self.base_url}/{action}/{endpoint_type}"

        print(f"Obtaining: {tmp_url}")
        response = requests.get(f"{tmp_url}", headers=self.headers)

        if response.status_code == 404:
            raise ex.ItemNotFoundException(f"Error: {response.status_code} {response.reason}")
        elif response.status_code == 429:
            raise ex.OverRateLimitException(f"Error: {response.status_code} {response.reason}", response.headers.get("Retry-After"))
        elif response.status_code != 200:
            raise Exception(f"Error: {response.status_code} {response.reason}")

        if not response.json():
            raise ex.EmptyResponseException(f"No {endpoint_type} found in {action}")

        print(f"Obtained: {tmp_url}")

        if cache:
            with open(os.path.join(self.base_cache_path, f"{cache_folder}/{action}_{endpoint_type}.json"), "wt") as out_file:
                json.dump(response.json(), out_file, indent=4)
        else:
            return response.json()
