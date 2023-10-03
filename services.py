import glob
import os
import subprocess

from fastapi import HTTPException

from database import get_db
from models import Video
from settings import COMPRESSED_DIR, THUMBNAIL_DIR, VIDEO_DIR


def process_video(
    video_id: int,
    file_location: str,
    filename: str,
):
    """
    Process a video by compressing it and extracting a thumbnail.

    Args:
        video_id (int): The ID of the video.
        file_location (str): The location of the video file.
        filename (str): The name of the video file.

    Raises:
        HTTPException: If an error occurs during video compression or thumbnail extraction.

    Returns:
        None
    """
    db = next(get_db())
    video = db.query(Video).filter(Video.id == video_id).first()

    # Generate compressed and thumbnail filenames
    comp = f"compressed_{filename}.mp4"
    compressed_location = os.path.join(COMPRESSED_DIR, comp)
    compressed_location = os.path.abspath(compressed_location)
    thumb = f"thumbnail_{filename}.jpg"
    thumbnail_location = os.path.join(THUMBNAIL_DIR, thumb)
    thumbnail_location = os.path.abspath(thumbnail_location)

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

    # Update the video status and save the compressed and thumbnail locations
    video.compressed_location = compressed_location
    video.thumbnail_location = thumbnail_location
    video.status = "complete"

    db.commit()
    db.close()


def compress_video(input_path: str, output_path: str) -> None:
    """
    Compresses a video using ffmpeg.

    Parameters:
    - input_path: The path to the input video.
    - output_path: The path to the output video.

    Returns:
    - None

    """
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
    """
    Extracts a thumbnail from a video using ffmpeg.

    Parameters:
    - video_path: The path to the input video.
    - thumbnail_path: The path to the output thumbnail.

    Returns:
    - None

    """
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
    """
    Check if a video file is valid by inspecting its metadata.
    Args:
        file_location (str): The location of the video file.
    Returns:
        bool: True if the video is valid, False otherwise.
    """
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
    """
    Create a directory or directories.
    Args:
        *args: Variable length argument list of directory paths.

    Returns:
        None
    """
    for path in args:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)


def save_blob(username: str, filename: str, blob_id: int, blob: bytes) -> str:
    """Saves a video blob/chunk.

    Parameters:
    - username: The user associated with the blob.
    - filename: The base filename for the video.
    - blob_id: The ID for this blob, indicating its sequence.
    - blob: The video blob itself.

    Returns:
    - The path to the saved blob.
    """
    # Create the directory structure if it doesn't exist
    user_dir = os.path.join(VIDEO_DIR, username)
    temp_video_dir = os.path.join(user_dir, filename)
    create_directory(user_dir, temp_video_dir)

    # Save the blob
    blob_filename = f"{blob_id}.mkv"
    blob_path = os.path.join(temp_video_dir, blob_filename)
    with open(blob_path, "wb") as f:
        f.write(blob)

    return blob_path


def merge_blobs(username: str, filename: str) -> str:
    """Merges video blobs/chunks to form the complete video.

    Parameters:
    - username: The user associated with the blobs.
    - filename: The base filename for the video.

    Returns:
    - The path to the merged video.
    """
    user_dir = os.path.join(VIDEO_DIR, username)
    user_dir = os.path.abspath(user_dir)
    temp_video_dir = os.path.join(user_dir, filename)
    temp_video_dir = os.path.abspath(temp_video_dir)

    # List all blob files and sort them by their sequence ID
    blob_files = sorted(
        glob.glob(os.path.join(temp_video_dir, "*.mkv")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]),
    )
    # Merge the blobs
    merged_video_path = os.path.join(user_dir, f"{filename}.mkv")
    with open(merged_video_path, "wb") as merged_file:
        for blob_file in blob_files:
            with open(blob_file, "rb") as f:
                merged_file.write(f.read())

    # Optionally, remove the temporary directory containing blobs
    # shutil.rmtree(temp_video_dir)

    return merged_video_path
