
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from collections import defaultdict
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from forms import QueryForm, EditForm
from config import Config

SECRET_KEY = 'omg'
TAG_TABLE = defaultdict(list)
TAG_TABLE['good'] = ['4Z8W4fKeB5YxbusRsdQVPb', '1uRxRKC7d9zwYGSRflTKDR']
TAG_TABLE['bad'] = ['3r2qdoM2Ryp8aBb3S3qIG1']


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

import models

@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    form = QueryForm()
    if form.validate_on_submit():
        return redirect(url_for('search_result', artist=form.artist_query.data))
    return render_template('index.html', form=form)

@app.route('/result/<artist>')
def search_result(artist):

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    search = spotify.search(q=f'artist:{artist}', type='artist')
    results = [
        fill_artist_details(item['id'])
        for item in search['artists']['items']
    ]

    return render_template('result.html', results=results)

def fill_artist_details(artist_id):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    result = spotify.artist(artist_id)

    artist_details = {
        'id': artist_id,
        'url': result['external_urls']['spotify'],
        'name': result['name'],
        'edit': url_for('edit_artist', artist_id=artist_id),
    }

    return artist_details

@app.route('/tags')
def show_tags():
    tags = {
        tag: [fill_artist_details(artist_id) for artist_id in artists]
        for tag, artists in TAG_TABLE.items()
    }
    return render_template('tags.html', tags=tags)

@app.route('/edit/<artist_id>', methods=['GET', 'POST'])
def edit_artist(artist_id):
    artist = fill_artist_details(artist_id)

    tags = [
        tag for tag, artists in TAG_TABLE.items()
        if artist_id in artists
    ]

    form = EditForm()
    if form.validate_on_submit():
        new_tags = [tag.strip() for tag in form.new_tags.data.split(';')]
        for tag in new_tags:
            if tag != '' and (tag not in TAG_TABLE or artist_id not in TAG_TABLE[tag]):
                TAG_TABLE[tag].append(artist_id)

        for old_tag in tags:
            if old_tag not in new_tags:
                TAG_TABLE[old_tag].remove(artist_id)

        return redirect(url_for('show_tags'))

    form.new_tags.data = ';'.join(tags)

    return render_template('edit.html', form=form, artist=artist)