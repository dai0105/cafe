from django.contrib import admin
from .models import Cafe, Tag, CafeImage, Review, ReviewImage


class CafeAdmin(admin.ModelAdmin):
    filter_horizontal = ('tags',)

class CafeImageAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'image_type', 'order')
    list_filter = ('image_type',)
    ordering = ('cafe', 'image_type', 'order')

class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'image_type', 'order')
    list_filter = ('image_type',)
    ordering = ('review', 'image_type', 'order')


admin.site.register(Cafe, CafeAdmin)
admin.site.register(Tag)
admin.site.register(CafeImage, CafeImageAdmin)
admin.site.register(Review)
admin.site.register(ReviewImage, ReviewImageAdmin)