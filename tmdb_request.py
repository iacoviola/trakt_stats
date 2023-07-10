import requests
import json
import os

import exceptions as ex

class TMDBRequest:

    # TMDB api base url
    base_url = "https://api.themoviedb.org/3"

    # TMDB image base url
    image_url = "https://image.tmdb.org/t/p/w500"
    
    # Initialize the TMDBRequest class with the api key and the base path for the cache
    def __init__(self, api_key, cache_path):
        self.base_cache_path = cache_path
        
        # TMDB Authorization header
        self.headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + api_key
        }

    # Get crew from TMDB api given an item id and the type of the item (movie/show)
    def get_crew(self, media_id, media_type):
        return self.get(f"{media_type}/{media_id}", "credits" if media_type == "movie" else "aggregate_credits")
    
    # Get item details from TMDB api given an item id and the type of the item (movie/show)
    # As of now, this method is used to get:
    # - Studio for movies
    # - Networks for shows
    # - Genres for movies/shows
    # - Countries for movies/shows
    def get_item_details(self, media_id, media_type):
        return self.get(f"{media_type}", f"{media_id}")
    
    # Get an image from TMDB api given an item's image path, the item name and the cache folder
    def cache_item_image(self, image_path, item_name, directory, ex):
        with open(os.path.join(directory, f"{item_name}.{ex}"), "wb") as outfile:
            print(f"Obtaining: {self.image_url}{image_path}")
            response = requests.get(f"{self.image_url}{image_path}")
            print(f"Obtained: {self.image_url}{image_path}")
            outfile.write(response.content)
    
    # Cache or get data from trakt api by specifying the action and type of media
    # if cache is True, the data will be cached in ./cache/ folder
    # if cache is False, the data will be returned
    def get(self, action, endpoint_type, cache=False, cache_folder=""):
        
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
            with open(os.path.join(self.base_cache_path, f"{cache_folder}/{action}_{endpoint_type}.json"), "wt") as outfile:
                json.dump(response.json(), outfile, indent=4)
        else:
            return response.json()
