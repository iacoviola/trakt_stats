import requests
import json
import os

import exceptions as ex

class TMDBRequest:

    base_url = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key, root_path):
        self.root_path = root_path
        # Trakt request required headers
        self.headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + api_key
        }

    def get_crew(self, media_id, media_type):
        return self.get(f"{media_type}/{media_id}", "credits")
    
    def get_item_details(self, media_id, media_type):
        return self.get(f"{media_type}", f"{media_id}")

    def create_data_files(self):
        self.get_watched_movies()
        self.get_watched_episodes()
        self.get_watched_shows()
        self.get_movies_ratings()
        self.get_episodes_ratings()
        self.get_shows_ratings()
        self.get_seasons_ratings()
        self.get_movies_history()
        self.get_episodes_ratings()
        self.get_movies_watchlist()
        self.get_episodes_history()
        self.get_shows_watchlist()
        self.get_movies_collection()
        self.get_episodes_collection()
        self.get_shows_collection()
        self.get_user_stats()

    # Cache data from trakt api by specifying the action and type of media
    def get(self, action, endpoint_type, cache=False, caching_path="", oauth=False):
        if oauth:
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
            file_watched = open(os.path.join(self.root_path, f"{caching_path}/{action}_{endpoint_type}.json"), "w")
            file_watched.write(json.dumps(response.json(), separators=(",", ":"), indent=4))
            file_watched.close()
        else:
            return response.json()
        
    def get_watched_movies(self):
        return self.get("watched", "movies", cache=True, caching_path="/movies", oauth=True)

    def get_watched_episodes(self):
        self.get("watched", "episodes")

    def get_watched_shows(self):
        return self.get("watched", "shows", cache=False, oauth=True)

    def get_movies_ratings(self):
        self.get("ratings", "movies")

    def get_episodes_ratings(self):
        self.get("ratings", "episodes")

    def get_shows_ratings(self):
        self.get("ratings", "shows")

    def get_seasons_ratings(self):
        self.get("ratings", "seasons")

    def get_movies_history(self):
        self.get("history", "movies")

    def get_episodes_history(self):
        self.get("history", "episodes")

    def get_movies_watchlist(self):
        self.get("watchlist", "movies")

    def get_shows_watchlist(self):
        self.get("watchlist", "shows")

    def get_movies_collection(self):
        self.get("collection", "movies")

    def get_episodes_collection(self):
        self.get("collection", "episodes")

    def get_shows_collection(self):
        self.get("collection", "shows")

    def get_user_stats(self):
        return self.get("stats", "", cache=False, oauth=True)
