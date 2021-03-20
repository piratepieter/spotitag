from flask_login import UserMixin
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from collections import defaultdict

from spotitag import db, login
from spotitag.spotify import SpotifyHandler, _get_artist_details


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tags = db.relationship('Tag', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username

    def set_artist_tags(self, tag_labels, artist_spotify_id):
        tags = Tag.get_tags(labels=tag_labels, user=self)
        artist = Artist.get(artist_spotify_id)

        for tag in tags:
            if artist not in tag.artists.all():
                tag.artists.append(artist)

        db.session.commit()

        all_artist_tags = set(self.tags_by_artist()[artist])
        tags_to_remove = all_artist_tags - set(tags)
        for tag in tags_to_remove:
            tag.artists.remove(artist)

        db.session.commit()

    def artists_by_tag(self):
        tag_artists = {
            tag: list(tag.artists.all())
            for tag in self.tags.all()
        }

        return tag_artists

    def tags_by_artist(self):
        artist_tags = defaultdict(list)
        for tag, artists in self.artists_by_tag().items():
            for artist in artists:
                artist_tags[artist].append(tag)
        return artist_tags

    def set_album_tags(self, tag_labels, album_spotify_id):
        tags = Tag.get_tags(labels=tag_labels, user=self)
        album = Album.get(album_spotify_id)

        for tag in tags:
            if album not in tag.albums.all():
                tag.albums.append(album)

        db.session.commit()

        all_album_tags = set(self.tags_by_album()[album])
        tags_to_remove = all_album_tags - set(tags)
        for tag in tags_to_remove:
            tag.albums.remove(album)

        db.session.commit()

    def albums_by_tag(self):
        tag_albums = {
            tag: list(tag.albums.all())
            for tag in self.tags.all()
        }

        return tag_albums

    def tags_by_album(self):
        album_tags = defaultdict(list)
        for tag, albums in self.albums_by_tag().items():
            for album in albums:
                album_tags[album].append(tag)
        return album_tags


artist_tags = db.Table('artist_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id')),
    db.UniqueConstraint('tag_id', 'artist_id', name='unique_artist_tag'),
)


album_tags = db.Table('album_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('album_id', db.Integer, db.ForeignKey('album.id')),
    db.UniqueConstraint('tag_id', 'album_id', name='unique_album_tag'),
)


class Tag(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    artists = db.relationship(
        'Artist',
        secondary=artist_tags,
        backref=db.backref('tags', lazy='dynamic'),
        lazy='dynamic'
    )

    albums = db.relationship(
        'Album',
        secondary=album_tags,
        backref=db.backref('tags', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return self.label

    def __normalize(self, label):
        return label.lower()

    @classmethod
    def get_tags(cls, labels, user):
        existing_tags = user.tags.all()
        existing_labels = [tag.label for tag in existing_tags]

        tags = [tag for tag in existing_tags if tag.label in labels]

        new_labels = set(labels) - set(existing_labels)
        for label in new_labels:
            tag = cls(label=label, user=user)
            db.session.add(tag)
            tags.append(tag)
        db.session.commit()

        return tags


class Artist(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(32), index=True, unique=True)

    @classmethod
    def get(cls, spotify_id):
        try:
            db.session.add(cls(spotify_id=spotify_id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        return cls.query.filter(cls.spotify_id == spotify_id)[0]

    @classmethod
    def search(cls, artist_query):
        handler = SpotifyHandler()
        artist_ids = handler.searchArtistSpotifyIDs(artist_query)
        artists = [Artist.get(artist_id) for artist_id in artist_ids]

        return artists

    def name(self):
        return self.__details()['name']

    def spotifyURL(self):
        return self.__details()['url']

    def editURL(self):
        return url_for('edit_artist', artist_id=self.spotify_id)

    def albums(self):
        albums = [
            Album.get(album_id) for album_id in self.__details()['albums']
        ]
        return albums

    def image(self):
        return self.__details()['image']

    def __details(self):
        return _get_artist_details(self.spotify_id)


class Album(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(32), index=True, unique=True)

    @classmethod
    def get(cls, spotify_id):
        try:
            db.session.add(cls(spotify_id=spotify_id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        return cls.query.filter(cls.spotify_id == spotify_id)[0]

    def name(self):
        return self.__details()['name']

    def spotifyURL(self):
        return self.__details()['url']

    def editURL(self):
        return url_for('edit_album', album_id=self.spotify_id),

    def image(self):
        return self.__details()['image']

    def __details(self):
        return SpotifyHandler().detailsForAlbum(self.spotify_id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
