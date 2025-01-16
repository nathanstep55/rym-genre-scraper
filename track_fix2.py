import spotipy, requests
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
from csv import DictReader, DictWriter
from pathlib import Path
from os.path import isfile
import signal, sys, atexit
import xxhash

albums_fn = "albums.csv"
tracks_fn = "tracks.csv"
new_tracks_fn = "tracksfixed.csv"

samples_dir = Path("audio_samples/")

interrupted = False

fields = ["id", "artist", "title", "length", "spotify track id", "spotify album id", "apple music track id", "apple music album id",
          "bandcamp album link", "primary genres", "secondary genres", "descriptors", "release date", "preview url", "preview filename",
          "rym album id", "rym artist id", "fixed tempo", "rym album rating", "number of album ratings"]

tracks = []

def save_csv():
    with open(new_tracks_fn, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(tracks)
    print("Saved.")

def main():
    global tracks, completed, interrupted

    print("Loading tracks.csv...")
    with open(tracks_fn, newline='') as csvfile:
        reader = DictReader(csvfile)
        tracks = [track for track in reader]

    for track in tqdm(tracks):
        descriptors = [descriptor.strip() for descriptor in track['descriptors'].split(',')]
        
        if '...' in descriptors:
            descriptors.remove('...')
            
        track['descriptors'] = ', '.join(descriptors)
        
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