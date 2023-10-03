# Chrome Extension Backend

## Overview

This service offers an API for recording and processing videos. Users can upload video data in the form of "blobs" or
chunks, which the service then compiles, compresses, and extracts thumbnails from. It's designed to integrate with a
Chrome extension that captures the user's screen.

## Features

- **Blob-based Video Upload**: Instead of sending large video files, users can break them into smaller blobs and send
  them sequentially.
- **Video Compression**: Once a video is fully received, it is compressed to save space.
- **Thumbnail Extraction**: A thumbnail image is extracted from the video for preview purposes.
- **User-specific Storage**: Videos are stored in user-specific folders to keep data organized.
- **Database Integration**: Video data, including paths and processing status, is stored in a database.

## How It Works

### Blob Upload

The service is designed to handle video uploads as a series of smaller blobs. Each blob is associated with metadata such
as:

- **blobId**: ID of the particular chunk to maintain order.
- **username**: Identifier for the user.
- **filename**: Name to save the video file under.
- **blobObject**: The actual chunk of video data.
- **is_last**: Indicates if the blob is the last one for that video.

Upon receiving each blob, the service saves it in a temporary folder specific to the user and the video. Once the last
blob is received, the service merges them to form the complete video.

### Video Processing

After a video is fully uploaded, it undergoes two processing steps:

1. **Compression**: The video is compressed to reduce its file size.
2. **Thumbnail Extraction**: A representative thumbnail image is extracted from the video.

## How to Use

### Setup

1. Ensure you have the required dependencies installed. This service uses FastAPI, SQLAlchemy, and other libraries.
2. Set up the database and configure the `DATABASE_URL` in `settings.py`.
3. Run the service using a tool like Uvicorn: `uvicorn main:app --reload`.

### Sending Blobs

You can test the blob upload functionality using the provided `test_blob.py` script. This script:

- Takes a video file and breaks it into smaller blobs (by default, 1MB each).
- Sends each blob to the service's `/upload_blob/` endpoint.
- Continues until the entire video is sent.

To use the script:

1. Set the `VIDEO_FILE_PATH` variable to the path of your video.
2. Run the script: `python test_blob.py`.

### API Endpoints

- **/upload_blob/**: POST endpoint to upload video blobs.
- **... (others based on your full implementation)**

## Limitations

- **Blob Size**: The current implementation splits videos into 1MB blobs. This size might need adjustment based on
  network conditions or video characteristics.
- **Video Formats**: The service assumes `.webm` format for the blobs. Other formats might require modifications to the
  processing logic.
- **Error Handling**: As this is an educational project, it doesn't implement exhaustive error handling. Production
  deployments should incorporate more robust error checks and handling mechanisms.

## Future Improvements

- **Improved Video Splitting**: Instead of splitting videos based on size, consider splitting based on keyframes or time
  intervals for smoother video reconstruction.
- **Security Enhancements**: Add authentication and authorization mechanisms to protect video data and ensure only
  authorized users can upload or access videos.
- **Scalability**: Consider adding distributed processing for video compression and thumbnail extraction to handle large
  numbers of simultaneous uploads.

## ffmpeg commands (for reference)

### Extract audio from video

Extract raw audio to `aac` format. Y
ou can change `aac` to `flac` as well.

```shell
ffmpeg -i input.mkv -vn -c:a copy output.aac
```

Extract audio and re-encode to mp3. You can increase the `-q:a` value form 2 to a higher value in order to get a smaller
lower quality audio.

```shell
ffmpeg -i test_rec.mkv -vn -c:a libmp3lame -q:a 2 output.mp3
```

Extract audio and compress to mp3 using bitrate flag. A lower bitrate produces a lower quality and smaller audio file.

```shell
ffmpeg -i test_rec.mkv -vn -c:a libmp3lame -b:a 64k output.mp3
```

Same thing as above but for `aac` format

```shell
ffmpeg -i test_rec.mkv -vn -c:a aac -b:a 48k output.aac
```
