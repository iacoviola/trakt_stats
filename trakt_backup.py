import os
import sys
import subprocess
import argparse
import json
import time
import progressbar
import threading

from deepdiff import DeepDiff
from deepdiff.helper import CannotCompare

from pprint import pprint

from dotenv import load_dotenv

from trakt_request import TraktRequest

import exceptions as ex

load_dotenv()
# We load the necessary infos from the env file
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
BACKUP_ROOT_PATH = os.getenv("BACKUP_ROOT_PATH")
CACHE_DIR = "cache"
RESULTS_DIR = "results"

if os.path.exists(os.path.join(RESULTS_DIR, "most_watched_actors.json")):
    with open(os.path.join(RESULTS_DIR, "most_watched_actors.json")) as json_file:
        most_watched_actors = json.load(json_file)
else:
    most_watched_actors = {}

if os.path.exists(os.path.join(RESULTS_DIR, "most_watched_directors.json")):
    with open(os.path.join(RESULTS_DIR, "most_watched_directors.json")) as json_file:
        most_watched_directors = json.load(json_file)
else:
    most_watched_directors = {}

needs_update = "actors" if most_watched_actors == {} and most_watched_directors != {} else "directors" if most_watched_actors != {} and most_watched_directors == {} else "both" if most_watched_actors == {} and most_watched_directors == {} else "none"

if os.path.exists(os.path.join(RESULTS_DIR, "most_watched_studios.json")):
    with open(os.path.join(RESULTS_DIR, "most_watched_studios.json")) as json_file:
        most_watched_studios = json.load(json_file)
else:
    most_watched_studios = {}

length = 0
index = 0
n_skip = -1
are_different = False

if not TRAKT_API_KEY:
    print("Please, add your Trakt API key in the .env file")
    sys.exit()

def launch_file(filepath):
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", filepath))
    elif os.name == "nt":
        os.startfile(filepath)
    elif os.name == "posix":
        subprocess.call(("xdg-open", filepath))

def compare_function(x, y, level=None):
    try:
        return x["movie"]["ids"]["trakt"] == y["movie"]["ids"]["trakt"]
    except Exception:
        raise CannotCompare from None

def generate_json_diff(json1, json2):

    global n_skip

    movies = []
    diff = DeepDiff(json1, json2, ignore_order=True)

    if "iterable_item_added" in diff:
        for key, movie in diff["iterable_item_added"].items():
            movies.append(movie)
            n_skip += 1
    if "iterable_item_removed" in diff:
        for key, movie in diff["iterable_item_removed"].items():
            movies.append(movie)

    return movies

def launch_threads(function, n_threads, list_len):

    threads = []

    if list_len >= 24:
        for i in range(0, n_threads):
            start = int(i * (list_len / n_threads) + 1)
            if i == 0:
                start = 0
            end = int((i + 1) * (list_len / n_threads))
            if end > list_len:
                end = list_len
            threads.append(threading.Thread(target=function, args=(start, end)))
            threads[i].start()

        for i in range(0, n_threads):
            threads[i].join()
    else:
        get_crew(0, list_len)

def update_dict(dictionary, key, i):
    if i < n_skip or n_skip == -1:
        if key in dictionary:
            dictionary[key] += 1
        else:
            dictionary[key] = 1
    else:
        if dictionary[key] > 1:
            dictionary[key] -= 1
        else:
            del dictionary[key]

def get_crew(start, end):

    global index

    for i, movie in enumerate(watched_movies[start:end]):
        with threading.Lock():
            bar.update(index)
            index += 1
        while(True):
            try:
                crew = trakt_request.get_crew(movie["movie"]["ids"]["trakt"], "movies")
            except ex.OverRateLimitException as e:
                print(e)
                time.sleep(e.retry_after())
            except ex.EmptyResponseException as e:
                print(e)
                break
            else:
                break

        if needs_update == "actors" or needs_update == "both":
            for actor in crew["cast"]:
                target = actor["person"]["name"]
                with threading.Lock():
                    update_dict(most_watched_actors, target, i)

        if needs_update == "directors" or needs_update == "both":
            for director in crew["crew"]["directing"]:
                if director["job"] == "Director":
                    target = director["person"]["name"]
                    with threading.Lock():
                        update_dict(most_watched_directors, target, i)

def get_studios(start, end):

    global index

    for i, movie in enumerate(watched_movies[start:end]):
        with threading.Lock():
            bar.update(index)
            index += 1
        while(True):
            try:
                studios = trakt_request.get_studio(movie["movie"]["ids"]["trakt"], "movies")
            except ex.OverRateLimitException as e:
                print(e)
                time.sleep(e.retry_after())
            except ex.EmptyResponseException as e:
                print(e)
                break
            else:
                break

        for studio in studios:
            target = studio["name"]
            with threading.Lock():
                update_dict(most_watched_studios, target, i)

def get_designated_file(type):

    global are_different

    designated_file = None

    with open(os.path.join(CACHE_DIR, f"tmp_watched_{type}s.json"), "w") as new_file:
        if type == "movie":
            new_file.write(json.dumps(trakt_request.get_watched_movies(), separators=(",", ":"), indent=4))
        elif type == "show":
            new_file.write(json.dumps(trakt_request.get_watched_shows(), separators=(",", ":"), indent=4))

    with open(os.path.join(CACHE_DIR, f"tmp_watched_{type}s.json")) as json_file:
        new_file = json.load(json_file)

    latest_file = None

    #if there is no history file, we create one
    if not os.path.isfile(os.path.join(CACHE_DIR, f"watched_{type}s.json")) or most_watched_actors == {} or most_watched_studios == {} or most_watched_directors == {}:
        designated_file = new_file
    else:
        with open(os.path.join(CACHE_DIR, f"watched_{type}s.json")) as json_file:
            latest_file = json.load(json_file)    

    #if there is history file, we compare it with the new one
    if not designated_file:
        designated_file = generate_json_diff(latest_file, new_file)
        are_different = designated_file != []

    return designated_file

# Check if the API key is valid
if len(TRAKT_API_KEY) != 64:
    print("Invalid Trakt API key, please check your trakt_request.py file")
    sys.exit()

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

trakt_request = TraktRequest(TRAKT_API_KEY, TRAKT_USERNAME, CACHE_DIR)

#try:
trakt_request.get_cached_data()

with open(os.path.join(RESULTS_DIR, "user_stats.json"), "w") as stats_file:
    stats_file.write(json.dumps(trakt_request.get_user_stats(), separators=(",", ":"), indent=4))   

watched_movies = get_designated_file("movie")

length = len(watched_movies)

widgets = [
    " [", progressbar.Timer(), "] ",
    progressbar.Bar(),
    "(", progressbar.Counter(), "/%s" % length, ") ",
]

if are_different or most_watched_actors == {} or most_watched_directors == {}:
    bar = progressbar.ProgressBar(maxval=length, redirect_stdout=True, widgets=widgets)

    index = 0
    launch_threads(get_crew, 6, length)

    bar.finish()

    if needs_update == "actors" or needs_update == "both":
        most_watched_actors = {k: v for k, v in sorted(most_watched_actors.items(), key=lambda item: item[1], reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_actors.json"), "w") as outfile:
            json.dump(most_watched_actors, outfile, indent=4)

    if needs_update == "directors" or needs_update == "both":
        most_watched_directors = {k: v for k, v in sorted(most_watched_directors.items(), key=lambda item: item[1], reverse=True)}
        with open(os.path.join(RESULTS_DIR, "most_watched_directors.json"), "w") as outfile:
            json.dump(most_watched_directors, outfile, indent=4)

if are_different or most_watched_studios == {}:
    bar = progressbar.ProgressBar(maxval=length, redirect_stdout=True, widgets=widgets)

    index = 0
    launch_threads(get_studios, 6, length)

    bar.finish()

    most_watched_studios = {k: v for k, v in sorted(most_watched_studios.items(), key=lambda item: item[1], reverse=True)}
    with open(os.path.join(RESULTS_DIR, "most_watched_studios.json"), "w") as outfile:
        json.dump(most_watched_studios, outfile, indent=4)

os.rename(os.path.join(CACHE_DIR, "tmp_watched_movies.json"), os.path.join(CACHE_DIR, "watched_movies.json"))