import spotipy, requests
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
from csv import DictReader, DictWriter
from pathlib import Path
from os.path import isfile
import signal, sys, atexit
import xxhash

# spotify API key!
CLIENT_ID = PUT YOUR CLIENT ID HERE
CLIENT_SECRET = PUT YOUR CLIENT SECRET HERE

albums_fn = "albums.csv"
tracks_fn = "tracks.csv"

samples_dir = Path("audio_samples/")

interrupted = False

fields = ["id", "artist", "title", "length", "spotify track id", "spotify album id", "apple music track id", "apple music album id",
          "bandcamp album link", "primary genres", "secondary genres", "descriptors", "release date", "preview url", "preview filename",
          "rym album id", "rym artist id", "fixed tempo", "rym album rating", "number of album ratings"]

tracks = []
completed = set()

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def save_csv():
    with open(tracks_fn, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(tracks)
    print("Saved.")

def main():
    global tracks, completed, interrupted
    with open(albums_fn, newline='') as csvfile:
        reader = DictReader(csvfile)
        albums = [album for album in reader]
        
    if isfile(tracks_fn):
        print("Existing tracks.csv found, loading data...")
        with open(tracks_fn, newline='') as csvfile:
            reader = DictReader(csvfile)
            tracks = [track for track in reader]
            completed = {int(track['rym album id']) for track in tracks}

    for album in tqdm(albums):
        if int(album['rym album id']) in completed:
            # print(f"Already parsed album {album['rym album id']}, skipping...")
            continue
        spotify_id = album.get('spotify id')
        apple_music_id = album.get('apple music id')
        
        if spotify_id not in (None, ''):
            try:
                results = sp.album_tracks(album['spotify id'])
            except:
                print(f"Error: could not retrieve {album['album']} with ID {album['spotify id']}")
                break
                
            for track in results['items']:
                track_dict = {
                    'id': xxhash.xxh64(f"{album['artist']}{track['duration_ms']}{track['name']}").hexdigest(),
                    'artist': album['artist'],
                    'title': track['name'],
                    'length': track['duration_ms'],
                    'spotify track id': track['id'],
                    'spotify album id': spotify_id,
                    'apple music track id': '',
                    'apple music album id': apple_music_id,
                    'bandcamp album link': album['bandcamp link'],
                    # genres and descriptors should ideally be determined per track and not per album, but this will have to wait until RYM opens an API or I get permission to scrape genres.
                    'primary genres': album['primary genres'],
                    'secondary genres': album['secondary genres'],
                    'descriptors': album['descriptors'],
                    'release date': album['release date'],
                    'preview url': track['preview_url'],
                    'rym album id': album['rym album id'],
                    'rym artist id': album['rym artist id'],
                    'fixed tempo': '',
                    'rym album rating': album['rym rating'],
                    'number of album ratings': album['number of ratings']
                }
                
                track_dict['preview filename'] = samples_dir/f"{track_dict['id']}_i_{track['id']}.mp3"
                
                tracks.append(track_dict)
                
                if not isfile(track_dict['preview filename']) and track_dict['preview url'] is not None:
                    r = requests.get(track_dict['preview url'], allow_redirects=True)
                    content_type = r.headers.get('content-type', None)
                    
                    if content_type is not None and 'text' not in content_type.lower() and 'html' not in content_type.lower():
                        with open(track_dict['preview filename'], 'wb') as wf:
                            wf.write(r.content)
                
        elif apple_music_id not in (None, ''):
            response = requests.get(f"https://itunes.apple.com/lookup?id={apple_music_id}&entity=song")
            if response.status_code == 200:
                for track in response.json()['results']:
                    if track['wrapperType'] != 'track':
                        continue
                    track_dict = {
                        'id': xxhash.xxh64(f"{album['artist']}{track['trackTimeMillis']}{track['trackName']}").hexdigest(),
                        'artist': album['artist'],
                        'title': track['trackName'],
                        'length': track['trackTimeMillis'],
                        'spotify track id': '',
                        'spotify album id': spotify_id,
                        'apple music track id': track['trackId'],
                        'apple music album id': apple_music_id,
                        'bandcamp album link': album['bandcamp link'],
                        'primary genres': album['primary genres'],
                        'secondary genres': album['secondary genres'],
                        'descriptors': album['descriptors'],
                        'release date': album['release date'],
                        'preview url': track.get('previewUrl'),
                        'rym album id': album['rym album id'],
                        'rym artist id': album['rym artist id'],
                        'fixed tempo': '',
                        'rym album rating': album['rym rating'],
                        'number of album ratings': album['number of ratings']
                    }
                    
                    track_dict['preview filename'] = samples_dir/f"{track_dict['id']}_i_{track['trackId']}.m4a"
                    
                    tracks.append(track_dict)
                    
                    if not isfile(track_dict['preview filename']) and track_dict['preview url'] is not None:
                        r = requests.get(track_dict['preview url'], allow_redirects=True)
                        content_type = r.headers.get('content-type', None)
                        
                        if content_type is not None and 'text' not in content_type.lower() and 'html' not in content_type.lower():
                            with open(track_dict['preview filename'], 'wb') as wf:
                                wf.write(r.content)
            else:
                print(f'error {response.status_code}')
                
        completed.add(int(album['rym album id']))
        if interrupted:
            save_csv()
            sys.exit()
                
    save_csv()
        
    finished = True

def sighandle(signum, frame):
    print('Signal received, ending after iteration finishes...')
    global interrupted
    interrupted = True

signal.signal(signal.SIGTERM, sighandle)
signal.signal(signal.SIGINT, sighandle)
                        
if __name__ == '__main__':
    main()