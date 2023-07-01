import datetime
import os
import sys
import subprocess
import argparse
import json
import progressbar
import threading
from dotenv import load_dotenv

from trakt_request import TraktRequest

load_dotenv()
# We load the necessary infos from the env file
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME") if os.getenv("TRAKT_USERNAME") else ""
BACKUP_ROOT_PATH = os.getenv("BACKUP_ROOT_PATH") if os.getenv("BACKUP_ROOT_PATH") else ""
TRAKT_URL = os.getenv("TRAKT_URL") if os.getenv("TRAKT_URL") else "https://api.trakt.tv/users"
CACHE_DIR = "cache"

most_watched_actors = {}
over_rate_movies = []

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

def get_crew_thread(start, end):
    global most_watched_actors
    global index
    global bar
    global over_rate_movies

    for movie in watched_movies[start:end]:
        with threading.Lock():
            bar.update(index)
            index += 1
        crew = trakt_request.get_crew(movie["movie"]["ids"]["trakt"], "movies")
        if not isinstance(crew, dict):
            over_rate_movies.append(movie["movie"]["ids"]["trakt"])
        for actor in crew["cast"]:
            if actor["person"]["name"] in most_watched_actors:
                with threading.Lock():
                    most_watched_actors[actor["person"]["name"]] += 1
            else:
                with threading.Lock():
                    most_watched_actors[actor["person"]["name"]] = 1

# Check if the API key is valid
if len(TRAKT_API_KEY) != 64:
    print("Invalid Trakt API key, please check your trakt_request.py file")
    sys.exit()

argparser = argparse.ArgumentParser(description="Backup your Trakt data")
argparser.add_argument("-i", "--interactive", action="store_true")
argparser.add_argument("-u", "--username", action="store", help="Your Trakt username")
args = argparser.parse_args()

if args.interactive:
    # -Y or --yes to save files in the current working directory (optional)
    argparser.add_argument(
        "-Y", "--yes", action="store_true", help="Save files in the current working directory", required=False
    )
    # Positional argument for the username (optional)
    argparser.add_argument("username", nargs="?", help="Your Trakt username")
    args = argparser.parse_args()

    # Ask the user if they want to save the files in the current working directory
    if not args.yes:
        folder = input(
            f"Save files here (shell current working directory) ? [Y/n]\n(files will otherwise be saved in {os.path.expanduser('~')}): "
        )
    else:
        folder = "Y"

    if folder.upper() == "Y":
        root = os.getcwd()
        BACKUP_ROOT_PATH = os.path.join(root, "trakt_backup")
    else:
        root = os.path.expanduser("~")
        BACKUP_ROOT_PATH = os.path.join(root, "trakt_backup")
    if args.username:
        TRAKT_USERNAME = args.username
    else:
        TRAKT_USERNAME = input("Enter your Trakt username: ")
else:
    if args.username:
        TRAKT_USERNAME = args.username


print(f"Files will be saved in: {BACKUP_ROOT_PATH}")

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

trakt_request = TraktRequest(TRAKT_API_KEY, TRAKT_USERNAME, CACHE_DIR)

#try:
#trakt_request.create_data_files()
trakt_request.get_cached_data()

watched_movies = json.loads(open("cache/watched_movies.json", "r").read())
length = len(watched_movies)
index = 0

widgets = [
    " [", progressbar.Timer(), "] ",
    progressbar.Bar(),
    "(", progressbar.Counter(), "/%s" % length, ") ",
]

bar = progressbar.ProgressBar(maxval=length, redirect_stdout=True, widgets=widgets)

threads = []

max_threads = 6
for i in range(0, max_threads):
    start = int(i * (length / max_threads) + 1)
    if i == 0:
        start = 0
    end = int((i + 1) * (length / max_threads))
    if end > length:
        end = length
    threads.append(threading.Thread(target=get_crew_thread, args=(start, end)))
    threads[i].start()

for i in range(0, max_threads):
    threads[i].join()

"Over rate movies: " + str(len(over_rate_movies))

for movie_id in over_rate_movies:
    crew = trakt_request.get_crew(movie_id, "movies")
    for actor in crew["cast"]:
        if actor["person"]["name"] in most_watched_actors:
            most_watched_actors[actor["person"]["name"]] += 1
        else:
            most_watched_actors[actor["person"]["name"]] = 1

most_watched_actors = {k: v for k, v in sorted(most_watched_actors.items(), key=lambda item: item[1], reverse=True)}
with open("cache/most_watched_actors.json", "w") as outfile:
    json.dump(most_watched_actors, outfile, indent=4)
    
'''except Exception as e:
    print(e)
    sys.exit()'''

#if args.interactive:
    #launch_file(new_backup_folder_name)
print("Done.")
