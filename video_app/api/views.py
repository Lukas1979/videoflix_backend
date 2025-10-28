from rest_framework.generics import ListAPIView

from video_app.models import Video
from .serializers import VideoSerializer


class VideoView(ListAPIView):
    """
    GET /api/video/
    Returns a list of all available videos.
    """
    
    serializer_class = VideoSerializer
    queryset = Video.objects.all().order_by('-created_at')
