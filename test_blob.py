import base64
import requests

# Configuration
VIDEO_FILE_PATH = "/home/cofucan/Videos/test_rec.mkv"
ENDPOINT_URL = "http://127.0.0.1:8000/srce/api/upload_blob/"
BLOB_SIZE = 1 * 1024 * 1024  # 1MB by default. Adjust as needed.
USERNAME = "cofucan"
FILENAME = "projectdemo"  # This should be unique for each video.


def send_blob(blob, blob_id, is_last):
    data = {
        "blobId": str(blob_id),
        "username": USERNAME,
        "filename": FILENAME,
        "blobObject": base64.b64encode(blob).decode("utf-8"),
        "is_last": str(is_last),
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(ENDPOINT_URL, json=data, headers=headers)
    print(response.text)


def main():
    with open(VIDEO_FILE_PATH, "rb") as f:
        blob_id = 1
        while True:
            blob = f.read(BLOB_SIZE)
            if not blob:
                break
            is_last = len(blob) < BLOB_SIZE
            send_blob(blob, blob_id, is_last)
            blob_id += 1


if __name__ == "__main__":
    main()
