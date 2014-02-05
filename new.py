#
#  new.py : Main module for the url parsing of the application
#
# Written in 2014 by Maria Carrasco  <kostspielig@gmail.com>
#
#  *NOTE: move out all the handlers

import webapp2
import cgi
import jinja2
import os
import logging
import sys


from google.appengine.ext import db
from google.appengine.api import images

# Importing my libraries
import handlers
sys.path.append('./lib/')
import utils

sys.path.append('./lib/DB/')
import art
import appuser

#from google.appengine.api import memcache
#from instagram.client import InstagramAPI


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)
jinja_env.filters['datetimeformat'] = datetimeformat

post =  000;


class Handler(webapp2.RequestHandler):
    """Class representing a handler template."""
    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    def set_secure_cookie(self, name, val):
        cookie_val = utils.make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and utils.check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and appuser.User.by_id(int(uid))
        

class Signup(Handler):
    """Class representing the Signup page."""
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not utils.valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not utils.valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not utils.valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        """Overwrite this method to save user's data."""
        raise NotImplementedError


class Register(Signup):
    """Class that handles the storing of the new user."""
    def done(self):
        #make sure the user doesn't already exist
        u = appuser.User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = appuser.User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/')

class Login(Handler):
    """Login of an existing user"""
    
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = appuser.User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(Handler):
    """Logout of a active user. """
    def get(self):
        self.logout()
        self.redirect('/')

"""def all_arts(update = False):
    key = 'all'
    arts = memcache.get(key)
    if arts is None or update:
        arts = Art.all().order('-date')
        arts = list(arts)
        memcache.set(key,arts)
    return arts
"""
class All(Handler):
    """Class that load all the posts in the system """
    def get(self):
        self.render_front()
        
    def render_front(self):
        arts = art.Art.all().order('-date')
        # Memcache call
        noinfo = 1
        self.render("index.html", arts = arts, noinfo = noinfo)

class LoadAll(Handler):
    """Load all the posts of a page, minus an offset """
    def get(self, offset):
        self.render_front(offset)
        
    def render_front(self, offset):
        ioffset = int(offset)
        arts = art.Art.all().order('-date').run( offset=ioffset )
        # Memcache call
        noinfo = 1
        self.render("getPost.html", arts = arts, noinfo = noinfo)

    
"""
def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)
    if arts is None or update:
        logging.error("DB QUERY")
        arts = Art.all().order('-date').fetch(limit=3)
        arts = list(arts)
        memcache.set(key, arts)
    return arts
"""
class MainPage(Handler):
    """Class that handles the index page of the app."""
    
    def render_front(self, username = None):
        arts = art.Art.all().order('-date').fetch(limit=3)
        # Memcache call
        for artitem in arts:
            artitem.date = artitem.date

        if username:
            url = '/logout'
            url_linktext = 'logout'
        else:
            url = '/login'
            url_linktext = 'login'
            username = ''
            
        """user = users.get_current_user()
        
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            user = ""
        """
        self.render("index.html", arts = arts, url_linktext = url_linktext, url =url, username=username)

    def get(self):
        if self.user:
            self.render_front(self.user.name)
        else:
            self.render_front()

            
class NotFound(Handler):
	def get(self):
		self.render("404.html")

        
class Social(Handler):
    def get(self):
    # api = InstagramAPI(client_id='7f93273ebbbd4d82b2bc93df598f00c5', client_secret='156630aeb6ac46eb95daaecd84118021')
    #   popular_media = api.media_popular(count=5)
    #   for media in popular_media:
    #   print media.images['standard_resolution'].url
     
        self.render("social.html")
        
class Cookie(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits_cookie = self.request.cookies.get('visits','0')
        visits = 0
        if visits_cookie:
            visits_cookie = utils.check_secure_val(visits_cookie)
            if visits_cookie:
                visits = int(visits_cookie)

        visits += 1
        visits_new = utils.make_secure_val(str(visits))

        self.response.headers.add_header('Set-Cookie', 'visits=%s' %visits_new)
        self.write("You have been here %s times" % visits)

        
class NewPost(Handler):
    """New post form handler"""
    
    def render_front(self, author="", comment="", error = ""):
        self.render("newpost.html", author = author, comment = comment, error = error )
        
    def get(self):
        if self.user:
            self.render_front()
        else:
            self.redirect("/notAllowed")

    def post(self):
        #if users.get_current_user():
        #    author = users.get_current_user().nickname()
        #else:

        author = self.request.get("author")
        comment = cgi.escape(self.request.get("comment"), True)
        img = self.request.get("avatar")

        logging.error("comment scaped?")
        
        if author and comment and img:
            #avatar = images.Image(img)
            if images.Image(img).width > 800:
                img = images.resize(img, 800)
                
            avatar = db.Blob(img)
            a = art.Art(author=author, comment=comment, avatar=avatar)
            a.put()
            #all_arts(True)
            #top_arts(True)
            
            self.redirect("/blog/%s" % str(a.key().id()))
        else:
            error = "We need all the params to continue"
            self.render_front(author, comment, error)

class PostPage(Handler):
    """Display of a single given post."""
    def get(self, post_id):
        key =  db.Key.from_path('Art', int(post_id))
        post = db.get(key)

        if not post:
                self.redirect("/notAllowed")
                #self.error(404)
                return
        
        self.render("post.html", post =  post)


"""URL mapping of the application"""
app = webapp2.WSGIApplication([('/blog/?', MainPage),
                              ('/blog/newpost/?', NewPost),
                              ('/blog/all/?', All),
                               ('/blog/([0-9]+)', PostPage),
                               ('/', MainPage),
                               ('/social', Social),
                               ('/img', handlers.Image),
                               ('/loadAll/([0-9]+)', LoadAll),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
							   ('/.*', NotFound)],
                              debug=True)

