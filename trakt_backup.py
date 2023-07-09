import os
import sys
import subprocess
import json
import time
import progressbar
import threading

from deepdiff import DeepDiff

from dotenv import load_dotenv

from trakt_request import TraktRequest
from tmdb_request import TMDBRequest
import exceptions as ex
from request_reason import RequestReason

import concurrent.futures

"""def sort_func(item):
    return item[1].get("movie", 0) + item[1].get("show", 0)"""

def sort_func(item):
    return item[1]

def load_file(py_list, file_path):
    if os.path.exists(os.path.join(RESULTS_DIR, f"most_watched_{file_path}.json")):
        with open(os.path.join(RESULTS_DIR, f"most_watched_{file_path}.json")) as json_file:
            py_list = json.load(json_file)
    
    if py_list == {}:
        needs_update.append(file_path)
    

load_dotenv()
# We load the necessary infos from the env file
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
BACKUP_ROOT_PATH = os.getenv("BACKUP_ROOT_PATH")
CACHE_DIR = "cache"
RESULTS_DIR = "results"

needs_update = []
trakt_lists = {"imdb_top250": 2142753, "trakt_top250": 4834049, "imdb_bottom100": 2142791, "reddit_top250_2019": 6544049, "statistical_best500": 23629843}
missing_lists = []
movies_details = []

most_watched_actors = {}
most_watched_directors = {}
most_watched_studios = {}
most_watched_genres = {}
most_watched_countries = {}

load_file(most_watched_actors, "actors")
load_file(most_watched_directors, "directors")
load_file(most_watched_studios, "studios")
load_file(most_watched_genres, "genres")
load_file(most_watched_countries, "countries")

if os.path.exists(os.path.join(RESULTS_DIR, "best_of_progress.json")):
    with open(os.path.join(RESULTS_DIR, "best_of_progress.json")) as json_file:
        best_of = json.load(json_file)
else:
    best_of = {}

for key, value in trakt_lists.items():
    if key not in best_of.keys():
        missing_lists.append(key)
        if "lists" not in needs_update:
            needs_update.append("lists")

record_del_startpoint = -1
max_threads = 6
default_indent = 4

progressbar_index = 0
progressbar_widgets = [
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

"""def launch_file(filepath):
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", filepath))
    elif os.name == "nt":
        os.startfile(filepath)
    elif os.name == "posix":
        subprocess.call(("xdg-open", filepath))"""

def generate_json_diff(json1, json2):

    global record_del_startpoint

    movies = []
    diff = DeepDiff(json1, json2, ignore_order=True)

    if "iterable_item_added" in diff:
        for key, movie in diff["iterable_item_added"].items():
            movies.append(movie)
            record_del_startpoint += 1
    if "iterable_item_removed" in diff:
        for key, movie in diff["iterable_item_removed"].items():
            movies.append(movie)

    return movies

def launch_threads(function, n_threads, list_len, type, watched_items):

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)

    with executor:
        for i in range(0, n_threads):
            start = int(i * (list_len / n_threads) + 1)
            if i == 0:
                start = 0
            end = int((i + 1) * (list_len / n_threads))
            if end > list_len:
                end = list_len
            executor.submit(function, start, end, type, watched_items)

"""def update_dict(dictionary, key, i, type):

    global record_del_startpoint

    if i < record_del_startpoint or record_del_startpoint == -1:
        if key in dictionary:
            if type in dictionary[key]:
                dictionary[key][type] += 1
            else:
                dictionary[key][type] = 1
        else:
            dictionary[key] = {type: 1}
    else:
        if dictionary[key][type] > 1:
            dictionary[key][type] -= 1
        else:
            del dictionary[key][type]"""

def update_dict(dictionary, key, i):

    global record_del_startpoint

    if i < record_del_startpoint or record_del_startpoint == -1:
        if key in dictionary:
            dictionary[key] += 1
        else:
            dictionary[key] = 1
    else:
        if dictionary[key] > 1:
            dictionary[key] -= 1
        else:
            del dictionary[key]

def get_crew(start, end, type, watched_items):

    global progressbar_index

    error_occured = False

    for i, item in enumerate(watched_items[start:end]):
        with threading.Lock():
            bar.update(progressbar_index)
            progressbar_index += 1
        while(True):
            try:
                crew = tmdb_request.get_crew(item[type]["ids"]["tmdb"], "tv" if type == "show" else type)
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
            if "actors" in needs_update:
                for actor in crew["cast"]:
                    target = actor["name"]
                    with threading.Lock():
                        update_dict(most_watched_actors, target, i)

            if "directors" in needs_update:
                for crew_p in crew["crew"]:
                    if crew_p["job"] == "Director":
                        target = crew_p["name"]
                        with threading.Lock():
                            update_dict(most_watched_directors, target, i)
        else:
            error_occured = False

"""def get_studios(start, end, type, watched_items):

    global progressbar_index

    error_occured = False

    for i, item in enumerate(watched_items[start:end]):
        with threading.Lock():
            bar.update(progressbar_index)
            progressbar_index += 1
        while(True):
            try:
                tmdb_item = tmdb_request.get_studio(item[type]["ids"]["tmdb"], "tv" if type == "show" else type)
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
            for studio in tmdb_item["production_companies"]:
                target = studio["name"]
                with threading.Lock():
                    update_dict(most_watched_studios, target, i)
        else:
            error_occured = False"""

def get_details(start, end, type, watched_items):
    
        global progressbar_index
    
        error_occured = False
    
        for i, item in enumerate(watched_items[start:end]):
            with threading.Lock():
                bar.update(progressbar_index)
                progressbar_index += 1
            while(True):
                try:
                    tmdb_item = tmdb_request.get_item_details(item[type]["ids"]["tmdb"], "tv" if type == "show" else type)
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
                movies_details.append(tmdb_item)

                if "genres" in needs_update:
                    for genre in tmdb_item["genres"]:
                        target = genre["name"]
                        with threading.Lock():
                            update_dict(most_watched_genres, target, i)

                if "studios" in needs_update:
                    for studio in tmdb_item["production_companies"]:
                        target = studio["name"]
                        with threading.Lock():
                            update_dict(most_watched_studios, target, i)

                if "countries" in needs_update:
                    for country in tmdb_item["production_countries"]:
                        target = country["name"]
                        with threading.Lock():
                            update_dict(most_watched_countries, target, i)
            else:
                error_occured = False

def get_designated_file(type):

    file_status = RequestReason.NO_REASON
    designated_file = None

    with open(os.path.join(CACHE_DIR, f"tmp_watched_{type}s.json"), "w") as new_file:
        if type == "movie":
            new_file.write(json.dumps(trakt_request.get_watched_movies(), separators=(",", ":"), indent=default_indent))
        elif type == "show":
            new_file.write(json.dumps(trakt_request.get_watched_shows(), separators=(",", ":"), indent=default_indent))

    with open(os.path.join(CACHE_DIR, f"tmp_watched_{type}s.json")) as json_file:
        new_file = json.load(json_file)

    latest_file = None

    #if there is no history file, we create one
    if not os.path.isfile(os.path.join(RESULTS_DIR, f"watched_{type}s.json")):
        designated_file = new_file
        file_status = RequestReason.WATCHED_FILE_MISSING
    elif needs_update != []:
        designated_file = new_file
        file_status = RequestReason.RESULTS_FILE_MISSING
    else:
        with open(os.path.join(RESULTS_DIR, f"watched_{type}s.json")) as json_file:
            latest_file = json.load(json_file)

    #if there is history file, we compare it with the new one
    if not designated_file:
        designated_file = generate_json_diff(latest_file, new_file)
        file_status = RequestReason.WATCHED_FILE_DIFFERENT if designated_file != [] else RequestReason.NO_REASON

    return [designated_file, file_status]

def search_movie(watched_movies, top_list):
    movie_list = []
    counter = 0
    for movie in watched_movies:
        for list_movie in top_list:
            if movie["movie"]["ids"]["trakt"] == list_movie["movie"]["ids"]["trakt"]:
                movie_list.append({"id": list_movie['movie']['ids']['trakt'], "title": f"{list_movie['movie']['title']}", "rank": list_movie['rank']})
                counter += 1
                break

    return [counter, len(top_list), movie_list]

# Check if the API key is valid
if len(TRAKT_API_KEY) != 64:
    print("Invalid Trakt API key, please check your trakt_request.py file")
    sys.exit()

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

trakt_request = TraktRequest(TRAKT_API_KEY, TRAKT_USERNAME, CACHE_DIR)
tmdb_request = TMDBRequest(TMDB_API_KEY, CACHE_DIR)

#try:
trakt_request.get_cached_data()

with open(os.path.join(RESULTS_DIR, "user_stats.json"), "w") as stats_file:
    stats_file.write(json.dumps(trakt_request.get_user_stats(), separators=(",", ":"), indent=default_indent))   

watched_movies = get_designated_file("movie")
movies_length = len(watched_movies[0])

watched_shows = get_designated_file("show")
shows_length = len(watched_shows[0])

get_in_cond = watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING
crew_cond = "actors" in needs_update or "directors" in needs_update

if get_in_cond or crew_cond:

    if watched_movies[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=movies_length  , redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_crew, max_threads, movies_length, "movie", watched_movies[0])

        bar.finish()

    if watched_shows[1] >= RequestReason.WATCHED_FILE_MISSING or crew_cond:
        bar = progressbar.ProgressBar(maxval=shows_length, redirect_stdout=True, widgets=progressbar_widgets)

        progressbar_index = 0
        launch_threads(get_crew, max_threads, shows_length, "show", watched_shows[0])

        bar.finish()

    if "actors" in needs_update or get_in_cond:
        most_watched_actors = {k: v for k, v in sorted(most_watched_actors.items(), key=sort_func, reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_actors.json"), "w") as outfile:
            json.dump(most_watched_actors, outfile, indent=default_indent)

    if "directors" in needs_update or get_in_cond:
        most_watched_directors = {k: v for k, v in sorted(most_watched_directors.items(), key=sort_func, reverse=True)}
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
        most_watched_studios = {k: v for k, v in sorted(most_watched_studios.items(), key=sort_func, reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_studios.json"), "w") as outfile:
            json.dump(most_watched_studios, outfile, indent=default_indent)

    if "genres" in needs_update or get_in_cond:
        most_watched_genres = {k: v for k, v in sorted(most_watched_genres.items(), key=sort_func, reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_genres.json"), "w") as outfile:
            json.dump(most_watched_genres, outfile, indent=default_indent)

    if "countries" in needs_update or get_in_cond:
        most_watched_countries = {k: v for k, v in sorted(most_watched_countries.items(), key=sort_func, reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_countries.json"), "w") as outfile:
            json.dump(most_watched_countries, outfile, indent=default_indent)

for top, list_id in trakt_lists.items():
    if get_in_cond or top in missing_lists:
        with open(os.path.join(CACHE_DIR, f"{top}.json"), "w") as list_file:
            current_list = trakt_request.get_list(list_id)
            list_file.write(json.dumps(current_list, separators=(",", ":"), indent=default_indent))

            result = search_movie(watched_movies[0], current_list)
            best_of[top] = {"watched": result[0], "total": result[1]}
            best_of[top]['watched_movies'] = sorted(result[2], key=lambda k: k['rank'])

        os.remove(os.path.join(CACHE_DIR, f"{top}.json"))

with open(os.path.join(RESULTS_DIR, "best_of_progress.json"), "w") as outfile:
    json.dump(best_of, outfile, separators=(",", ":"), indent=default_indent)

os.rename(os.path.join(CACHE_DIR, "tmp_watched_movies.json"), os.path.join(RESULTS_DIR, "watched_movies.json"))
os.rename(os.path.join(CACHE_DIR, "tmp_watched_shows.json"), os.path.join(RESULTS_DIR, "watched_shows.json"))