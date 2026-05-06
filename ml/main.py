from realtime import run_realtime
from video_processing import process_video
import os
from django.conf import settings

VIDEO_PATH = os.path.join(settings.BASE_DIR, "static/videos/demo.mp4")

mode = input("Enter mode (1: realtime, 2: upload): ")

if mode == "1":
    run_realtime(VIDEO_PATH)

elif mode == "2":
    process_video(VIDEO_PATH)