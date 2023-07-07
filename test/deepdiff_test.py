from deepdiff import DeepDiff
from deepdiff.helper import CannotCompare

from pprint import pprint

def compare_func(x, y, level=None):
    try:
        return x['id'] == y['id']
    except Exception:
        raise CannotCompare() from None

t1 = [
    {
        "plays":2,
        "last_watched_at":"2022-05-25T20:26:25.000Z",
        "last_updated_at":"2022-05-25T20:26:29.000Z",
        "movie":{
            "title":"Jurassic World",
            "year":2015,
            "ids":{
                "trakt":91374,
                "slug":"jurassic-world-2015",
                "imdb":"tt0369610",
                "tmdb":135397
            }
        }
    },
    {
        "plays":2,
        "last_watched_at":"2022-04-01T20:22:41.000Z",
        "last_updated_at":"2022-04-01T20:22:40.000Z",
        "movie":{
            "title":"Edge of Tomorrow",
            "year":2014,
            "ids":{
                "trakt":92230,
                "slug":"edge-of-tomorrow-2014",
                "imdb":"tt1631867",
                "tmdb":137113
            }
        }
    },
    {
        "plays":2,
        "last_watched_at":"2023-06-21T11:51:23.000Z",
        "last_updated_at":"2023-06-21T11:51:23.000Z",
        "movie":{
            "title":"Spider-Man: Into the Spider-Verse",
            "year":2018,
            "ids":{
                "trakt":205404,
                "slug":"spider-man-into-the-spider-verse-2018",
                "imdb":"tt4633694",
                "tmdb":324857
            }
        }
    },
]

t2 = [
    {
        "plays":2,
        "last_watched_at":"2022-05-25T20:26:25.000Z",
        "last_updated_at":"2022-05-25T20:26:29.000Z",
        "movie":{
            "title":"Jurassic World",
            "year":2015,
            "ids":{
                "trakt":91374,
                "slug":"jurassic-world-2015",
                "imdb":"tt0369610",
                "tmdb":135397
            }
        }
    },
    {
        "plays":2,
        "last_watched_at":"2023-06-21T11:51:23.000Z",
        "last_updated_at":"2023-06-21T11:51:23.000Z",
        "movie":{
            "title":"Spider-Man: Into the Spider-Verse",
            "year":2018,
            "ids":{
                "trakt":205404,
                "slug":"spider-man-into-the-spider-verse-2018",
                "imdb":"tt4633694",
                "tmdb":324857
            }
        }
    },
]

pprint(DeepDiff(t1, t2, ignore_order=True))