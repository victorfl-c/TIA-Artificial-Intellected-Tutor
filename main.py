from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import logging
import shutil
import os

from rag_pipeline import get_hybrid_response_stream
from ingest import run_ingestion

KNOWLEDGE_BASE_PATH = "./knowledge_base"

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Assistente PBL Offline API")

class QuestionRequest(BaseModel):
    question: str
    history: list = []

@app.post("/ask-stream")
def ask_stream(request: QuestionRequest):
    def response_generator():
        for chunk in get_hybrid_response_stream(request.question, request.history):
            yield chunk
    return StreamingResponse(response_generator(), media_type="text/plain")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []
    os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
    for file in files:
        file_path = os.path.join(KNOWLEDGE_BASE_PATH, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved_files.append(file.filename)
    logging.info(f"Arquivos enviados: {saved_files}")
    run_ingestion()
    return JSONResponse(content={
        "message": f"Arquivos salvos com sucesso: {saved_files}. Base de conhecimento reprocessada."
    })