import os, shutil

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import Video
from .tasks import convert_video_hls


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    A video object is stored in the database.
    """
        
    print(f"🎥 New Video: {instance.video_file.path}")
    convert_video_hls.delay(instance.id)

    clear_cache(instance)


@receiver(post_delete, sender=Video)
def delete_files(sender, instance, **kwargs):
    """
    The files (hls, thumbnails, videos) from media/ will be deleted as soon as the model is deleted.
    """
    
    if instance.video_file:
        instance.video_file.delete(save=False)

    if instance.thumbnail:
        instance.thumbnail.delete(save=False)
    
    if hasattr(instance, 'base_dir') and os.path.exists(instance.base_dir):
        shutil.rmtree(instance.base_dir)

    clear_cache(instance)


@receiver(pre_save, sender=Video)
def delete_old_files_on_update(sender, instance, **kwargs):
    """
    When updating, delete the old file (hls, thumbnails, videos) before saving the new one.
    """
    
    if not instance.pk:
        return

    try:
        old_instance = Video.objects.get(pk=instance.pk)
    except Video.DoesNotExist:
        return
    
    _delete_video_hls_thumbnail(old_instance, instance)


def _delete_video_hls_thumbnail(old_instance, instance):
    if old_instance.video_file and old_instance.video_file != instance.video_file:
        old_instance.video_file.delete(save=False)
        clear_cache(old_instance)

        if hasattr(old_instance, 'base_dir') and os.path.exists(old_instance.base_dir):
            shutil.rmtree(old_instance.base_dir)

    if old_instance.thumbnail and old_instance.thumbnail != instance.thumbnail:
        old_instance.thumbnail.delete(save=False)


def clear_cache(instance):
    """
    Clear cache for VideoView, VideoHLSView and VideoHLSSegmentView.
    """
    
    print('✅ Cache cleared.')
    cache.delete("video_list")

    video_id = instance.id
    for res in ["480p", "720p", "1080p"]:
        cache.delete(f"hls_playlist_{video_id}_{res}")

    for res in ["480p", "720p", "1080p"]:
        dir_path = os.path.join(instance.base_dir, res)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith(".ts"):
                    cache.delete(f"hls_segment_{video_id}_{res}_{filename}")
