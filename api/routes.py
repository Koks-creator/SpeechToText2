import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from typing import List
from pydantic import BaseModel
import asyncio
from fastapi import HTTPException, UploadFile, File, status

from api import app, logger, Config, speech_to_text


class STTResponse(BaseModel):
    result: List[str]

class HealthResponse(BaseModel):
    status: str


def validate_audio_file(file: UploadFile) -> None:
    ext = Path(file.filename).suffix.lower()
    if ext.replace(".", "") not in Config.API_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Not allowed file format: {ext}. Allowed: {', '.join(Config.API_ALLOWED_EXTENSIONS)}"
        )

@app.get("/")
async def alive():
    return "Hello, I'm alive :) https://www.youtube.com/watch?v=9DeG5WQClUI"

@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return HealthResponse(status="all green")

@app.post("/get_text", response_model=STTResponse)
async def get_text(files: List[UploadFile] = File(...),
                   normalize: bool = False
                   ):
    try:
        logger.debug(f"Uploaded {len(files)} files")
        logger.debug(f"{normalize=}")

        for file in files:
            validate_audio_file(file)

        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
    
        if len(files) > Config.MAX_IMAGE_FILES:
            logger.error(f"(status code 400) Max number of files is {Config.MAX_IMAGE_FILES}")
            raise HTTPException(
                status_code=400,
                detail=f"Max number of files is {Config.MAX_IMAGE_FILES}"
            )
        
        contents = []
        for file in files:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Empty file: {file.filename}"
                )
            
            if len(content) > Config.API_MAX_FILE_SIZE_MB * 1024 * 1024:
                 raise HTTPException(
                    status_code=400,
                    detail=f"File: {file.filename} is too big, max size is {Config.API_MAX_FILE_SIZE_MB} MB"
                )

            contents.append(content)

        results = await asyncio.to_thread(
            speech_to_text.transcribe,
            audio_input=contents,
            normalize=normalize
        )

        logger.info(f"Done, results: {results}")
        return STTResponse(
            result=results
        )
        
    except HTTPException as http_ex:
        logger.error(f"HTTPException {http_ex}")
        raise http_ex
    except Exception as e:
        logger.error(f"(status code 500) Internal server error {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error {e}")

