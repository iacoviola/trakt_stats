import os
import sys
import json
import time
import progressbar
import threading

from deepdiff import DeepDiff

from typing import Callable, Tuple

from dotenv import load_dotenv

from trakt_request import TraktRequest
from tmdb_request import TMDBRequest
import exceptions as ex
from request_reason import RequestReason
from graph_drawer import GraphDrawer
from arguments import vprint

import logging

# Sort dict based on the number of movies and shows watched for that specific item
def sort_func(order_type: bool = False) -> Callable[[dict], int]:
    if order_type:
        return lambda item: item[1].get("movies", 0) + item[1].get("shows", 0)
    return lambda item: item[1]

# Load the json files if they exist, else return an empty dict
def load_file(file_path: str) -> dict:
    py_dict: dict = {}

    try:
        with open(os.path.join(RESULTS_DIR, f"most_watched_{file_path}.json"), "rt") as json_file:
            py_dict = json.load(json_file)
    except FileNotFoundError:
        pass
    
    if py_dict == {}:
        needs_update.append(file_path)

    return py_dict

# Check if some lists are missing from the best_of_progress.json file
def check_best_of_contents(top_list: dict, missing_list: list) -> None:
    for key, value in top_list.items():
        if key not in best_of.keys():
            missing_list.append(key)
            if "lists" not in needs_update:
                needs_update.append("lists")

# Returns the diffs between two json files as a valid json list
def generate_json_diff(json1: dict, json2: dict) -> list:

    global record_del_startpoint

    missing_items: list = []
    diff = DeepDiff(json1, json2, ignore_order=True)

    if "iterable_item_added" in diff:
        for key, item in diff["iterable_item_added"].items():
            missing_items.append(item)
            record_del_startpoint += 1
    if "iterable_item_removed" in diff:
        for key, item in diff["iterable_item_removed"].items():
            missing_items.append(item)

    return missing_items

def launch_threads(function: Callable[[int, int, str, dict], None], n_threads: int, list_len: int, media_type: str, watched_items: dict) -> None:
    
    global progressbar_index

    progressbar_index = 0
    
    threads: list = []

    for i in range(0, n_threads):
        start: int = int(i * (list_len / n_threads))
        end: int = int((i + 1) * (list_len / n_threads))
        if end > list_len:
            end = list_len
        
        threads.append(threading.Thread(target=function, args=(start, end, media_type, watched_items)))
        threads[i].start()

    for i in range(0, n_threads):
        threads[i].join()

def update_dict(dictionary: dict, key: str, i: int, media_type: str = "movies") -> None:

    global record_del_startpoint

    if i < record_del_startpoint or record_del_startpoint == -1:
        if key in dictionary:
            if media_type in dictionary[key]:
                dictionary[key][media_type] += 1
            else:
                dictionary[key][media_type] = 1
        else:
            dictionary[key] = {}
            dictionary[key][media_type] = 1
    else:
        if dictionary[key][media_type] > 1:
            dictionary[key][media_type] -= 1
        else:
            del dictionary[key][media_type]

def get_crew(start: int, end: int, media_type: str, watched_items: dict) -> None:

    global progressbar_index

    error_occured: bool = False

    for i, item in enumerate(watched_items[start:end]):
        with threading.Lock():
            bar.update(progressbar_index)
            progressbar_index += 1
        while(True):
            try:
                crew: dict = tmdb_request.get_crew(item[media_type]["ids"]["tmdb"], "tv" if media_type == "show" else media_type)
            except ex.OverRateLimitException as e:
                print(e)
                print("Retrying in " + str(e.retry_after()) + " seconds...")
                time.sleep(e.retry_after())
            except (ex.EmptyResponseException, ex.ItemNotFoundException) as e:
                print(e)
                error_occured = True
                break
            else:
                break

        if not error_occured:
            #if "actors" in needs_update:
            for actor in crew["cast"]:
                target: str = actor["name"]
                with threading.Lock():
                    update_dict(most_watched_actors, target, i, media_type + "s")
                    if "profile_path" not in most_watched_actors[target]:
                        most_watched_actors[target]["profile_path"] = actor["profile_path"]

            #if "directors" in needs_update and media_type == "movie":
            if media_type == "movie":
                for crew_p in crew["crew"]:
                    if crew_p["job"] == "Director":
                        target: str = crew_p["name"] 
                        with threading.Lock():
                            update_dict(most_watched_directors, target, i)
                            if "profile_path" not in most_watched_directors[target]:
                                most_watched_directors[target]["profile_path"] = crew_p["profile_path"]
        else:
            error_occured = False

def get_details(start: int, end: int, media_type: str, watched_items: list) -> None:
    
        global progressbar_index
    
        error_occured: bool = False
    
        for i, item in enumerate(watched_items[start:end]):
            with threading.Lock():
                bar.update(progressbar_index)
                progressbar_index += 1
            while(True):
                try:
                    tmdb_item: dict = tmdb_request.get_item_details(item[media_type]["ids"]["tmdb"], "tv" if media_type == "show" else media_type)
                except ex.OverRateLimitException as e:
                    print(e)
                    print("Retrying in " + str(e.retry_after()) + " seconds...")
                    time.sleep(e.retry_after())
                except (ex.EmptyResponseException, ex.ItemNotFoundException) as e:
                    print(e)
                    error_occured = True
                    break
                else:
                    break

            if not error_occured:
                #if "genres" in needs_update:
                for genre in tmdb_item["genres"]:
                    target: str = genre["name"]
                    with threading.Lock():
                        update_dict(most_watched_genres, target, i, media_type + "s")

                #if "studios" in needs_update:
                for studio in tmdb_item["networks" if media_type == "show" else "production_companies"]:
                    target: str = studio["name"]
                    with threading.Lock():
                        if media_type == "movie":
                            update_dict(most_watched_studios, target, i, media_type + "s")
                            if "logo_path" not in most_watched_studios[target]:
                                most_watched_studios[target]["logo_path"] = studio["logo_path"]
                        else:
                            update_dict(most_watched_networks, target, i, media_type + "s")
                            if "logo_path" not in most_watched_networks[target]:
                                most_watched_networks[target]["logo_path"] = studio["logo_path"]

                #if "countries" in needs_update:
                for country in tmdb_item["production_countries"]:
                    target: str = country["iso_3166_1"]
                    with threading.Lock():
                        update_dict(most_watched_countries, target, i, media_type + "s")
                        if "name" not in most_watched_countries[target]:
                            most_watched_countries[target]["name"] = country["name"]
            else:
                error_occured = False

def get_designated_file(media_type: str) -> Tuple[dict, RequestReason]:

    file_status: RequestReason = RequestReason.NO_REASON
    designated_file: dict | None = None

    with open(os.path.join(CACHE_DIR, f"tmp_watched_{media_type}s.json"), "w") as new_file_handle:
        if media_type == "movie":
            new_file: dict = trakt_request.get_watched_movies()
        else:
            new_file: dict = trakt_request.get_watched_shows()
        json.dump(new_file, new_file_handle, indent=default_indent)

    latest_file: dict | None = None

    #if there is no history file, we create one
    if not os.path.isfile(os.path.join(RESULTS_DIR, f"watched_{media_type}s.json")):
        designated_file = new_file
        file_status = RequestReason.WATCHED_FILE_MISSING
    elif needs_update != []:
        designated_file = new_file
        file_status = RequestReason.RESULTS_FILE_MISSING
    else:
        with open(os.path.join(RESULTS_DIR, f"watched_{media_type}s.json")) as json_file:
            latest_file = json.load(json_file)

    #if there is history file, we compare it with the new one
    if not designated_file:
        designated_file = generate_json_diff(new_file, latest_file)
        file_status = RequestReason.WATCHED_FILE_DIFFERENT if designated_file != [] else RequestReason.NO_REASON

    return [designated_file, file_status]

def search_item(watched_items: dict, top_list_dict: dict, media_type: str) -> Tuple[int, int, list]:
    items_list: list = []
    counter: int = 0
    for item in watched_items:
        for item_list in top_list_dict:
            if item[media_type]["ids"]["trakt"] == item_list[media_type]["ids"]["trakt"]:
                items_list.append({"id": item_list[media_type]['ids']['trakt'], "title": f"{item_list[media_type]['title']}", "rank": item_list['rank']})
                counter += 1
                break

    return [counter, len(top_list_dict), items_list]

def clear_list(dict_name: dict, media_type: str) -> None:
    for key in dict_name:
        if media_type in dict_name[key].keys():
            dict_name[key][media_type] = 0

def dump_images(dict_name: dict, dir_name: str, person: bool) -> None:
    if person:
        path_type = "profile_path"
    else:
        path_type = "logo_path"

    for item in dict(sorted(dict_name.items(), key=sort_func(True), reverse=True)[:10]):
        image_path = dict_name[item][path_type]
        if image_path is not None:
            ex: str = image_path.split(".")[-1]
            if not os.path.isfile(os.path.join(dir_name, f"{item}.{ex}")):
                tmdb_request.cache_item_image(image_path, item, dir_name, ex)


def dump_files(dict_name: dict, dump_type: str) -> None:
    if dump_type in needs_update or get_in_cond:
        dict_name = {k: v for k, v in sorted(dict_name.items(), key=sort_func(True), reverse=True)}
        with open(os.path.join(RESULTS_DIR, f"most_watched_{dump_type}.json"), "wt") as outfile:
            json.dump(dict_name, outfile, indent=default_indent)
            vprint(f"Dumped most_watched_{dump_type}.json")

load_dotenv()

# Loading the necessary infos from the env file
TRAKT_API_KEY: str = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY")
TRAKT_USERNAME: str = os.getenv("TRAKT_USERNAME")

CACHE_DIR: str = "cache"
RESULTS_DIR: str = "results"
IMG_DIR: str = "results/img"
MAPS_DIR: str = "results/maps"
GRAPHS_DIR: str = "results/graphs"
ACTORS_DIR: str = "results/img/actors"
DIRECTORS_DIR: str = "results/img/directors"
STUDIOS_DIR: str = "results/img/studios"
NETWORKS_DIR: str = "results/img/networks"

needs_update: list = []

missing_top_movielists: list = []
top_movielists_dict: dict = {"imdb_top250_movies": 2142753, 
                             "trakt_top250_movies": 4834049, 
                             "imdb_bottom100_movies": 2142791, 
                             "reddit_top250_2019_movies": 6544049,
                             "statistical_best500_movies": 23629843,
                             "oscar_best_picture_movies": 25486243}

missing_top_showslists: list = []
top_showslists_dict: dict = {"imdb_top250_shows": 2143363, 
                             "trakt_top250_shows": 4834057, 
                             "rollingstone_top100_shows": 2748259}

media_types: list = ["movies", "shows"]
extended_media_types: list = ["movies", "shows", "seasons", "episodes"]

most_watched_actors: dict = load_file("actors")
most_watched_directors: dict = load_file("directors")
most_watched_studios: dict = load_file("studios")
most_watched_networks: dict = load_file("networks")
most_watched_genres: dict = load_file("genres")
most_watched_countries: dict = load_file("countries")

try:
    with open("country_codes.json", "rt") as json_file:
        country_codes: dict = json.load(json_file)
except FileNotFoundError:
    country_codes: dict = {}
    print("Country codes file not found. Please, add it back in the root folder, no maps will be generated.")

try:
    with open(os.path.join(RESULTS_DIR, "best_of_progress.json"), "rt") as json_file:
        best_of: dict = json.load(json_file)
except FileNotFoundError:
    best_of: dict = {}
    needs_update.append("lists")

if dict != {}:
    check_best_of_contents(top_movielists_dict, missing_top_movielists)
    check_best_of_contents(top_showslists_dict, missing_top_showslists)

record_del_startpoint: int = -1
max_threads: int = 6
default_indent: int = 4

progressbar_index: int = 0
progressbar_widgets: list = [
    " [", progressbar.Timer(), "] ",
    progressbar.Bar(),
    "(", progressbar.SimpleProgress(), ") ",
]

if not TRAKT_API_KEY:
    print("Please, add your Trakt API key in the .env file")
    sys.exit()
if not TMDB_API_KEY:
    print("Please, add your TMDB API key in the .env file")
    sys.exit()
if not TRAKT_USERNAME:
    print("Please, add your Trakt username in the .env file")
    sys.exit()

# Check if the API key is valid
if len(TRAKT_API_KEY) != 64:
    print("Invalid Trakt API key, please check your trakt_request.py file")
    sys.exit()

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(MAPS_DIR, exist_ok=True)
os.makedirs(GRAPHS_DIR, exist_ok=True)
os.makedirs(ACTORS_DIR, exist_ok=True)
os.makedirs(DIRECTORS_DIR, exist_ok=True)
os.makedirs(STUDIOS_DIR, exist_ok=True)
os.makedirs(NETWORKS_DIR, exist_ok=True)

# Initialize the requests objects
trakt_request: TraktRequest = TraktRequest(TRAKT_API_KEY, TRAKT_USERNAME, CACHE_DIR)
tmdb_request: TMDBRequest = TMDBRequest(TMDB_API_KEY, CACHE_DIR)

# Get the watched movies and shows for the user
watched_movies: dict = get_designated_file("movie")
movies_length: int = len(watched_movies[0])

watched_shows: dict = get_designated_file("show")
shows_length: int = len(watched_shows[0])

# This is the condition which checks if watched_movies or watched_shows are the ones needing an update
get_in_cond: bool = watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING
# This is the condition which checks if the actors or directors files need an update
crew_cond: bool = "actors" in needs_update or "directors" in needs_update

# If the watched_movies file is missing, we clear the lists of all movies
if watched_movies[1] == RequestReason.WATCHED_FILE_MISSING:
    clear_list(most_watched_genres, "movies")
    clear_list(most_watched_studios, "movies")
    clear_list(most_watched_countries, "movies")
    clear_list(most_watched_actors, "movies")
    clear_list(most_watched_directors, "movies")

# If the watched_shows file is missing, we clear the lists of all shows
if watched_shows[1] == RequestReason.WATCHED_FILE_MISSING:
    clear_list(most_watched_genres, "shows")
    clear_list(most_watched_networks, "shows")
    clear_list(most_watched_countries, "shows")
    clear_list(most_watched_actors, "shows")

# Get in only if watched_movies or watched_shows need update or if the actors or directors files need an update
if get_in_cond or crew_cond:

    if watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=movies_length, redirect_stdout=True, widgets=progressbar_widgets)
        launch_threads(get_crew, max_threads, movies_length, "movie", watched_movies[0])
        bar.finish()

    if watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=shows_length, redirect_stdout=True, widgets=progressbar_widgets)
        launch_threads(get_crew, max_threads, shows_length, "show", watched_shows[0])
        bar.finish()

    dump_files(most_watched_actors, "actors")
    dump_files(most_watched_directors, "directors")

# This is the condition which checks if the studios, genres or countries files need an update
details_cond = "genres" in needs_update or "countries" in needs_update

# Get in only if watched_movies or watched_shows need update or if the studios, networks, genres or countries files need an update
if get_in_cond or details_cond:
    if watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or details_cond or "studios" in needs_update:
        bar = progressbar.ProgressBar(maxval=movies_length, redirect_stdout=True, widgets=progressbar_widgets)
        launch_threads(get_details, max_threads, movies_length, "movie", watched_movies[0])
        bar.finish()
    
    if watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING or details_cond or "networks" in needs_update:
        bar = progressbar.ProgressBar(maxval=shows_length, redirect_stdout=True, widgets=progressbar_widgets)
        launch_threads(get_details, max_threads, shows_length, "show", watched_shows[0])
        bar.finish()

    dump_files(most_watched_genres, "genres")
    dump_files(most_watched_studios, "studios")
    dump_files(most_watched_networks, "networks")
    dump_files(most_watched_countries, "countries")

for top, list_id in top_movielists_dict.items():
    if get_in_cond or top in missing_top_movielists:
        current_list_dict = trakt_request.get_list(list_id)

        result: Tuple[int, int, list] = search_item(watched_movies[0], current_list_dict, "movie")
        best_of[top] = {"watched": result[0], "total": result[1]}
        best_of[top]['watched_movies'] = sorted(result[2], key=lambda k: k['rank'])

for top, list_id in top_showslists_dict.items():
    if get_in_cond or top in missing_top_showslists:
        current_list_dict = trakt_request.get_list(list_id)

        result: Tuple[int, int, list] = search_item(watched_shows[0], current_list_dict, "show")
        best_of[top] = {"watched": result[0], "total": result[1]}
        best_of[top]['watched_shows'] = sorted(result[2], key=lambda k: k['rank'])

dump_images(most_watched_actors, ACTORS_DIR, person=True)
dump_images(most_watched_directors, DIRECTORS_DIR, person=True)
dump_images(most_watched_studios, STUDIOS_DIR, person=False)
dump_images(most_watched_networks, NETWORKS_DIR, person=False)

with open(os.path.join(RESULTS_DIR, "best_of_progress.json"), "wt") as outfile:
    json.dump(best_of, outfile, indent=default_indent)

for media in media_types:
    os.replace(os.path.join(CACHE_DIR, f"tmp_watched_{media}.json"), os.path.join(RESULTS_DIR, f"watched_{media}.json"))

 # Dump the user stats in user_stats.json
with open(os.path.join(RESULTS_DIR, "user_stats.json"), "wt") as stats_file:
    user_stats: dict = trakt_request.get_user_stats()
    json.dump(user_stats, stats_file, indent=default_indent)

try:
    totals = user_stats["ratings"]["distribution"].values()
except Exception as e:
    totals = []

graph_drawer = GraphDrawer(["png", "svg", "mll"])

try:
    ratings = {}
    for media in extended_media_types:
        current_media_ratings = trakt_request.get_user_ratings(media)
        ratings[media] = [0] * 10
        for rating in current_media_ratings:
            ratings[media][rating['rating'] - 1] += 1

    graph_drawer.ratings_graph(ratings, totals, os.path.join(GRAPHS_DIR, f"ratings_distribution"))
    vprint("Ratings distribution graph generated")
except Exception as e:
    logging.error(f"Error while generating ratings graph: {e}")

for media in media_types:
    if "genres" in needs_update or get_in_cond:
        graph_drawer.genres_graph(most_watched_genres, os.path.join(GRAPHS_DIR, f"{media}_genres"), media)
    if "countries" in needs_update or get_in_cond or country_codes != {}:
        graph_drawer.draw_countries_map(most_watched_countries, country_codes, os.path.join(MAPS_DIR, f"{media}_countries"), media)
    elif country_codes == {}:
        logging.warning("Country codes not found, countries map not generated")