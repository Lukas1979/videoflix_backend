import os

from django.conf import settings
from django.db import models


class Video(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    category = models.CharField(max_length=100)
    video_file = models.FileField(upload_to='videos/')

    @property
    def base_dir(self):
        return os.path.join(settings.MEDIA_ROOT, 'hls', str(self.id))
