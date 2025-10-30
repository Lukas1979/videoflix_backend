from django.urls import path

from .views import VideoView, VideoHLSView, VideoHLSSegmentView


urlpatterns = [
    path('', VideoView.as_view(), name='video'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', VideoHLSView.as_view(), name="video_hls"),
    path('<int:movie_id>/<str:resolution>/<str:segment>/', VideoHLSSegmentView.as_view(), name="video_hls_segment")
]
