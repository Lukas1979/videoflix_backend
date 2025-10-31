import io, os

from django.core.cache import cache
from django.http import FileResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.models import Video
from .serializers import VideoSerializer


VIDEO_LIST_CACHE_TIMEOUT = 60 * 60        # 1 hour
HLS_PLAYLIST_CACHE_TIMEOUT = 6 * 60 * 60  # 6 hours
HLS_SEGMENT_CACHE_TIMEOUT = 12 * 60 * 60  # 12 hours


class VideoView(ListAPIView):
    """
    GET /api/video/
    Returns a list of all available videos (cached).
    """
    
    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.all().order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        cache_key = "video_list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        cache.set(cache_key, data, timeout=VIDEO_LIST_CACHE_TIMEOUT)
        return Response(data)


class VideoHLSView(APIView):
    """
    GET /api/video/<int:movie_id>/<str:resolution>/index.m3u8
    Returns the HLS playlist for a video in a specific resolution (cached).
    """

    def get(self, request, movie_id, resolution):
        video = get_object_or_404(Video, id=movie_id)

        cache_key = f"hls_playlist_{movie_id}_{resolution}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return StreamingHttpResponse(cached_data, content_type="application/vnd.apple.mpegurl")
        
        return self._load_and_cache(video, resolution, cache_key)

    def _load_and_cache(self, video, resolution, cache_key):
        playlist_path = os.path.join(video.base_dir, resolution, "index.m3u8")
        if not os.path.exists(playlist_path):
            return Response({"detail": f"HLS for {resolution} not found."}, status=status.HTTP_404_NOT_FOUND)

        with open(playlist_path, "r") as f:
            data = f.read()

        cache.set(cache_key, data, timeout=HLS_PLAYLIST_CACHE_TIMEOUT)

        return StreamingHttpResponse(data, content_type="application/vnd.apple.mpegurl")


class VideoHLSSegmentView(APIView):
    """
    GET /api/video/<int:movie_id>/<str:resolution>/<str:segment>/
    Delivers a single HLS segment for a video at a specific resolution (cached).
    """

    def get(self, request, movie_id, resolution, segment):
        video = get_object_or_404(Video, id=movie_id)
        cache_key = f"hls_segment_{video.id}_{resolution}_{segment}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return FileResponse(io.BytesIO(cached_data), content_type="video/MP2T", filename=segment)

        return self._load_and_cache(video, resolution, segment, cache_key)
    
    def _load_and_cache(self, video, resolution, segment, cache_key):
        segment_path = os.path.join(video.base_dir, resolution, segment)
        if not os.path.exists(segment_path):
            return Response({"detail": "Segment not found"}, status=404)
    
        with open(segment_path, "rb") as f:
            data = f.read()
    
        cache.set(cache_key, data, timeout=HLS_SEGMENT_CACHE_TIMEOUT)
    
        return FileResponse(io.BytesIO(data), content_type="video/MP2T", filename=segment)
