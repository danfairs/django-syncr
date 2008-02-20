import datetime, calendar
import math
import flickrapi
from syncr.flickr.models import Photo, PhotoSet, FavoriteList

class FlickrSyncr:
    """FlickrSyncr objects sync flickr photos, photo sets, and favorites
    lists with the Django backend.

    It does not currently sync user meta-data. Photo, PhotoSet, and
    FavoriteList objects include some meta-data, but are mostly Django
    ManyToManyFields to Photo objects.

    This app requires Beej's flickrapi library. Available at:
    http://flickrapi.sourceforge.net/
    """
    def __init__(self, flickr_key, flickr_secret):
        """Construct a new FlickrSyncr object.

        Required arguments
          flickr_key: a Flickr API key string
          flickr_secret: a Flickr secret key as a string        
        """
        self.flickr = flickrapi.FlickrAPI(flickr_key, flickr_secret)

    def user2nsid(self, username):
        """Convert a flickr username to an NSID
        """
        return self.flickr.people_findByUsername(username=username).user[0]['nsid']

    def _getXMLNodeTag(self, node):
        try:
            return " ".join([x.elementText for x in node.photo[0].tags[0].tag])
        except AttributeError:
            return " "

    def getPhotoSizeURLs(self, photo_id):
        """Return a dictionary of image URLs for a flickr photo.

        Required arguments
          photo_id: a flickr photo id as a string
        """
        result = self.flickr.photos_getSizes(photo_id=photo_id)
        urls = dict()
        for el in result.sizes[0].size:
            urls[el['label']] = el['source']
        return urls
        
    def _syncPhoto(self, photo_xml):
        """Synchronize a flickr photo with the Django backend.

        Required Arguments
          photo_xml: A flickr photos in Flickrapi's REST XMLNode format
        """
        photo_id = photo_xml.photo[0]['id']
        urls = self.getPhotoSizeURLs(photo_id)
        default_dict = {'flickr_id': photo_xml.photo[0]['id'],
                        'owner': photo_xml.photo[0].owner[0]['username'],
                        'owner_nsid': photo_xml.photo[0].owner[0]['nsid'],
                        'title': photo_xml.photo[0].title[0].elementText,
                        'description': photo_xml.photo[0].description[0].elementText,
                        'taken_date': datetime.datetime.strptime(photo_xml.photo[0].dates[0]['taken'], "%Y-%m-%d %H:%M:%S"),
                        'photopage_url': photo_xml.photo[0].urls[0].url[0].elementText,
                        'square_url': urls['Square'],
                        'small_url': urls['Small'],
                        'medium_url': urls['Medium'],
                        'thumbnail_url': urls['Thumbnail'],
                        'tag_list': self._getXMLNodeTag(photo_xml)}
        obj, created = Photo.objects.get_or_create(flickr_id = photo_xml.photo[0]['id'],
                                                   defaults=default_dict)
        return obj

    def _syncPhotoXMLList(self, photos_xml):
        """Synchronize a list of flickr photos with Django ORM.

        Required Arguments
          photos_xml: A list of photos in Flickrapi's REST XMLNode format.
        """
        photo_list = []
        for photo in photos_xml:
            photo_result = self.flickr.photos_getInfo(photo_id = photo['id'])
            photo_list.append(self._syncPhoto(photo_result))
        return photo_list

    def syncAllPublic(self, username):
        """Synchronize all of a flickr user's photos with Django.
        WARNING: This could take a while!

        Required arguments
          username: a flickr username as a string
        """
        nsid = self.user2nsid(username)
        count = int(self.flickr.people_getInfo(user_id=nsid).person[0].photos[0].count[0].elementText)
        pages = int(math.ceil(count / 500))

        for page in range(1, pages + 1):
            result = self.flickr.people_getPublicPhotos(user_id=nsid, per_page=500, page=page)
            self._syncPhotoXMLList(result.photos[0].photo)
            
    def syncRecentPhotos(self, username, days=1):
        """Synchronize recent public photos from a flickr user.

        Required arguments
          username: a flickr username as a string
        Optional arguments
          days: sync photos since this number of days, defaults
                to 1 (yesterday)
        """
        syncSince = datetime.datetime.now() - datetime.timedelta(days=days)
        timestamp = calendar.timegm(syncSince.timetuple())
        nsid = self.user2nsid(username)
        
        result = self.flickr.photos_search(user_id=nsid, per_page=500, min_upload_date=timestamp)
        page_count = result.photos[0]['pages']
            
        for page in range(1, int(page_count)+1):
            photo_list = self._syncPhotoXMLList(result.photos[0].photo)
            result = self.flickr.photos_search(user_id=nsid, page=page+1, per_page=500, min_upload_date=timestamp)

    def syncPublicFavorites(self, username):
        """Synchronize a flickr user's public favorites.

        Required arguments
          username: a flickr user name as a string
        """
        nsid = self.user2nsid(username)
        favList, created = FavoriteList.objects.get_or_create(owner = username,
                                                     defaults = {'sync_date': datetime.datetime.now()})

        result = self.flickr.favorites_getPublicList(user_id=nsid, per_page=500)
        page_count = int(result.photos[0]['pages'])
        for page in range(1, page_count+1):
            photo_list = self._syncPhotoXMLList(result.photos[0].photo)
            for photo in photo_list:
                favList.photos.add(photo)
            result = self.flickr.favorites_getPublicList(user_id=nsid, per_page=500, page=page+1)

    def syncPhotoSet(self, photoset_id):
        """Synchronize a single flickr photo set based on the set id.

        Required arguments
          photoset_id: a flickr photoset id number as a string
        """
        photoset_xml = self.flickr.photosets_getInfo(photoset_id = photoset_id)
        nsid = photoset_xml.photoset[0]['owner']
        username = self.flickr.people_getInfo(user_id = nsid).person[0].username[0].elementText
        result = self.flickr.photosets_getPhotos(photoset_id = photoset_id)
        page_count = int(result.photoset[0]['pages'])

        d_photoset, created = PhotoSet.objects.get_or_create(flickr_id = photoset_id,
                                                    defaults = {'owner': username,
                                                                'flickr_id': result.photoset[0]['id'],
                                                                'title': photoset_xml.photoset[0].title[0].elementText,
                                                                'description': photoset_xml.photoset[0].description[0].elementText})
        for page in range(1, page_count+1):
            photo_list = self._syncPhotoXMLList(result.photoset[0].photo)
            for photo in photo_list:
                d_photoset.photos.add(photo)
            result = self.flickr.photosets_getPhotos(photoset_id = photoset_id,
                                                     page = page+1)

    def syncAllPhotoSets(self, username):
        """Synchronize all photo sets for a flickr user.

        Required arguments
          username: a flickr username as a string
        """
        nsid = self.user2nsid(username)
        result = self.flickr.photosets_getList(user_id=nsid)

        for photoset in result.photosets[0].photoset:
            self.syncPhotoSet(photoset['id'])
