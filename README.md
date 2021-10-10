# Context

This script will delete all files and folder for media items present in a Jellyfin collection.

## Usefulness

If all of the following is true, this script could be useful to you:

- You manage a [Jellyfin](https://jellyfin.org/) instance
- Your movies are managed in [Radarr](https://radarr.video/)
- You'd like to clean up your Jellyfin movies cleanly (by using Radarr)

## Personal use-case

A collection called "Items to delete" is present on my Jellyfin instance.
A user adds an item to this collection only when this item must be removed (they requested it and they'll never want to watch it again).

As those movies are managed in Radarr, I'd like to remove them from there, instead of Jellyfin, where some files after removal could remain.

# Usage

```sh
python jellyfin_cleaner/__init__.py --jellyfin-base-url https://jellyfin.example.org/jellyfin/ --jellyfin-api-key xxxxx --jellyfin-user-id yyyyy --jellyfin-collection-id zzzz --radarr-base-url https://radarr.example.org/ --radarr-api-key aaaaa
```

```
INFO:root:1 jellyfin items to clean
INFO:root:1 jellyfin movie items to clean
INFO:root:Dry-run - Would have removed from Radarr the movies ['ZZZZZZZZZ']
INFO:root:Clean-up done
```

# To-do

* Removal from Sonarr