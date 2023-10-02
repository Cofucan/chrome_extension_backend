import base64
import os
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Video, VideoBlob
from services import (
    is_valid_video,
    process_video,
    create_directory,
    save_blob,
    merge_blobs,
)
from settings import COMPRESSED_DIR, THUMBNAIL_DIR, VIDEO_DIR


router = APIRouter(prefix="/srce/api")


@router.post("/upload/")
def upload_video(
    background_tasks: BackgroundTasks,
    username: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Convert the username to lowercase
    username = username.lower()

    # Generate a unique filename using datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{username}_{timestamp}_{file.filename}"

    # Get the absolute path of the uploaded file
    file_location = os.path.join(VIDEO_DIR, unique_filename)
    file_location = os.path.abspath(file_location)

    # Create the directories if they don't exist
    create_directory(VIDEO_DIR, COMPRESSED_DIR, THUMBNAIL_DIR)

    # Save the uploaded file
    with open(file_location, "wb+") as file_object:
        for chunk in file.file:
            file_object.write(chunk)

    # Delete the uploaded file if it is not a valid video
    if not is_valid_video(file_location):
        os.remove(file_location)
        raise HTTPException(
            status_code=400,
            detail="Invalid video file. Please upload a valid video file.",
        )

    # Save the video data to the database
    video_data = Video(
        username=username,
        original_location=file_location,
        file_type=file.content_type,
    )

    db.add(video_data)
    db.commit()
    db.refresh(video_data)
    db.close()

    # Process the video in the background
    background_tasks.add_task(
        process_video,
        video_data.id,
        file_location,
        unique_filename,
    )

    return {
        "msg": "Video uploaded successfully and is being processed!",
        "video_data": video_data,
    }


@router.post("/upload_blob/")
def upload_video_blob(
    background_tasks: BackgroundTasks,
    video_blob: VideoBlob,
    db: Session = Depends(get_db),
):
    # Get the blob data
    if isinstance(video_blob.blobObject, UploadFile):
        blob_data = video_blob.blobObject.file.read()
    else:
        blob_data = base64.b64decode(video_blob.blobObject)

    # Convert the username to lowercase
    username = video_blob.username.lower()

    # Save the blob
    _ = save_blob(username, video_blob.filename, video_blob.blobId, blob_data)

    # If it's the last blob, merge all blobs and process the video
    if video_blob.is_last:
        merged_video_path = merge_blobs(username, video_blob.filename)

        # Save the video data to the database
        video_data = Video(
            username=username,
            original_location=merged_video_path,
            file_type="video/mp4",
        )

        db.add(video_data)
        db.commit()
        db.refresh(video_data)
        db.close()

        # Process the video in the background
        # background_tasks.add_task(
        #     process_video,
        #     video_data.id,
        #     merged_video_path,
        #     video_blob.filename,
        # )

        return {
            "msg": "Video blobs received successfully and video is being processed!",
            "video_data": video_data,
        }

    return {"msg": "Video blob received successfully!"}


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
