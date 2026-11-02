"""
test_api.py
Script kiểm thử tự động các endpoint của Web API bằng thư viện `requests`.
Đáp ứng yêu cầu Mục 4 của Đề bài: "At least one Python file for testing the API using the requests library."

Cách chạy:
    1. Khởi động server trong 1 terminal: uvicorn app:app --reload
    2. Chạy test trong terminal thứ 2: python test_api.py
"""

from pathlib import Path
import sys
import requests

BASE_URL = "http://127.0.0.1:8000"
SAMPLES_DIR = Path(__file__).parent / "samples"


def test_root_endpoint():
    """1. Kiểm thử GET /: Giới thiệu hệ thống."""
    print("[1] Kiểm thử GET / ...", end=" ")
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200, f"Mong đợi 200, nhận được {res.status_code}"
    data = res.json()
    assert "model_name" in data, "Thiếu trường 'model_name' trong JSON"
    assert "endpoints" in data, "Thiếu trường 'endpoints' trong JSON"
    print("PASS! [OK]")


def test_health_endpoint():
    """2. Kiểm thử GET /health: Trạng thái hệ thống."""
    print("[2] Kiểm thử GET /health ...", end=" ")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Mong đợi 200, nhận được {res.status_code}"
    data = res.json()
    assert data.get("status") == "healthy", f"Hệ thống không healthy: {data}"
    assert data.get("model_loaded") is True, "Mô hình chưa được nạp"
    print("PASS! [OK]")


def test_predict_sample1():
    """3. Kiểm thử POST /predict với sample1.wav hợp lệ."""
    sample1_path = SAMPLES_DIR / "sample1.wav"
    print(f"[3] Kiểm thử POST /predict với {sample1_path.name} ...", end=" ")
    assert sample1_path.exists(), f"Không tìm thấy file mẫu: {sample1_path}"

    with open(sample1_path, "rb") as f:
        files = {"file": (sample1_path.name, f, "audio/wav")}
        res = requests.post(f"{BASE_URL}/predict", files=files)

    assert res.status_code == 200, f"Mong đợi 200, nhận được {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("success") is True, "Response không báo success=True"
    assert "text" in data and len(data["text"]) > 0, "Không nhận dạng được văn bản"
    assert data.get("duration_seconds", 0) > 0, "Thời lượng âm thanh không hợp lệ"
    print(f"PASS! -> Văn bản: '{data['text']}' ({data['duration_seconds']}s)")


def test_predict_sample2():
    """4. Kiểm thử POST /predict với sample2.wav hợp lệ (Input thứ 2)."""
    sample2_path = SAMPLES_DIR / "sample2.wav"
    print(f"[4] Kiểm thử POST /predict với {sample2_path.name} ...", end=" ")
    assert sample2_path.exists(), f"Không tìm thấy file mẫu: {sample2_path}"

    with open(sample2_path, "rb") as f:
        files = {"file": (sample2_path.name, f, "audio/wav")}
        res = requests.post(f"{BASE_URL}/predict", files=files)

    assert res.status_code == 200, f"Mong đợi 200, nhận được {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("success") is True
    print(f"PASS! -> Văn bản: '{data['text']}' ({data['duration_seconds']}s)")


def test_predict_empty_file_validation():
    """5. Kiểm thử Validation: Gửi file rỗng (0 bytes) -> Phải trả về lỗi 400 Bad Request."""
    print("[5] Kiểm thử Validation lỗi file rỗng ...", end=" ")
    empty_content = b""
    files = {"file": ("empty.wav", empty_content, "audio/wav")}
    res = requests.post(f"{BASE_URL}/predict", files=files)

    assert res.status_code == 400, f"Mong đợi lỗi 400, nhưng nhận được {res.status_code}"
    print(f"PASS! [Bắt lỗi đúng: {res.json().get('detail')}]")


def test_predict_invalid_extension():
    """6. Kiểm thử Validation: Gửi file không phải định dạng audio (.txt) -> Phải trả về lỗi 400."""
    print("[6] Kiểm thử Validation định dạng file sai (.txt) ...", end=" ")
    fake_txt = b"Day khong phai la file audio"
    files = {"file": ("document.txt", fake_txt, "text/plain")}
    res = requests.post(f"{BASE_URL}/predict", files=files)

    assert res.status_code == 400, f"Mong đợi lỗi 400, nhưng nhận được {res.status_code}"
    print(f"PASS! [Bắt lỗi đúng: {res.json().get('detail')}]")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 65)
    print("     BẮT ĐẦU KIỂM THỬ AUTOMATED API (REQUESTS)")
    print(f"     Target URL: {BASE_URL}")
    print("=" * 65)

    try:
        test_root_endpoint()
        test_health_endpoint()
        test_predict_sample1()
        test_predict_sample2()
        test_predict_empty_file_validation()
        test_predict_invalid_extension()
        print("=" * 65)
        print("🎉 TẤT CẢ 6/6 TEST CASES ĐỀU PASS THÀNH CÔNG RỰC RỠ!")
        print("=" * 65)
    except AssertionError as err:
        print(f"\n❌ TEST THẤT BẠI: {err}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ KHÔNG THỂ KẾT NỐI ĐẾN {BASE_URL}.")
        print("Vui lòng khởi động server bằng lệnh trước: uvicorn app:app --reload")
        sys.exit(1)


if __name__ == "__main__":
    main()
