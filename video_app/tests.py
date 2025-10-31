import os, shutil

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import StreamingHttpResponse, FileResponse
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase

from video_app.api.serializers import VideoSerializer
from video_app.models import Video

User = get_user_model()


class VideoViewTests(APITestCase):
    """
    Test suite for /api/video/ endpoint with JWT cookie authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test@example.com", password="Pass123!", email="test@example.com")
        cls.url = reverse("video")

        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)
        cls.refresh_token = str(refresh)

        dummy_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
        cls.video1 = Video.objects.create(title="Video A",video_file=dummy_file)
        cls.video2 = Video.objects.create(title="Video B", video_file=dummy_file)

    def setUp(self):
        cache.clear()


    def authenticate_with_cookies(self):
        self.client.cookies["access_token"] = self.access_token
        self.client.cookies["refresh_token"] = self.refresh_token
    
    def test_video_list_returns_200_and_data(self):
        """GET /api/video/ → 200 OK + contains all videos"""

        self.authenticate_with_cookies()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        videos = Video.objects.all().order_by("-created_at")
        serializer = VideoSerializer(videos, many=True)

        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)
    
    def test_video_list_unauthenticated_returns_401(self):
        """GET /api/video/ without authentication → 401 Unauthorized"""
    
        response = self.client.get(self.url)
    
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_cache_is_cleared_after_new_video_created(self):
        """The cache is automatically cleared when a new video is created."""
        
        self.authenticate_with_cookies()
        response_1 = self.client.get(self.url)
        
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get("video_list"))
    
        dummy_file = SimpleUploadedFile("video_c.mp4", b"file_content", content_type="video/mp4")
        Video.objects.create(title="Video C", video_file=dummy_file)
    
        self.assertIsNone(cache.get("video_list"))

    def test_video_list_ordering_desc(self):
        """Videos are sorted by -created_at"""

        self.authenticate_with_cookies()
        response = self.client.get(self.url)
        
        titles = [v["title"] for v in response.data]
        self.assertEqual(titles[0], "Video B")
        self.assertEqual(titles[1], "Video A")


class VideoHLSViewTests(APITestCase):
    """
    Test suite for /api/video/<movie_id>/<resolution>/index.m3u8 endpoint with JWT cookie authentication and caching.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="hlsuser@example.com", password="Pass123!", email="hlsuser@example.com")
    
        dummy_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
        cls.video = Video.objects.create(title="Test Video", video_file=dummy_file)
    
        cls._prepare_resolution_directory()
        cls.url = reverse("video_hls", args=[cls.video.id, cls.resolution])
    
        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)
        cls.refresh_token = str(refresh)
    
    @classmethod
    def _prepare_resolution_directory(cls):
        cls.resolution = "720p"
        cls.base_dir = cls.video.base_dir
        os.makedirs(os.path.join(cls.base_dir, cls.resolution), exist_ok=True)
    
        cls.index_path = os.path.join(cls.base_dir, cls.resolution, "index.m3u8")
        with open(cls.index_path, "w") as f:
            f.write("#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:10.0,\nfileSequence0.ts\n")

    def setUp(self):
        cache.clear()


    def authenticate_with_cookies(self):
        self.client.cookies["access_token"] = self.access_token
        self.client.cookies["refresh_token"] = self.refresh_token

    def test_returns_401_when_not_authenticated(self):
        """GET without Login → 401"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_200_and_playlist_content_when_authenticated(self):
        """GET requests with valid JWT cookies deliver a playlist"""

        self.authenticate_with_cookies()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertIn("#EXTM3U", response.getvalue().decode())

    def test_returns_404_if_playlist_not_found(self):
        """If playlist file is missing → 404"""

        self.authenticate_with_cookies()

        bad_url = reverse("video_hls", args=[self.video.id, "1080p"])  # nicht vorhandene Auflösung
        response = self.client.get(bad_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_uses_cache_after_first_request(self):
        """Second GET uses cache"""

        self.authenticate_with_cookies()
        response_1 = self.client.get(self.url)

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(f"hls_playlist_{self.video.id}_{self.resolution}"))

        response_2 = self.client.get(self.url)

        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_2.getvalue(), response_1.getvalue())

    def test_cache_is_updated_after_manual_clear(self):
        """After clearing the cache, the playlist will be reloaded"""

        self.authenticate_with_cookies()
        self.client.get(self.url)
        
        self.assertIsNotNone(cache.get(f"hls_playlist_{self.video.id}_{self.resolution}"))

        cache.clear()
        with open(self.index_path, "a") as f:
            f.write("#EXTINF:5.0,\nfileSequence1.ts\n")
        response = self.client.get(self.url)
        data = response.getvalue().decode()

        self.assertIn("fileSequence1.ts", data)


class VideoHLSSegmentViewTests(APITestCase):
    """
    Test suite for /api/video/<id>/<resolution>/<segment>/ endpoint with JWT cookie authentication and caching.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="segmentuser@example.com", password="Pass123!", email="segmentuser@example.com")

        dummy_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
        cls.video = Video.objects.create(title="Test Video", video_file=dummy_file)

        cls._prepare_resolution_directory()
        cls.url = reverse("video_hls_segment", args=[cls.video.id, cls.resolution, cls.segment_name])

        refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(refresh.access_token)
        cls.refresh_token = str(refresh)

    @classmethod
    def _prepare_resolution_directory(cls):
        cls.resolution = "720p"
        cls.base_dir = cls.video.base_dir
        os.makedirs(os.path.join(cls.base_dir, cls.resolution), exist_ok=True)

        cls.segment_name = "segment0.ts"
        cls.segment_path = os.path.join(cls.base_dir, cls.resolution, cls.segment_name)
        with open(cls.segment_path, "wb") as f:
            f.write(b"FAKE-TS-DATA")

    def setUp(self):
        cache.clear()


    def authenticate_with_cookies(self):
        self.client.cookies["access_token"] = self.access_token
        self.client.cookies["refresh_token"] = self.refresh_token

    def test_returns_200_and_correct_segment(self):
        """GET existing segment returns 200 and correct file"""

        self.authenticate_with_cookies()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, FileResponse)

        content = b"".join(response.streaming_content)
        with open(self.segment_path, "rb") as f:
            expected = f.read()
        
        self.assertEqual(content, expected)

    def test_returns_404_if_segment_not_found(self):
        """GET non-existent segment → 404"""

        self.authenticate_with_cookies()
        bad_url = reverse("video_hls_segment", args=[self.video.id, "720p", "notfound.ts"])

        response = self.client.get(bad_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Segment not found", response.data["detail"])

    def test_uses_cache_on_second_request(self):
        """Second request for same segment uses cache"""

        self.authenticate_with_cookies()
        response_1 = self.client.get(self.url)

        self.assertEqual(response_1.status_code, 200)
        cache_key = f"hls_segment_{self.video.id}_{self.resolution}_{self.segment_name}"
        self.assertIsNotNone(cache.get(cache_key))

        response_2 = self.client.get(self.url)

        self.assertEqual(response_2.status_code, 200)
        data_1 = b"".join(response_1.streaming_content)
        data_2 = b"".join(response_2.streaming_content)
        self.assertEqual(data_1, data_2)

    def test_returns_401_if_not_authenticated(self):
        """Request without JWT cookies → 401"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @classmethod
    def tearDownClass(cls):
        """Clean up files after test"""

        if os.path.exists(cls.base_dir):
            shutil.rmtree(cls.base_dir)
        super().tearDownClass()
