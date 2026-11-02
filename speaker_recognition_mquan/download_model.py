"""
Script hỗ trợ tải mô hình Zipformer Streaming 30M từ Hugging Face Hub:
Repo: https://huggingface.co/hynt/Zipformer-30M-RNNT-Streaming-6000h
"""

from pathlib import Path
import sys

REPO_ID = "hynt/Zipformer-30M-RNNT-Streaming-6000h"
MODEL_DIR = Path(__file__).parent / "models"

FILES_TO_DOWNLOAD = [
    "config.json",
    "encoder-epoch-31-avg-11-chunk-16-left-128.fp16.onnx",
    "decoder-epoch-31-avg-11-chunk-16-left-128.fp16.onnx",
    "joiner-epoch-31-avg-11-chunk-16-left-128.fp16.onnx",
]


def download_models(target_dir: Path = MODEL_DIR) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    missing = [f for f in FILES_TO_DOWNLOAD if not (target_dir / f).is_file()]

    if not missing:
        print(f"[OK] Tất cả file mô hình đã sẵn sàng trong: {target_dir}")
        return

    print(f"Đang tải các file mô hình còn thiếu từ Hugging Face ({REPO_ID})...")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("[Lỗi] Thư viện 'huggingface_hub' chưa được cài đặt.")
        print("Vui lòng chạy: pip install huggingface_hub")
        sys.exit(1)

    for filename in missing:
        print(f"-> Đang tải {filename}...")
        downloaded = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
        print(f"   Đã lưu: {downloaded}")

    print("[Hoàn tất] Tải mô hình thành công!")


if __name__ == "__main__":
    download_models()
