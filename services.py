import subprocess


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
    result = subprocess.run(metadata_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    msg = "Invalid data found when processing input"
    return msg not in result.stderr