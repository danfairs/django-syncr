import calendar
from datetime import datetime, timedelta
from time import strptime
import math
import flickrapi
from django.core.exceptions import ObjectDoesNotExist
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
        self.flickr = flickrapi.FlickrAPI(flickr_key, flickr_secret, format='xmlnode')

    def user2nsid(self, username):
        """Convert a flickr username to an NSID
        """
        return self.flickr.people_findByUsername(username=username).user[0]['nsid']

    def _getXMLNodeTag(self, node):
        try:
            return " ".join([x.text for x in node.photo[0].tags[0].tag])
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

    def getExifInfo(self, photo_id):
        """Obtain the exif information for a photo_id

        Required arguments
          photo_id: a flickr photo id as a string
        """
        def getRawOrClean(xmlnode):
            try:
                return xmlnode.clean[0].text
            except AttributeError:
		try:
		    return xmlnode.raw[0].text
		except AttributeError:
		    return ''

        def testResultKey(result_elem, label):
            if result_elem['label'] == label:
                return getRawOrClean(result_elem)
            else:
                return None

        exif_data = {'Make': '', 'Model': '', 'Orientation': '',
                     'Exposure': '', 'Software': '', 'Aperture': '',
                     'ISO': '', 'Metering Mode': '', 'Flash': '',
                     'Focal Length': '', 'Color Space': ''}
        try:
            result = self.flickr.photos_getExif(photo_id=photo_id)
        except flickrapi.FlickrError:
            return exif_data

	try:
	    for exif_elem in result.photo[0].exif:
		for label in exif_data.keys():
		    data = testResultKey(exif_elem, label)
		    if data:
			exif_data[label] = data
	    return exif_data
	except:
	    return exif_data

    def getGeoLocation(self, photo_id):
        """Obtain the geographical location information for a photo_id

        Required Arguments
          photo_id: A flickr photo id
        """
        geo_data = {'Latitude': 'Unknown', 'Longitude': 'Unknown', 'Accuracy': 'Unknown'}
        try:
            result = self.flickr.photos_geo_getLocation(photo_id=photo_id)
            geo_data['Latitude'] = result.photo[0].location[0]['latitude']
            geo_data['Longitude'] = result.photo[0].location[0]['longitude']
            geo_data['Accuracy'] = result.photo[0].location[0]['accuracy']
            return geo_data
        except flickrapi.FlickrError:
            return geo_data

    def getExifKey(self, exif_data, key):
	try:
	    return exif_data[key]
	else:
	    return ''
        
    def _syncPhoto(self, photo_xml, refresh=False):
        """Synchronize a flickr photo with the Django backend.

        Required Arguments
          photo_xml: A flickr photos in Flickrapi's REST XMLNode format
        """
        photo_id = photo_xml.photo[0]['id']
        # if we're refreshing this data, then delete the Photo first...
        if refresh:
            try:
                p = Photo.objects.get(flickr_id = photo_id)
                p.delete()
            except ObjectDoesNotExist:
                pass
            
        urls = self.getPhotoSizeURLs(photo_id)
        exif_data = self.getExifInfo(photo_id)
        geo_data = self.getGeoLocation(photo_id)

	default_dict = {'flickr_id': photo_xml.photo[0]['id'],
			'owner': photo_xml.photo[0].owner[0]['username'],
			'owner_nsid': photo_xml.photo[0].owner[0]['nsid'],
			'title': photo_xml.photo[0].title[0].text,
			'description': photo_xml.photo[0].description[0].text,
			'taken_date': datetime(*strptime(photo_xml.photo[0].dates[0]['taken'], "%Y-%m-%d %H:%M:%S")[:7]),
			'photopage_url': photo_xml.photo[0].urls[0].url[0].text,
			'square_url': urls['Square'],
			'small_url': urls['Small'],
			'medium_url': urls['Medium'],
			'thumbnail_url': urls['Thumbnail'],
			'tag_list': self._getXMLNodeTag(photo_xml),
			'license': photo_xml.photo[0]['license'],
			'geo_latitude': geo_data['Latitude'],
			'geo_longitude': geo_data['Longitude'],
			'geo_accuracy': geo_data['Accuracy'],
			'exif_model': getExifKey(exif_data, 'Model'),
			'exif_make': getExifKey(exif_data, 'Make'),
			'exif_orientation': getExifKey(exif_data, 'Orientation'),
			'exif_exposure': getExifKey(exif_data, 'Exposure'),
			'exif_software': getExifKey(exif_data, 'Software'),
			'exif_aperture': getExifKey(exif_data, 'Aperture'),
			'exif_iso': getExifKey(exif_data, 'ISO'),
			'exif_metering_mode': getExifKey(exif_data, 'Metering Mode'),
			'exif_flash': getExifKey(exif_data, 'Flash'),
			'exif_focal_length': getExifKey(exif_data, 'Focal Length'),
			'exif_color_space': getExifKey(exif_data, 'Color Space'),
			}
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

    def syncPhoto(self, photo_id, refresh=False):
        """Synchronize a single flickr photo with Django ORM.

        Required Arguments
          photo_id: A flickr photo_id
        Optional Arguments
          refresh: A boolean, if true the Photo will be re-sync'd with flickr
        """
        photo_result = self.flickr.photos_getInfo(photo_id = photo_id)
        photo = self._syncPhoto(photo_result, refresh=refresh)
        return photo

    def syncAllPublic(self, username):
        """Synchronize all of a flickr user's photos with Django.
        WARNING: This could take a while!

        Required arguments
          username: a flickr username as a string
        """
        nsid = self.user2nsid(username)
        count = int(self.flickr.people_getInfo(user_id=nsid).person[0].photos[0].count[0].text)
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
        syncSince = datetime.now() - timedelta(days=days)
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
                                                     defaults = {'sync_date': datetime.now()})

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
	username = self.flickr.people_getInfo(user_id = nsid).person[0].username[0].text
        result = self.flickr.photosets_getPhotos(photoset_id = photoset_id)
        page_count = int(result.photoset[0]['pages'])

        d_photoset, created = PhotoSet.objects.get_or_create(flickr_id = photoset_id,
                                                    defaults = {'owner': username,
                                                                'flickr_id': result.photoset[0]['id'],
                                                                'title': photoset_xml.photoset[0].title[0].text,
                                                                'description': photoset_xml.photoset[0].description[0].text})
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
