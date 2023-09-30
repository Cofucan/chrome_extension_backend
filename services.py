import os
import subprocess

from fastapi import HTTPException

from database import get_db
from models import Video


def process_video(
    video_id: int,
    file_location: str,
    compressed_location: str,
    thumbnail_location: str,
):
    db = next(get_db())
    video = db.query(Video).filter(Video.id == video_id).first()

    try:
        compress_video(file_location, compressed_location)
        extract_thumbnail(compressed_location, thumbnail_location)
    except Exception as err:
        # Delete the uploaded file if an error occurs
        if os.path.exists(file_location):
            os.remove(file_location)
        # Update the video status to `failed`
        video.status = "failed"
        raise HTTPException(status_code=500, detail=str(err)) from err

    # Update the video status to complete
    video.status = "complete"

    db.commit()
    db.close()


def compress_video(input_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vcodec",
        "libx264",
        "-crf",
        "28",  # Lower values will have better quality but larger size.
        output_path,
    ]
    subprocess.run(command, check=True)


def extract_thumbnail(video_path: str, thumbnail_path: str) -> None:
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-ss",
        "00:00:02.000",  # Grab a frame at the 2-second mark
        "-vframes",
        "1",
        thumbnail_path,
    ]
    subprocess.run(command, check=True)


def is_valid_video(file_location: str) -> bool:
    metadata_command = ["ffmpeg", "-i", file_location]
    result = subprocess.run(
        metadata_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    msg = "Invalid data found when processing input"
    return msg not in result.stderr


def create_directory(*args):
    for path in args:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
