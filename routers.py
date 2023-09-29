import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Video
from services import compress_video, extract_thumbnail, is_valid_video
from settings import COMPRESSED_DIR, THUMBNAIL_DIR, VIDEO_DIR


router = APIRouter(prefix="/chrome_ext/screen_rec/api")


@router.post("/upload/")
def upload_video(
    username: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # Convert the username to lowercase
    username = username.lower()

    # Check if the directories exist, if not create them
    if not os.path.isdir(VIDEO_DIR):
        os.makedirs(VIDEO_DIR, exist_ok=True)
    if not os.path.isdir(COMPRESSED_DIR):
        os.makedirs(COMPRESSED_DIR, exist_ok=True)
    if not os.path.isdir(THUMBNAIL_DIR):
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    # Generate a unique filename using datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{username}_{timestamp}_{file.filename}"

    # Get the absolute path of the uploaded file
    file_location = os.path.join(VIDEO_DIR, unique_filename)
    file_location = os.path.abspath(file_location)

    # Save the uploaded file
    with open(file_location, "wb+") as file_object:
        for chunk in file.file:
            file_object.write(chunk)

    # Compress and generate thumbnail, then get the absolute paths
    compressed_location = os.path.join(
        COMPRESSED_DIR, f"compressed_{unique_filename}.mp4"
    )
    compressed_location = os.path.abspath(compressed_location)
    thumbnail_location = os.path.join(
        THUMBNAIL_DIR, f"thumbnail_{unique_filename}.jpg"
    )
    thumbnail_location = os.path.abspath(thumbnail_location)

    # Delete the uploaded file if it is not a valid video
    if not is_valid_video(file_location):
        os.remove(file_location)
        raise HTTPException(
            status_code=400,
            detail="Invalid video file. Please upload a valid video file.",
        )

    try:
        compress_video(file_location, compressed_location)
        extract_thumbnail(compressed_location, thumbnail_location)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err

    # Save the video data to the database
    video_data = Video(
        username=username,
        original_location=file_location,
        compressed_location=compressed_location,
        thumbnail_location=thumbnail_location,
        file_type=file.content_type,
    )

    db.add(video_data)
    db.commit()
    db.refresh(video_data)
    db.close()

    return {"msg": "Video uploaded successfully!", "video_data": video_data}


@router.get("/videos/{username}")
def get_videos(username: str, db: Session = Depends(get_db)):
    # Convert the username to lowercase for querying
    username = username.lower()

    videos = db.query(Video).filter(Video.username == username).all()
    db.close()
    return videos


@router.get("/video/stream/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    db.close()

    if video:
        return FileResponse(video.compressed_location, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found.")


@router.delete("/video/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    if video := db.query(Video).filter(Video.id == video_id).first():
        os.remove(video.original_location)
        if os.path.exists(video.thumbnail_location):
            os.remove(video.thumbnail_location)
        if os.path.exists(video.compressed_location):
            os.remove(video.compressed_location)

        db.delete(video)
        db.commit()
        db.close()

        return {"msg": "Video deleted successfully!"}

    db.close()
    raise HTTPException(status_code=404, detail="Video not found.")
