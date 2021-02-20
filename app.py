from dotenv import load_dotenv
load_dotenv('.env')

from spotitag import app, db
from spotitag.models import Artist, Tag, User, Album

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Tag': Tag,
        'Artist': Artist,
        'Album': Album,
    }
