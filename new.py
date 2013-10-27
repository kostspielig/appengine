import webapp2
import hashlib
import cgi
import re
import jinja2
import os
import hmac
import random
import string
import logging

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import images

template_dir = os.path.join(os.path.dirname(__file__))
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

post =  000;
SECRET = 'mmm';

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)
jinja_env.filters['datetimeformat'] = datetimeformat

def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return '%s|%s' %(s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt():
    return ''.join(random.sample(string.letters, 5))

def make_pw_hash(name, pw):
    salt = make_salt()
    return hashlib.sha256(name + pw + salt).hexdigest() + ','+ salt

def valid_pw(name, pw, h):
    hp = h.split(',')
    if hp[0] == hashlib.sha256(name + pw + hp[1]).hexdigest():
        return True
    else:
        return False
    
class Art(db.Model):
    """Models a user entry with an author, comment, avatar, and date."""
    author = db.StringProperty(required=True)
    comment = db.StringProperty(multiline=True)
    avatar = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
        
    def render(self):
        self._render_text = self.content #.replace('\n', '<br>')


class MainPage2(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
def all_arts(update = False):
    key = 'all'
    arts = memcache.get(key)
    if arts is None or update:
        arts = Art.all().order('-date')
        arts = list(arts)
        memcache.set(key,arts)
    return arts

class All(Handler):
    def get(self):
        self.render_front()
        
    def render_front(self):
        arts = all_arts()
        noinfo = 1
        self.render("index.html", arts = arts, noinfo = noinfo)

def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)
    if arts is None or update:
        logging.error("DB QUERY")
        arts = Art.all().order('-date').fetch(limit=3)
        arts = list(arts)
        memcache.set(key, arts)
    else:
        logging.error('get cached copy')
    return arts


class MainPage(Handler):
    def render_front(self):
        arts = top_arts()
        for art in arts:
            art.date = art.date
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            user = ""
            
        self.render("index.html", arts = arts, url_linktext = url_linktext, url =url, user=user)

    def get(self):
        self.render_front()

class Carrasco(Handler):
    def get(self):
        self.render("carrasco.html")

class NotFound(Handler):
	def get(self):
		self.render("404.html")		

class Cookie(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits_cookie = self.request.cookies.get('visits','0')
        visits = 0
        if visits_cookie:
            visits_cookie = check_secure_val(visits_cookie)
            if visits_cookie:
                visits = int(visits_cookie)

        visits += 1
        visits_new = make_secure_val(str(visits))

        self.response.headers.add_header('Set-Cookie', 'visits=%s' %visits_new)
        self.write("You have been here %s times" % visits)

class NewPost(Handler):
    def render_front(self, author="", comment="", error = ""):
        self.render("newpost.html", author = author, comment = comment, error = error )
        
    def get(self):
        self.render_front()

    def post(self):
        #if users.get_current_user():
        #    author = users.get_current_user().nickname()
        #else:
        author = self.request.get("author")
        comment = cgi.escape(self.request.get("comment"))
        img = self.request.get("avatar")

        logging.error("comment scaped?")
        
        if author and comment and img:
            #avatar = images.Image(img)
            if images.Image(img).width > 800:
                img = images.resize(img, 800)
                
            avatar = db.Blob(img)
            a = Art(author=author, comment=comment, avatar=avatar)
            a.put()
            all_arts(True)
            top_arts(True)
            
            self.redirect("/blog/%s" % str(a.key().id()))
        else:
            error = "We need all the params to continue"
            self.render_front(author, comment, error)

class PostPage(Handler):
    def get(self, post_id):
        key =  db.Key.from_path('Art', int(post_id))
        post = db.get(key)

        if not post:
                self.redirect("/notAllowed")
                #self.error(404)
                return
        
        self.render("post.html", post =  post)

class Image(webapp2.RequestHandler):
    def get(self):
        art = db.get(self.request.get('img_id'))
        if art.avatar:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(art.avatar)
        else:
                self.response.out.write("No image")
          
app = webapp2.WSGIApplication([('/blog/?', MainPage),
                              ('/blog/newpost/?', NewPost),
                              ('/blog/all/?', All),
                               ('/blog/([0-9]+)', PostPage),
                               ('/', MainPage),
                               ('/img', Image),
							   ('/.*', NotFound)],
                              debug=True)

