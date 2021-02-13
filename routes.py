from flask import render_template, url_for, redirect, flash
from flask_login import current_user, login_user, logout_user
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from forms import QueryForm, EditForm, LoginForm, RegistrationForm
from flask_app import app, db
from models import User


from collections import defaultdict
TAG_TABLE = defaultdict(list)
TAG_TABLE['good'] = ['4Z8W4fKeB5YxbusRsdQVPb', '1uRxRKC7d9zwYGSRflTKDR']
TAG_TABLE['bad'] = ['3r2qdoM2Ryp8aBb3S3qIG1']


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = QueryForm()
    if form.validate_on_submit():
        return redirect(url_for('search_result', artist=form.artist_query.data))
    return render_template('index.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


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