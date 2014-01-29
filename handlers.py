import webapp2

from google.appengine.ext import db



class Image(webapp2.RequestHandler):
    def get(self):
        art = db.get(self.request.get('img_id'))
        if art.avatar:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(art.avatar)
        else:
                self.response.out.write("No image")

