"""
app.py
FastAPI Web Service cho mô hình nhận dạng tiếng nói tiếng Việt (ASR)
Mô hình Hugging Face: hynt/Zipformer-30M-RNNT-Streaming-6000h
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect

from asr_engine import ZipformerASREngine

import sys

# Đảm bảo UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Biến toàn cục lưu trữ engine
asr_engine: ZipformerASREngine | None = None
MODEL_NAME = "hynt/Zipformer-30M-RNNT-Streaming-6000h"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng: Tải mô hình khi khởi động và dọn dẹp khi tắt."""
    global asr_engine
    print("[Startup] Loading Zipformer Streaming model...")
    try:
        asr_engine = ZipformerASREngine(model_dir="models", num_threads=2)
        print("[Startup] Zipformer Streaming model loaded successfully!")
    except Exception as e:
        print(f"[Warning] Failed to load model automatically: {e}")
        print("Please verify model files exist in `models/` directory.")
    yield
    print("[Shutdown] Cleaning up resources...")


app = FastAPI(
    title="Vietnamese Zipformer Streaming ASR API",
    description="Web API nhận dạng tiếng nói tiếng Việt thời gian thực dựa trên mô hình Zipformer từ Hugging Face.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_engine() -> ZipformerASREngine:
    """Helper lấy instance của engine, báo lỗi 503 nếu chưa sẵn sàng."""
    if asr_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Mô hình ASR chưa sẵn sàng hoặc tải thất bại. Vui lòng kiểm tra thư mục models/."
        )
    return asr_engine


# --------------------------------------------------------------------------
# 1. Endpoint GET /: Giới thiệu hệ thống & mô tả chức năng
# --------------------------------------------------------------------------
@app.get("/", summary="Thông tin tổng quan hệ thống")
async def root() -> Dict[str, Any]:
    """Trả về mô tả hệ thống, danh sách endpoint và thông tin mô hình Hugging Face."""
    return {
        "message": "Chào mừng đến với Web API Nhận dạng Tiếng nói (ASR) Tiếng Việt!",
        "model_name": MODEL_NAME,
        "huggingface_url": f"https://huggingface.co/{MODEL_NAME}",
        "endpoints": {
            "GET /": "Giới thiệu hệ thống và danh sách endpoint.",
            "GET /health": "Kiểm tra trạng thái sẵn sàng hoạt động của hệ thống.",
            "POST /predict": "Nhận file âm thanh (.wav) và trả về văn bản nhận dạng kèm thời lượng.",
            "WS /ws/stream": "Kênh WebSocket nhận diện tiếng nói streaming từ micro thời gian thực.",
            "GET /docs": "Tài liệu tương tác OpenAPI / Swagger UI."
        }
    }


# --------------------------------------------------------------------------
# 2. Endpoint GET /health: Kiểm tra trạng thái hoạt động
# --------------------------------------------------------------------------
@app.get("/health", summary="Kiểm tra trạng thái hệ thống")
async def health_check() -> Dict[str, Any]:
    """Kiểm tra mô hình đã được tải và sẵn sàng phục vụ hay chưa."""
    is_ready = asr_engine is not None
    return {
        "status": "healthy" if is_ready else "unhealthy",
        "model_loaded": is_ready,
        "model_name": MODEL_NAME,
        "service": "Vietnamese Zipformer ASR"
    }


# --------------------------------------------------------------------------
# 3. Endpoint POST /predict: Nhận dạng âm thanh từ file upload
# --------------------------------------------------------------------------
@app.post("/predict", summary="Nhận dạng tiếng nói từ file âm thanh")
async def predict_speech(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Nhận file âm thanh người dùng gửi lên, gọi mô hình Hugging Face và trả về kết quả JSON.
    Hỗ trợ các định dạng phổ biến như .wav, .flac, .ogg.
    """
    engine = get_engine()

    # Kiểm tra tính hợp lệ của file đầu vào (Validation)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ hoặc bị thiếu.")

    valid_extensions = {".wav", ".flac", ".ogg", ".mp3"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext and file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file '{file_ext}' không được hỗ trợ. Vui lòng gửi file: {', '.join(valid_extensions)}"
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File âm thanh rỗng (0 bytes).")

        result = engine.transcribe_file(content)
        return {
            "success": True,
            "filename": file.filename,
            "text": result["text"],
            "duration_seconds": result["duration_seconds"],
            "sample_rate": result["sample_rate"],
            "model": MODEL_NAME,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi trong quá trình suy luận mô hình: {str(exc)}"
        )


# --------------------------------------------------------------------------
# 4. Endpoint WebSocket /ws/stream: Nhận dạng streaming qua Micro trực tiếp
# --------------------------------------------------------------------------
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket nhận các khối PCM audio 16-bit từ client (microphone) theo thời gian thực
    và trả về văn bản nhận dạng tức thời.
    """
    engine = get_engine()
    await websocket.accept()

    stream = engine.create_stream()
    current_text = ""

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                pcm_bytes = message["bytes"]
                if len(pcm_bytes) >= 2:
                    # Chuyển đổi mảng byte PCM 16-bit sang float32 [-1.0, 1.0]
                    chunk = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    current_text = engine.process_chunk(stream, chunk, sample_rate=16000)
                    await websocket.send_json({
                        "text": current_text,
                        "is_final": False
                    })
            elif "text" in message:
                text_msg = message["text"].strip().upper()
                if text_msg == "END":
                    await websocket.send_json({
                        "text": current_text,
                        "is_final": True
                    })
                    break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"error": str(exc)})
        except Exception:
            pass
