from flask import render_template, url_for, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from collections import defaultdict

from spotitag.forms import QueryForm, EditForm, LoginForm, RegistrationForm
from spotitag import app, db
from spotitag.models import User, Album, Artist, get_spotify_client


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
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
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

    spotify_client = get_spotify_client()

    search = spotify_client.search(q=f'artist:{artist}', type='artist')
    artists = [
        Artist.get(item['id'])
        for item in search['artists']['items']
    ]

    return render_template('result.html', artists=artists)


@app.route('/tags')
@login_required
def show_tags():
    tags = defaultdict(lambda: defaultdict(list))

    for tag, artists in current_user.artists_by_tag().items():
        for artist in artists:
            tags[tag]['artists'].append(artist)

    for tag, albums in current_user.albums_by_tag().items():
        for album in albums:
            tags[tag]['albums'].append(album)


    return render_template('tags.html', tags=tags)


@app.route('/editartist/<artist_id>', methods=['GET', 'POST'])
@login_required
def edit_artist(artist_id):
    artist = Artist.get(artist_id)
    
    tags = current_user.tags_by_artist()[artist]

    form = EditForm()
    if form.validate_on_submit():
        new_tags = [
            tag.strip()
            for tag in form.new_tags.data.split(';')
            if tag != ''
        ]
        current_user.set_artist_tags(new_tags, artist_id)

        return redirect(url_for('show_tags'))

    form.new_tags.data = ';'.join(tag.label for tag in tags)

    return render_template('edit.html', form=form, item=artist)


@app.route('/editalbum/<album_id>', methods=['GET', 'POST'])
@login_required
def edit_album(album_id):
    album = Album.get(album_id)

    tags = current_user.tags_by_album()[album]

    form = EditForm()
    if form.validate_on_submit():
        new_tags = [
            tag.strip()
            for tag in form.new_tags.data.split(';')
            if tag != ''
        ]
        current_user.set_album_tags(new_tags, album_id)

        return redirect(url_for('show_tags'))

    form.new_tags.data = ';'.join(tag.label for tag in tags)

    return render_template('edit.html', form=form, item=album)
