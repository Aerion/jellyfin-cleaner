__version__ = "0.1.0"

import argparse
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
args = parser.parse_args()

jellyfin_headers = {
    "X-MediaBrowser-Token": args.jellyfin_api_key,
    "Content-Type": "application/json",
}

jellyfin_items_to_clean = requests.get(
    urllib.parse.urljoin(
        args.jellyfin_base_url, f"Users/{args.jellyfin_user_id}/Items"
    ),
    headers=jellyfin_headers,
    params={
        "fields": ["ProviderIds"],
        "parentId": args.jellyfin_collection_id,
    },
).json()["Items"]

logging.info(f"{len(jellyfin_items_to_clean)} jellyfin items to clean")

if len(jellyfin_items_to_clean) == 0:
    exit(0)

movies_imdb_ids_to_clean = set(
    jellyfin_item["ProviderIds"]["Imdb"]
    for jellyfin_item in jellyfin_items_to_clean
    if jellyfin_item["Type"] == "Movie"
    and jellyfin_item["ProviderIds"]["Imdb"].startswith("tt")
)

radarr_known_movies = requests.get(
    urllib.parse.urljoin(args.radarr_base_url, "api/v3/movie"),
    params={"apiKey": args.radarr_api_key},
).json()

radarr_movies_to_delete = [
    radarr_item
    for radarr_item in radarr_known_movies
    if radarr_item["imdbId"] in movies_imdb_ids_to_clean
]

requests.delete(
    urllib.parse.urljoin(args.radarr_base_url, "api/v3/movie/editor"),
    json={
        "movieIds": [radarr_item["id"] for radarr_item in radarr_movies_to_delete],
        "deleteFiles": True,
    },
    params={"apiKey": args.radarr_api_key},
)

for radarr_movie in radarr_movies_to_delete:
    logging.debug(
        f"Removed {radarr_movie['title']} (id={radarr_movie['id']}) from {radarr_movie['path']}"
    )

logging.info(f"Removed {len(radarr_movies_to_delete)} movies from Radarr")

requests.post(
    urllib.parse.urljoin(args.jellyfin_base_url, f"Library/Refresh"),
    headers=jellyfin_headers,
)
