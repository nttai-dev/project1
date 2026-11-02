"""
asr_engine.py
Module quản lý mô hình Zipformer Streaming ASR (sherpa-onnx).
Mô hình từ Hugging Face: hynt/Zipformer-30M-RNNT-Streaming-6000h
"""

from io import BytesIO
from pathlib import Path
from typing import Generator, Tuple, Union
import numpy as np
import sherpa_onnx
import soundfile as sf


class ZipformerASREngine:
    """Wrapper đơn giản, tải và quản lý mô hình nhận dạng tiếng nói Zipformer."""

    def __init__(self, model_dir: Union[str, Path] = "models", num_threads: int = 2):
        self.model_dir = Path(model_dir)
        self.num_threads = num_threads

        tokens_path = self.model_dir / "config.json"
        encoder_path = self.model_dir / "encoder-epoch-31-avg-11-chunk-16-left-128.fp16.onnx"
        decoder_path = self.model_dir / "decoder-epoch-31-avg-11-chunk-16-left-128.fp16.onnx"
        joiner_path = self.model_dir / "joiner-epoch-31-avg-11-chunk-16-left-128.fp16.onnx"

        for p in (tokens_path, encoder_path, decoder_path, joiner_path):
            if not p.is_file():
                raise FileNotFoundError(
                    f"Không tìm thấy file mô hình: {p}. Vui lòng chạy `python download_model.py`."
                )

        # Khởi tạo OnlineRecognizer từ checkpoint Transducer
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(tokens_path),
            encoder=str(encoder_path),
            decoder=str(decoder_path),
            joiner=str(joiner_path),
            num_threads=self.num_threads,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
        )

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Đưa audio về dạng mono float32 chuẩn [-1.0, 1.0]."""
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        return audio

    def transcribe_file(self, audio_source: Union[str, Path, bytes, BytesIO]) -> dict:
        """
        Nhận diện toàn bộ một file audio (đường dẫn hoặc bytes).
        Trả về kết quả text và thời lượng (giây).
        """
        if isinstance(audio_source, bytes):
            audio_source = BytesIO(audio_source)

        audio, sample_rate = sf.read(audio_source, dtype="float32")
        audio = self._normalize_audio(audio)
        duration_s = float(len(audio) / sample_rate)

        # Tạo luồng nhận dạng tạm thời cho file này
        stream = self.recognizer.create_stream()
        stream.accept_waveform(sample_rate, audio)

        while self.recognizer.is_ready(stream):
            self.recognizer.decode_stream(stream)

        text = self.recognizer.get_result(stream)
        return {
            "text": text.strip(),
            "duration_seconds": round(duration_s, 2),
            "sample_rate": sample_rate,
        }

    def create_stream(self):
        """Tạo một stream mới phục vụ nhận dạng trực tiếp qua mic hoặc WebSocket."""
        return self.recognizer.create_stream()

    def process_chunk(self, stream, chunk: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Nạp một chunk audio vào stream, giải mã và trả về text tích lũy hiện tại.
        """
        chunk = self._normalize_audio(chunk)
        stream.accept_waveform(sample_rate, chunk)

        while self.recognizer.is_ready(stream):
            self.recognizer.decode_stream(stream)

        return self.recognizer.get_result(stream).strip()
