import os
import subprocess

from django_rq import job

from .models import Video


CONTENT = """
    #EXTM3U
    #EXT-X-VERSION:3

    #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480
    480p/index.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720
    720p/index.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1920x1080
    1080p/index.m3u8
"""


@job('default')
def convert_video_hls(video_id):
    """
    Creates HLS streams in 480p, 720p, and 1080p using ffmpeg. Runs in the background via django-rq.
    """

    video = Video.objects.get(id=video_id)
    input_path = video.video_file.path
    output_base = video.base_dir
    os.makedirs(output_base, exist_ok=True)
    
    resolutions = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080"}
    _conversion_process(resolutions, output_base, input_path)
    _create_master_playlist(video.base_dir)

    print(f"✅ HLS conversion for video {video_id} completed.")


def _conversion_process(resolutions, output_base, input_path):
    for res, size in resolutions.items():
        output_dir = os.path.join(output_base, res)
        os.makedirs(output_dir, exist_ok=True)

        index_path = os.path.join(output_dir, "index.m3u8")
        if os.path.exists(index_path):
            print(f"✅ {res} already exists, skip …")
            continue

        print(f"🔧 Convert {res} …")
        subprocess.run(_ffmpeg_command(input_path, size, output_dir, index_path), check=True)


def _ffmpeg_command(input_path, size, output_dir, index_path):
    return [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale={size}", "-c:a", "aac",
            "-ar", "48000", "-c:v", "h264",
            "-profile:v", "main", "-crf", "20",
            "-sc_threshold", "0", "-g", "48",
            "-keyint_min", "48", "-hls_time", "4",
            "-hls_playlist_type", "vod", "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),
            index_path,
        ]


def _create_master_playlist(output_base):
    master_path = os.path.join(output_base, "master.m3u8")
    if os.path.exists(master_path):
        print("✅ master.m3u8 already exists, skip …")
        return
    
    content = CONTENT
    with open(master_path, "w") as f:
        f.write(content)

    print("✅ master.m3u8 created.")
