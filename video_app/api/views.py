from rest_framework.generics import ListAPIView

from video_app.models import Video
from .serializers import VideoSerializer


class VideoView(ListAPIView):
    serializer_class = VideoSerializer
    queryset = Video.objects.all().order_by('-created_at')
