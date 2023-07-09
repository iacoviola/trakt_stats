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

def sort_func(order_type: bool = False) -> Callable[[dict], int]:
    if order_type:
        return lambda item: item[1].get("movies", 0) + item[1].get("shows", 0)
    return lambda item: item[1]

def load_file(file_path: str) -> dict:
    py_dict: dict = {}

    if os.path.exists(os.path.join(RESULTS_DIR, f"most_watched_{file_path}.json")):
        with open(os.path.join(RESULTS_DIR, f"most_watched_{file_path}.json")) as json_file:
            py_dict = json.load(json_file)
    
    if py_dict == {}:
        needs_update.append(file_path)

    return py_dict
    

load_dotenv()
# We load the necessary infos from the env file
TRAKT_API_KEY: str = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY")
TRAKT_USERNAME: str = os.getenv("TRAKT_USERNAME")
BACKUP_ROOT_PATH: str = os.getenv("BACKUP_ROOT_PATH")
CACHE_DIR: str = "cache"
RESULTS_DIR: str = "results"

needs_update: list = []
top_lists_dict: dict = {"imdb_top250": 2142753, "trakt_top250": 4834049, "imdb_bottom100": 2142791, "reddit_top250_2019": 6544049, "statistical_best500": 23629843}
missing_top_lists: list = []
media_types: list = ["movies", "shows"]

most_watched_actors: dict = load_file("actors")
most_watched_directors: dict = load_file("directors")
most_watched_studios: dict = load_file("studios")
most_watched_networks: dict = load_file("networks")
most_watched_genres: dict = load_file("genres")
most_watched_countries: dict = load_file("countries")

if os.path.exists(os.path.join(RESULTS_DIR, "best_of_progress.json")):
    with open(os.path.join(RESULTS_DIR, "best_of_progress.json")) as json_file:
        best_of: dict = json.load(json_file)
else:
    best_of: dict = {}

for key, value in top_lists_dict.items():
    if key not in best_of.keys():
        missing_top_lists.append(key)
        if "lists" not in needs_update:
            needs_update.append("lists")

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

def update_dict(dictionary: dict, key: str, i: int, media_type: str | None = None) -> None:

    global record_del_startpoint

    if i < record_del_startpoint or record_del_startpoint == -1:
        if key in dictionary:
            if media_type:
                dictionary[key][media_type] += 1
            else:
                dictionary[key] += 1
        else:
            if media_type:
                dictionary[key] = {"movies": 0, "shows": 0}
                dictionary[key][media_type] += 1
            else:
                dictionary[key] = 1
    else:
        if media_type:
            if dictionary[key][media_type] > 1:
                dictionary[key][media_type] -= 1
            else:
                del dictionary[key][media_type]
        else:
            if dictionary[key] > 1:
                dictionary[key] -= 1
            else:
                del dictionary[key]

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

            #if "directors" in needs_update and media_type == "movie":
            if media_type == "movie":
                for crew_p in crew["crew"]:
                    if crew_p["job"] == "Director":
                        target: str = crew_p["name"] 
                        with threading.Lock():
                            update_dict(most_watched_directors, target, i)
        else:
            error_occured = False

def get_details(start: int, end: int, media_type: str, watched_items: dict) -> None:
    
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
                except (ex.EmptyResponseException, ex.NotFoundException) as e:
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
                for studio in tmdb_item["production_companies"]:
                    target: str = studio["name"]
                    with threading.Lock():
                        if media_type == "movie":
                            update_dict(most_watched_studios, target, i)
                        else:
                            update_dict(most_watched_networks, target, i)

                #if "countries" in needs_update:
                for country in tmdb_item["production_countries"]:
                    target: str = country["name"]
                    with threading.Lock():
                        update_dict(most_watched_countries, target, i, media_type + "s")
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
        new_file_handle.write(json.dumps(new_file, separators=(',', ':'), indent=4))

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
        designated_file = generate_json_diff(latest_file, new_file)
        file_status = RequestReason.WATCHED_FILE_DIFFERENT if designated_file != [] else RequestReason.NO_REASON

    return [designated_file, file_status]

def search_movie(watched_movies: dict, top_list_dict: dict) -> Tuple[int, int, list]:
    movie_list: list = []
    counter: int = 0
    for movie in watched_movies:
        for list_movie in top_list_dict:
            if movie["movie"]["ids"]["trakt"] == list_movie["movie"]["ids"]["trakt"]:
                movie_list.append({"id": list_movie['movie']['ids']['trakt'], "title": f"{list_movie['movie']['title']}", "rank": list_movie['rank']})
                counter += 1
                break

    return [counter, len(top_list_dict), movie_list]

def clear_list(dict_name: dict, media_type: str) -> None:
    for key in dict_name:
        if media_type in dict_name[key].keys():
            dict_name[key][media_type] = 0

# Check if the API key is valid
if len(TRAKT_API_KEY) != 64:
    print("Invalid Trakt API key, please check your trakt_request.py file")
    sys.exit()

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

trakt_request: TraktRequest = TraktRequest(TRAKT_API_KEY, TRAKT_USERNAME, CACHE_DIR)
tmdb_request: TMDBRequest = TMDBRequest(TMDB_API_KEY, CACHE_DIR)

with open(os.path.join(RESULTS_DIR, "user_stats.json"), "w") as stats_file:
    stats_file.write(json.dumps(trakt_request.get_user_stats(), separators=(",", ":"), indent=default_indent))   

watched_movies: dict = get_designated_file("movie")
movies_length: int = len(watched_movies[0])

watched_shows: dict = get_designated_file("show")
shows_length: int = len(watched_shows[0])

get_in_cond: bool = watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING
crew_cond: bool = "actors" in needs_update or "directors" in needs_update

if watched_movies[1] == RequestReason.WATCHED_FILE_MISSING:
    clear_list(most_watched_genres, "movie")
    clear_list(most_watched_studios, "movie")
    clear_list(most_watched_countries, "movie")
    clear_list(most_watched_actors, "movie")
    most_watched_directors = {}

if watched_shows[1] == RequestReason.WATCHED_FILE_MISSING:
    clear_list(most_watched_genres, "show")
    clear_list(most_watched_studios, "show")
    clear_list(most_watched_countries, "show")
    clear_list(most_watched_actors, "show")

if get_in_cond or crew_cond:

    if watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=movies_length, redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_crew, max_threads, movies_length, "movie", watched_movies[0])

        bar.finish()

    if watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=shows_length, redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_crew, max_threads, shows_length, "show", watched_shows[0])

        bar.finish()

    if "actors" in needs_update or get_in_cond:
        most_watched_actors = {k: v for k, v in sorted(most_watched_actors.items(), key=sort_func(True), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_actors.json"), "w") as outfile:
            json.dump(most_watched_actors, outfile, indent=default_indent)

    if "directors" in needs_update or get_in_cond:
        most_watched_directors = {k: v for k, v in sorted(most_watched_directors.items(), key=sort_func(), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_directors.json"), "w") as outfile:
            json.dump(most_watched_directors, outfile, indent=default_indent)

details_cond = "studios" in needs_update or "genres" in needs_update or "countries" in needs_update

if get_in_cond or details_cond:
    if watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or details_cond:
        bar = progressbar.ProgressBar(maxval=movies_length, redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_details, max_threads, movies_length, "movie", watched_movies[0])

        bar.finish()
    
    if watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING or details_cond:
        bar = progressbar.ProgressBar(maxval=shows_length, redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_details, max_threads, shows_length, "show", watched_shows[0])
        
        bar.finish()

    if "studios" in needs_update or get_in_cond:
        most_watched_studios = {k: v for k, v in sorted(most_watched_studios.items(), key=sort_func(), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_studios.json"), "w") as outfile:
            json.dump(most_watched_studios, outfile, indent=default_indent)

    if "networks" in needs_update or get_in_cond:
        most_watched_networks = {k: v for k, v in sorted(most_watched_networks.items(), key=sort_func(), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_networks.json"), "w") as outfile:
            json.dump(most_watched_networks, outfile, indent=default_indent)

    if "genres" in needs_update or get_in_cond:
        most_watched_genres = {k: v for k, v in sorted(most_watched_genres.items(), key=sort_func(True), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_genres.json"), "w") as outfile:
            json.dump(most_watched_genres, outfile, indent=default_indent)

    if "countries" in needs_update or get_in_cond:
        most_watched_countries = {k: v for k, v in sorted(most_watched_countries.items(), key=sort_func(True), reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_countries.json"), "w") as outfile:
            json.dump(most_watched_countries, outfile, indent=default_indent)

for top, list_id in top_lists_dict.items():
    if get_in_cond or top in missing_top_lists:
        current_list_dict = trakt_request.get_list(list_id)

        result: Tuple[int, int, list] = search_movie(watched_movies[0], current_list_dict)
        best_of[top] = {"watched": result[0], "total": result[1]}
        best_of[top]['watched_movies'] = sorted(result[2], key=lambda k: k['rank'])


with open(os.path.join(RESULTS_DIR, "best_of_progress.json"), "w") as outfile:
    json.dump(best_of, outfile, separators=(",", ":"), indent=default_indent)

for media in media_types:
    os.remove(os.path.join(RESULTS_DIR, f"watched_{media}.json"))
    os.rename(os.path.join(CACHE_DIR, f"tmp_watched_{media}.json"), os.path.join(RESULTS_DIR, f"watched_{media}.json"))