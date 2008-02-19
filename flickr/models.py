from django.db import models
from tagging.validators import isTagList
from tagging.models import Tag, TaggedItem

class Photo(models.Model):
    flickr_id = models.PositiveIntegerField()
    owner = models.CharField(max_length=50)
    owner_nsid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=250, blank=True)
    taken_date = models.DateTimeField()
    photopage_url = models.URLField()
    square_url = models.URLField()
    small_url = models.URLField()
    medium_url = models.URLField()
    thumbnail_url = models.URLField()
    tag_list = models.CharField(max_length=250, validator_list=[isTagList])
    enable_comments = models.BooleanField(default=True)

    def __unicode__(self):
        return u'%s' % self.title

    def _get_tags(self):
        return Tag.objects.get_for_object(self)
    def _set_tags(self, tag_list):
        Tag.objects.update_tags(self, tag_list)
    tags = property(_get_tags, _set_tags)

    def save(self):
        super(Photo, self).save()
        Tag.objects.update_tags(self, self.tag_list)

    class Meta:
        ordering = ('-taken_date',)
        get_latest_by = 'taken_date'

    class Admin:
        list_display = ('taken_date', 'title', 'flickr_id', 'owner')
        search_fields = ['title', 'description']
        date_hierarchy = 'taken_date'

class FavoriteList(models.Model):
    owner = models.CharField(max_length=50)
    sync_date = models.DateTimeField()
    photos = models.ManyToManyField('Photo')

    def numPhotos(self):
        return len(self.photo_list.objects.all())

    def __unicode__(self):
        return u"%s's favorite photos" % self.owner
    
    class Admin:
        list_display = ('owner', 'sync_date', 'numPhotos')

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

    class Admin:
        list_display = ('flickr_id', 'owner', 'title')
