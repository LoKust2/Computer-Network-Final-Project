from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_token
from storage import create_session_folder, save_video_file, save_metadata
from datetime import datetime
from pathlib import Path
import uuid
import os
import pytz

app = FastAPI()

tz = pytz.timezone("Asia/Bangkok")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def home():
    html = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.post("/verify-token")
async def verify_token_api(token: str = Form(...)):
    valid, user = verify_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "status": "ok",
        "user": user
    }


BASE_DIR = "uploads"
os.makedirs(BASE_DIR, exist_ok=True)

@app.post("/session/start")
async def start_session(user: str = Form(...)):
    """
    Creates a session folder and returns a token
    """
    try:
        token = str(uuid.uuid4())
        now = datetime.now()
        folder_name = now.strftime("%d_%m_%Y_%H_%M_") + user
        folder_path = os.path.join(BASE_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Save metadata file
        with open(os.path.join(folder_path, "metadata.txt"), "w") as f:
            f.write(f"user={user}\ntoken={token}\n")

        return {"token": token}
    except Exception as e:
        return {"error": str(e)}



@app.post("/upload-one")
async def upload_one(
    session_id: str = Form(...),
    question_number: int = Form(...),
    video: UploadFile = File(...)
):
    file_path = save_video_file(session_id, question_number, video)

    return {
        "status": "uploaded",
        "file": file_path,
        "question": question_number
    }


@app.post("/session/finish")
async def finish_session(
    session_id: str = Form(...),
    metadata: str = Form(...)
):
    save_metadata(session_id, metadata)

    return {
        "status": "session complete",
        "metadata_saved": True
    }
