import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cacheout.memoization import memoize
from flask import url_for


class SpotifyHandler:

    def client(self):
        return spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    def searchArtistSpotifyIDs(self, artist_query):
        search = self.client().search(q=f'artist:{artist_query}', type='artist')
        artist_spotify_ids = [item['id'] for item in search['artists']['items']]

        return artist_spotify_ids


def _smallest_image(images):
    if len(images) == 0:
        return url_for('static', filename='unknown.png')

    return min(images, key=lambda r: r['width'])['url']


@memoize(maxsize=512, ttl=3600)
def _get_artist_details(spotify_id):
    spotify_client = SpotifyHandler().client()
    result = spotify_client.artist(spotify_id)
    album_result = spotify_client.artist_albums(spotify_id, album_type='album')

    artist_details = {
        'id': spotify_id,
        'url': result['external_urls']['spotify'],
        'name': result['name'],
        'edit': url_for('edit_artist', artist_id=spotify_id),
        'image': _smallest_image(result['images']),
        'albums':
            [
                album['id'] for album in album_result['items']
            ],
    }
    return artist_details


@memoize(maxsize=512, ttl=3600)
def _get_album_details(spotify_id):
    spotify_client = SpotifyHandler().client()
    result = spotify_client.album(spotify_id)
    album_details = {
        'id': result['id'],
        'name': result['name'],
        'url': result['external_urls']['spotify'],
        'edit': url_for('edit_album', album_id=spotify_id),
        'image': _smallest_image(result['images']),
    }

    return album_details