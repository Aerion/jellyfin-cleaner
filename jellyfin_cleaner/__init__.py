__version__ = "0.1.0"

import argparse
from typing import Iterable
import urllib.parse
import requests
import logging


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description="Clean Jellyfin items to delete")
parser.add_argument(
    "--jellyfin-base-url", type=str, help="Jellyfin base url", required=True
)
parser.add_argument(
    "--jellyfin-api-key", type=str, help="Jellyfin api key", required=True
)
parser.add_argument(
    "--jellyfin-user-id", type=str, help="Jellyfin user id", required=True
)
parser.add_argument(
    "--jellyfin-collection-id",
    type=str,
    help="Jellyfin collection id to clean",
    required=True,
)
parser.add_argument(
    "--radarr-base-url", type=str, help="Radarr base url", required=True
)
parser.add_argument("--radarr-api-key", type=str, help="Radarr api key", required=True)
parser.add_argument("-n", "--dry-run", help="Dry-run", action="store_true")
args = parser.parse_args()

JELLYFIN_BASE_URL = args.jellyfin_base_url
JELLYFIN_HEADERS = {
    "X-MediaBrowser-Token": args.jellyfin_api_key,
    "Content-Type": "application/json",
}
RADARR_BASE_URL = args.radarr_base_url
RADARR_API_KEY = args.radarr_api_key


def get_jellyfin_items_to_clean(user_id: str, parent_id: str):
    resp = requests.get(
        urllib.parse.urljoin(JELLYFIN_BASE_URL, f"Users/{user_id}/Items"),
        headers=JELLYFIN_HEADERS,
        params={
            "fields": ["ProviderIds"],
            "parentId": parent_id,
        },
    )
    resp.raise_for_status()
    return resp.json()["Items"]


def delete_radarr_movies_by_imdbids(imdb_ids: Iterable[int]):
    resp = requests.get(
        urllib.parse.urljoin(RADARR_BASE_URL, "api/v3/movie"),
        params={"apiKey": RADARR_API_KEY},
    )
    resp.raise_for_status()
    radarr_known_movies = resp.json()

    radarr_movies_to_delete = [
        radarr_item
        for radarr_item in radarr_known_movies
        if radarr_item["imdbId"] in imdb_ids
    ]

    if args.dry_run:
        logging.info(
            f"Dry-run - Would have removed from Radarr the movies {[radarr_item['title'] for radarr_item in radarr_movies_to_delete]}"
        )
        return

    resp = requests.delete(
        urllib.parse.urljoin(RADARR_BASE_URL, "api/v3/movie/editor"),
        json={
            "movieIds": [radarr_item["id"] for radarr_item in radarr_movies_to_delete],
            "deleteFiles": True,
        },
        params={"apiKey": RADARR_API_KEY},
    )
    resp.raise_for_status()

    for radarr_movie in radarr_movies_to_delete:
        logging.debug(
            f"Removed {radarr_movie['title']} (id={radarr_movie['id']}) from {radarr_movie['path']}"
        )

    logging.info(f"Removed {len(radarr_movies_to_delete)} movies from Radarr")


jellyfin_items_to_clean = get_jellyfin_items_to_clean(
    args.jellyfin_user_id, args.jellyfin_collection_id
)

if len(jellyfin_items_to_clean) == 0:
    logging.info("No Jellyfin items to clean, exiting")
    exit(0)

logging.info(f"{len(jellyfin_items_to_clean)} jellyfin items to clean")

movies_imdb_ids_to_clean = set(
    jellyfin_item["ProviderIds"]["Imdb"]
    for jellyfin_item in jellyfin_items_to_clean
    if jellyfin_item["Type"] == "Movie"
    and jellyfin_item["ProviderIds"]["Imdb"].startswith("tt")
)

logging.info(f"{len(movies_imdb_ids_to_clean)} jellyfin movie items to clean")
if len(movies_imdb_ids_to_clean) > 0:
    delete_radarr_movies_by_imdbids(movies_imdb_ids_to_clean)

requests.post(
    urllib.parse.urljoin(JELLYFIN_BASE_URL, f"Library/Refresh"),
    headers=JELLYFIN_HEADERS,
).raise_for_status()
logging.info(f"Clean-up done")
