from django.contrib import admin
from django.utils.html import format_html

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'created_at', 'thumbnail_preview')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description', 'category')
    readonly_fields = ('thumbnail_preview',)
    ordering = ('-created_at',)
    fields = ('title', 'description', 'category', 'thumbnail_preview', 'thumbnail', 'video_file')

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(f'<img src="{obj.thumbnail.url}" width="80" height="50" style="object-fit:cover;" />')
        return "—"
    thumbnail_preview.short_description = 'Thumbnail'
