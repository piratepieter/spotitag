import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cacheout.memoization import memoize
from cacheout.fifo import FIFOCache
from flask import url_for


def _fetch_details_albums(spotify_ids):
    if len(spotify_ids) == 0:
        return {}
    
    spotify_client = SpotifyHandler().client()
    results = spotify_client.albums(spotify_ids)

    details = {
        spotify_id: {
            'id': result['id'],
            'name': result['name'],
            'url': result['external_urls']['spotify'],
            'edit': url_for('edit_album', album_id=spotify_id),
            'image': _smallest_image(result['images']),
        }
        for spotify_id, result in zip(spotify_ids, results['albums'])
    }

    return details


class SpotifyHandler:

    __album_cache = FIFOCache(maxsize=512, ttl=3600)

    def detailsForAlbums(self, spotify_ids):

        album_details = self.__album_cache.get_many(spotify_ids)
       
        albums_to_fetch = set(spotify_ids) - set(album_details.keys())
        fetched_details = _fetch_details_albums(albums_to_fetch)

        album_details.update(fetched_details)
        self.__album_cache.set_many(fetched_details)
       
        return album_details

    def detailsForAlbum(self, spotify_id):
        details = self.detailsForAlbums([spotify_id])
        return details[spotify_id]

    def client(self):
        return spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    def searchArtistSpotifyIDs(self, artist_query):
        search = self.client().search(q=f'artist:{artist_query}', type='artist')
        artist_spotify_ids = [item['id'] for item in search['artists']['items']]

        return artist_spotify_ids

    def artistAlbums(self, spotify_id):
        album_result = self.client().artist_albums(spotify_id, album_type='album')
        albums = [album['id'] for album in album_result['items']]
        return albums


def _smallest_image(images):
    if len(images) == 0:
        return url_for('static', filename='unknown.png')

    return min(images, key=lambda r: r['width'])['url']


@memoize(maxsize=512, ttl=3600)
def _get_artist_details(spotify_id):
    spotify_handler = SpotifyHandler()
    spotify_client = spotify_handler.client()
    result = spotify_client.artist(spotify_id)

    artist_details = {
        'id': spotify_id,
        'url': result['external_urls']['spotify'],
        'name': result['name'],
        'edit': url_for('edit_artist', artist_id=spotify_id),
        'image': _smallest_image(result['images']),
    }

    return artist_details
