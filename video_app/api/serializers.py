from rest_framework import serializers

from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """
    Converts video model data into JSON so it can be delivered via the API.
    """
    
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        
        if obj.thumbnail:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
