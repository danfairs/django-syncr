from django.db import models
from tagging.models import Tag, TaggedItem

FLICKR_LICENSES = (
    ('0', 'All Rights Reserved'),
    ('1', 'Attribution-NonCommercial-ShareAlike License'),
    ('2', 'Attribution-NonCommercial License'),
    ('3', 'Attribution-NonCommercial-NoDerivs License'),
    ('4', 'Attribution License'),
    ('5', 'Attribution-ShareAlike License'),
    ('6', 'Attribution-NoDerivs License'),
)

class Photo(models.Model):
    flickr_id = models.PositiveIntegerField()
    owner = models.CharField(max_length=50)
    owner_nsid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    slug = models.SlugField(
	unique_for_date='taken_date',
	help_text='Automatically built from the title.'
    )
    description = models.TextField(blank=True)
    taken_date = models.DateTimeField()
    photopage_url = models.URLField()
    square_url = models.URLField()
    small_url = models.URLField()
    medium_url = models.URLField()
    thumbnail_url = models.URLField()
    tag_list = models.CharField(max_length=250)
    enable_comments = models.BooleanField(default=True)
    license = models.CharField(max_length=50, choices=FLICKR_LICENSES)
    geo_latitude = models.CharField(max_length=50, blank=True)
    geo_longitude = models.CharField(max_length=50, blank=True)
    geo_accuracy = models.CharField(max_length=50, blank=True)
    exif_make  = models.CharField(max_length=50, blank=True)
    exif_model = models.CharField(max_length=50, blank=True)
    exif_orientation = models.CharField(max_length=50, blank=True)
    exif_exposure = models.CharField(max_length=50, blank=True)
    exif_software = models.CharField(max_length=50, blank=True)
    exif_aperture = models.CharField(max_length=50, blank=True)
    exif_iso = models.CharField(max_length=50, blank=True)
    exif_metering_mode = models.CharField(max_length=50, blank=True)
    exif_flash = models.CharField(max_length=50, blank=True)
    exif_focal_length = models.CharField(max_length=50, blank=True)
    exif_color_space = models.CharField(max_length=50, blank=True)
    
    def __unicode__(self):
        return u'%s' % self.title

    def _get_tags(self):
        return Tag.objects.get_for_object(self)
    def _set_tags(self, tag_list):
        Tag.objects.update_tags(self, tag_list)
    tags = property(_get_tags, _set_tags)

    def save(self, force_insert=False, force_update=False):
        super(Photo, self).save()
        Tag.objects.update_tags(self, self.tag_list)

    class Meta:
        ordering = ('-taken_date',)
        get_latest_by = 'taken_date'


class FavoriteList(models.Model):
    owner = models.CharField(max_length=50)
    sync_date = models.DateTimeField()
    photos = models.ManyToManyField('Photo')

    def numPhotos(self):
        return len(self.photo_list.objects.all())

    def __unicode__(self):
        return u"%s's favorite photos" % self.owner

class PhotoSet(models.Model):
    flickr_id = models.CharField(max_length=50)
    owner = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=250)
    photos = models.ManyToManyField('Photo')

    def numPhotos(self):
        return len(self.photos.objects.all())

    def __unicode__(self):
        return u"%s photo set by %s" % (self.title, self.owner)
