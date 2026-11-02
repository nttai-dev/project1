# Vietnamese Zipformer Streaming ASR - Web API & Microphone Streaming

Dự án bài tập môn **Computational Thinking (Practice 01: Application Programming Interface)** - Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM.

Dự án triển khai một hệ thống Web API hoàn chỉnh bằng **FastAPI**, tích hợp mô hình nhận dạng tiếng nói tiếng Việt (Automatic Speech Recognition - ASR) công nghệ **Zipformer Streaming** từ **Hugging Face**, hỗ trợ cả nhận dạng file âm thanh qua REST API và nhận dạng trực tiếp qua Microphone thời gian thực qua giao thức WebSocket / Web UI.

---

## 1. Thông Tin Sinh Viên (Student Information)

- **Họ và tên**: [Điền họ và tên của bạn]
- **Mã số sinh viên (MSSV)**: [Điền MSSV]
- **Lớp**: [Điền tên lớp]
- **Khoa**: Công nghệ Thông tin - Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM

---

## 2. Mô Hình Hugging Face Sử Dụng (Selected Model)

- **Tên mô hình**: `hynt/Zipformer-30M-RNNT-Streaming-6000h`
- **Tác vụ**: Speech Recognition (ASR) tiếng Việt.
- **Kiến trúc**: Emformer/Zipformer RNN-T (Recurrent Neural Network Transducer) streaming, định dạng ONNX runtime siêu nhẹ (~50 MB tổng cộng), tối ưu chạy thời gian thực trên CPU với độ trễ chỉ ~160ms.
- **Link trực tiếp đến Hugging Face**: [https://huggingface.co/hynt/Zipformer-30M-RNNT-Streaming-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-Streaming-6000h)

---

## 3. Cấu Trúc Mã Nguồn (Source Code Structure)

```text
speaker_recognition_mquan/
├── app.py              # Ứng dụng FastAPI chính (GET /, GET /health, POST /predict, WS /ws/stream)
├── asr_engine.py       # Module nạp mô hình Zipformer & thực hiện suy luận (sherpa-onnx)
├── stream_mic.py       # Client CLI thu âm Micro thời gian thực và stream lên API qua WebSocket
├── test_api.py         # Script kiểm thử tự động toàn bộ API bằng thư viện `requests`
├── download_model.py   # Script tự động tải các file mô hình từ Hugging Face
├── requirements.txt    # Danh sách các thư viện phụ thuộc
├── models/             # Chứa trọng số ONNX và config của mô hình Zipformer
└── samples/            # 2 file audio mẫu (.wav) phục vụ kiểm thử và quay video demo
    ├── sample1.wav
    └── sample2.wav
```

---

## 4. Hướng Dẫn Cài Đặt (Installation)

### Bước 1: Chuẩn bị môi trường Python (Python 3.10 - 3.12 khuyến nghị)
Mở terminal tại thư mục dự án:
```bash
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate
```

### Bước 2: Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### Bước 3: Tải mô hình từ Hugging Face (nếu chưa có trong thư mục `models/`)
```bash
python download_model.py
```

---

## 5. Hướng Dẫn Khởi Chạy Ứng Dụng (Running the Application)

Khởi động Web API server bằng `uvicorn`:
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
Server sẽ chạy tại địa chỉ: `http://127.0.0.1:8000`

---

## 6. Hướng Dẫn Gọi API (API Usage & Examples)

### 6.1. Kiểm tra giới thiệu hệ thống (`GET /`)
- **cURL**:
  ```bash
  curl -X GET http://127.0.0.1:8000/
  ```
- **Response mẫu**:
  ```json
  {
    "message": "Chào mừng đến với Web API Nhận dạng Tiếng nói (ASR) Tiếng Việt!",
    "model_name": "hynt/Zipformer-30M-RNNT-Streaming-6000h",
    "huggingface_url": "https://huggingface.co/hynt/Zipformer-30M-RNNT-Streaming-6000h",
    "endpoints": { ... }
  }
  ```

### 6.2. Kiểm tra trạng thái hệ thống (`GET /health`)
- **cURL**:
  ```bash
  curl -X GET http://127.0.0.1:8000/health
  ```
- **Response mẫu**:
  ```json
  {
    "status": "healthy",
    "model_loaded": true,
    "model_name": "hynt/Zipformer-30M-RNNT-Streaming-6000h",
    "service": "Vietnamese Zipformer ASR"
  }
  ```

### 6.3. Nhận dạng qua file âm thanh (`POST /predict`)
Gửi một file âm thanh `.wav` qua form-data với key là `file`:
- **cURL**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/predict" \
       -H "accept: application/json" \
       -H "Content-Type: multipart/form-data" \
       -F "file=@samples/sample1.wav"
  ```
- **Response mẫu**:
  ```json
  {
    "success": true,
    "filename": "sample1.wav",
    "text": "VÀ NGÀY NÀO LÀM VIỆC KHÔNG THIỆN CON CHO MỘT HẠT ĐẬ",
    "duration_seconds": 3.94,
    "sample_rate": 16000,
    "model": "hynt/Zipformer-30M-RNNT-Streaming-6000h"
  }
  ```

### 6.4. Tài liệu tương tác Swagger UI
Truy cập trình duyệt tại: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) để xem chi tiết schema và test trực tiếp các endpoint trên web.

---

## 7. Nhận Dạng Trực Tiếp Bằng Microphone (Terminal Streaming)

Hệ thống hỗ trợ client streaming trực tiếp từ Microphone qua lệnh CLI ngay trên Terminal:

Mở một cửa sổ terminal riêng và chạy:
```bash
python stream_mic.py
```
- Client sẽ mở microphone máy tính thông qua thư viện `sounddevice`.
- Tiếng nói tiếng Việt được thu nhận và gửi liên tục qua `WebSocket /ws/stream` lên server FastAPI.
- Kết quả nhận dạng sẽ xuất hiện theo thời gian thực (real-time teleprompter) ngay trên cửa sổ console.
- Bấm `Ctrl+C` để kết thúc thu âm.

---

## 8. Chạy Kiểm Thử Tự Động (Automated Testing)

Dự án cung cấp file kiểm thử `test_api.py` sử dụng thư viện `requests` kiểm tra toàn bộ các trường hợp thành công và các ca biên/validation (file rỗng, sai định dạng).

```bash
python test_api.py
```

Kết quả mong đợi:
```text
=================================================================
     BẮT ĐẦU KIỂM THỬ AUTOMATED API (REQUESTS)
     Target URL: http://127.0.0.1:8000
=================================================================
[1] Kiểm thử GET / ... PASS! [OK]
[2] Kiểm thử GET /health ... PASS! [OK]
[3] Kiểm thử POST /predict với sample1.wav ... PASS! -> Văn bản: '...' (3.94s)
[4] Kiểm thử POST /predict với sample2.wav ... PASS! -> Văn bản: '...' (6.72s)
[5] Kiểm thử Validation lỗi file rỗng ... PASS! [Bắt lỗi đúng: File âm thanh rỗng (0 bytes).]
[6] Kiểm thử Validation định dạng file sai (.txt) ... PASS! [Bắt lỗi đúng: Định dạng file '.txt' không được hỗ trợ.]
=================================================================
🎉 TẤT CẢ 6/6 TEST CASES ĐỀU PASS THÀNH CÔNG RỰC RỠ!
=================================================================
```

---

## 9. Video Báo Cáo & Trình Diễn (Demonstration Video)

- **Link Video Demo (YouTube / Google Drive)**: [Dán link video demo <= 5 phút của bạn vào đây]
- Kịch bản quay video demo hoàn toàn trên Terminal (dưới 5 phút):
  1. **Giới thiệu**: Tên sinh viên, đề tài và mô hình Hugging Face (`hynt/Zipformer-30M-RNNT-Streaming-6000h`).
  2. **Giải thích code**: Giới thiệu nhanh cấu trúc các file (`app.py`, `asr_engine.py`, `stream_mic.py`, `test_api.py`).
  3. **Khởi động server**: Chạy lệnh `uvicorn app:app --reload` trên Terminal 1.
  4. **Kiểm thử API tự động**: Trên Terminal 2, chạy `python test_api.py` để biểu diễn kiểm thử với 2 file mẫu và các case validation. Giải thích kết quả JSON.
  5. **Demo Streaming Microphone**: Trên Terminal 2, chạy `python stream_mic.py`, nói tiếng Việt trực tiếp vào mic và quan sát chữ nhảy theo thời gian thực trên console.
