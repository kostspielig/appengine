
from google.appengine.ext import db


class Art(db.Model):
    """Models a user entry with an author, comment, avatar, and date."""
    author = db.StringProperty(required=True)
    comment = db.StringProperty(multiline=True)
    avatar = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
        
    def render(self):
        self._render_text = self.content #.replace('\n', '<br>')

