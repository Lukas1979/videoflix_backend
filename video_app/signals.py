from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Video
from .tasks import convert_video_hls


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    A video object is stored in the database.
    """
    
    print(f"🎥 Neues Video: {instance.video_file.path}")
    convert_video_hls.delay(instance.id)
