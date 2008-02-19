"""django-syncr: Synchronize Django with the web.

This project supplies everything needed to sync a Django project
with several web APIs. It currently supports 4 services:
   - Flickr (http://flickr.com)
   - YouTube (http://youtube.com)
   - del.icio.us (http://del.icio.us)
   - Twitter (http://twitter.com)

Additional web services can be added easily. Suggestions for
more services and/or patches welcome!

DEPENDENCIES

Each syncr app has different dependencies, but generally you should
have ElementTree. ET is included in Python 2.5, but for older versions
you need to download it from http://effbot.org/zone/element-index.htm.

The twitter app depends on python-twitter, available at:
http://code.google.com/p/python-twitter/

The flickr app depends on Beej's Python flickrapi, available at:
http://flickrapi.sourceforge.net/

INSTALLATION / USAGE

1. Add the syncr app to your PYTHONPATH.
2. Modify your Django settings file by adding the appropriate
   modules to your INSTALLED_APPS. Available modules are:
   'syncr.flickr'
   'syncr.youtube'
   'syncr.twitter'
   'syncr.delicious'
3. Use the interfaces provided in syncr.app to write scripts
   for synchronizing your web service data with the Django backend.

   For example:
   from syncr.app.flickr import FlickrSyncr

   f = FlickrSyncr(API_KEY, API_SECRET)
   
   # sync all my photos from the past week...
   f.syncRecentPhotos('jesselegg', days=7)

   # sync my favorite photos
   f.syncPublicFavorites('jesselegg')

4. Explore the results in the Django admin interface.
"""

__author__ = 'jesse@jesselegg.com'
__version__ = '0.2'
