from django.db import models
from tagging.validators import is_tag_list
from tagging.models import Tag, TaggedItem

class Bookmark(models.Model):
    # description, href, tags, extended, dt
    description = models.CharField(max_length=250, blank=True)
    url = models.URLField()
    tag_list = models.CharField(max_length=250, validator_list=[is_tag_list], blank=True)
    extended_info = models.CharField(max_length=250, blank=True)
    post_hash = models.CharField(max_length=100)
    saved_date = models.DateTimeField()

    def __unicode__(self):
        return u'%s' % self.description

    def _get_tags(self):
        return Tag.objects.get_for_object(self)
    def _set_tags(self, tag_list):
        Tag.objects.update_tags(self, tag_list)
    tags = property(_get_tags, _set_tags)

    def get_absolute_url(self):
        return "/links/%s/" % self.id

    def save(self):
        super(Bookmark, self).save()
        Tag.objects.update_tags(self, self.tag_list)

    class Meta:
        ordering = ('-saved_date',)
        get_latest_by = 'saved_date'