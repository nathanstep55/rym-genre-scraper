import sys
from csv import DictWriter
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import locale
from locale import atoi, atof  # just in case, this makes sure that even if , and . are used in different locales this will convert it correctly

locale.setlocale(locale.LC_ALL, 'en_US.UTF8')

# CSV structure:
fields = ["artist", "album", "spotify id", "apple music id", "bandcamp link", "primary genres", "secondary genres", "descriptors", 
          "release date", "rym link", "rym album id", "rym artist id", "fixed tempo", "rym rating", "number of ratings"]

albums = []
max_albums = 40  # 40 per page

csv_fn = "albums.csv"

def get_url_end(url):
    return urlparse(url).path.rsplit('/', 1)[-1]
    
def sanitize(s):
    return s.strip().replace('\n', '').replace('\r', '') if isinstance(s, str) else s

def main():
    p = Path('html/')
    for fn in tqdm(p.glob('*.html'), total=1771):
        with open(fn) as infile:
            soup = BeautifulSoup(infile, 'html.parser')
        # print(fn)
        
        results = soup.find('div', class_='chart_results')
        i = 1
        while i <= max_albums:
            # search for 
            entry = soup.find(id=f'pos{i}')
            if entry is None:
                break
            
            album_ = entry.find('div', class_='topcharts_item_title')
            rym_album_id = int(album_.a['title'].strip()[6:].replace(']', '')) # [Album290]
            rym_link = urljoin("https://rateyourmusic.com", album_.a['href'])
            album = album_.get_text().strip()
            
            artist_ = entry.find('div', class_='topcharts_item_artist')
            rym_artist_id = int(artist_.a['title'].strip()[7:].replace(']', '')) # [Artist101]
            artist = artist_.get_text().strip()
            
            release_date_ = entry.find('div', class_='topcharts_item_releasedate')
            release_date_str = ''.join(release_date_.find_all(text=True, recursive=False)).strip()
            # pure pain
            try:
                release_timestamp = datetime.strptime(release_date_str, "%d %B %Y")
            except:
                try:
                    release_timestamp = datetime.strptime(release_date_str, "%B %Y")
                except:
                    try:
                        release_timestamp = datetime.strptime(release_date_str, "%Y")
                    except:
                        release_timestamp = None
            release_date = release_timestamp.strftime("%Y-%m-%d") if release_timestamp is not None else ''
            
            rym_rating_ = entry.find('span', class_='topcharts_avg_rating_stat')
            try:
                rym_rating = atof(rym_rating_.get_text())
            except:
                # no rating
                rym_rating_ = ''
            
            number_of_ratings_ = entry.find('span', class_='topcharts_ratings_stat')
            try:
                number_of_ratings = atoi(number_of_ratings_.get_text())
            except:
                # no ratings
                rym_rating_ = ''
            
            primary_genres_ = entry.find('div', class_='topcharts_item_genres_container')
            primary_genres = primary_genres_.get_text().strip()
            
            secondary_genres_ = entry.find('div', class_='topcharts_item_secondarygenres_container')
            secondary_genres = secondary_genres_.get_text().strip()
            
            descriptors_ = entry.find('div', class_='topcharts_item_descriptors_container')
            descriptors = descriptors_.get_text().strip()
            
            apple_music_id = ''
            apple_music_id_ = entry.find('a', class_='ui_media_link_btn_applemusic')
            if apple_music_id_ is not None:
                try:
                    apple_music_id = int(get_url_end(apple_music_id_['href']))
                except:
                    # item is not available in US store, most likely
                    pass
            
            spotify_id = ''
            spotify_id_ = entry.find('a', class_='ui_media_link_btn_spotify')
            if spotify_id_ is not None:
                spotify_id = get_url_end(spotify_id_['href'])
            
            bandcamp_link = ''
            bandcamp_link_ = entry.find('a', class_='ui_media_link_btn_bandcamp')
            if bandcamp_link_ is not None:
                bandcamp_link = bandcamp_link_['href'].strip()
                                
            fixed_tempo = ''  # release_date > '1990-01-01'
            
            
            album = {
                'artist': artist,
                'album': album,
                'spotify id': spotify_id,
                'apple music id': apple_music_id,
                'bandcamp link': bandcamp_link,
                'primary genres': primary_genres,
                'secondary genres': secondary_genres,
                'descriptors': descriptors,
                'release date': release_date,
                'rym link': rym_link,
                'rym album id': rym_album_id,
                'rym artist id': rym_artist_id,
                'fixed tempo': fixed_tempo,
                'rym rating': rym_rating,
                'number of ratings': number_of_ratings
            }
            
            for key in album:
                album[key] = sanitize(album[key])
            
            albums.append(album)
            
            
            i += 1
        
    with open(csv_fn, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fields)
        
        writer.writeheader()
        writer.writerows(albums)
        
            
if __name__ == '__main__':
    main()