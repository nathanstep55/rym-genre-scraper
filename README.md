# rym-genre-scraper
rateyourmusic scraper for genre pages

I worked on a project in 2021-2022 to collect metadata and Spotify/Apple Music previews for each genre page on Rate Your Music.
This requires storing saved webpages in a folder called `html`, and to avoid ToS violations, you can manually download the genre pages in your browser using CTRL+S.

`chart_htmltocsv.py` will parse through genre album pages in the `html` folder and produce an `albums.csv`.
`albumtotracks.py` will take an album from `albums.csv` and add it to `tracks.csv`, as well as store the preview in a folder `audio_samples`.

Library requirements include bs4, Spotipy, TQDM, xxhash.
