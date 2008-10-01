from django.contrib import admin
from syncr.flickr.models import Photo, FavoriteList, PhotoSet

class PhotoAdmin(admin.ModelAdmin):
        prepopulated_fields = {"slug": ("title",)}
	list_display = ('taken_date', 'title', 'flickr_id', 'owner')
	search_fields = ['title', 'description']
	date_hierarchy = 'taken_date'

class FavoriteListAdmin(admin.ModelAdmin):
 	list_display = ('owner', 'sync_date', 'numPhotos')

class PhotoSetAdmin(admin.ModelAdmin):
	list_display = ('flickr_id', 'owner', 'title')

admin.site.register(Photo, PhotoAdmin)
admin.site.register(FavoriteList, FavoriteListAdmin)
admin.site.register(PhotoSet, PhotoSetAdmin)
