"""
stream_mic.py
Client thu âm từ Microphone thời gian thực và gửi trực tiếp tới WebSocket API của server.
Tích hợp thanh đo âm lượng (Volume Meter) và tự động căn chỉnh vừa vặn chiều rộng màn hình Terminal.
"""

import argparse
import asyncio
import json
import shutil
import sys
import numpy as np
import sounddevice as sd
import websockets

# Dam bao UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SAMPLE_RATE = 16000
BLOCK_SIZE = 3200  # 200 ms moi chunk audio


def make_volume_bar(peak: float, width: int = 10) -> str:
    """Tạo thanh đo âm lượng trực quan chuẩn ASCII không bị lỗi font."""
    filled = min(width, int((peak / 0.15) * width))
    bar = "=" * filled + "-" * (width - filled)
    return bar


async def mic_streaming_client(server_url: str, device: int | None = None):
    print("=" * 70)
    print("   🎙️  CLI STREAMING MICROPHONE TỚI WEBSOCKET API")
    print(f"   Địa chỉ WebSocket : {server_url}")
    dev_info = sd.query_devices(device, kind="input")
    print(f"   Thiết bị Micro    : [{dev_info.get('index', 'Default')}] {dev_info['name']}")
    print("   Nhấn Ctrl+C để dừng thu âm.")
    print("=" * 70)

    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
    volume_state = {"peak": 0.0, "silent_chunks": 0}
    loop = asyncio.get_running_loop()

    def audio_callback(indata, frames, time_info, status):
        peak = float(np.max(np.abs(indata))) / 32768.0
        volume_state["peak"] = peak
        if peak < 0.001:
            volume_state["silent_chunks"] += 1
        else:
            volume_state["silent_chunks"] = 0

        data_bytes = indata.tobytes()
        loop.call_soon_threadsafe(audio_queue.put_nowait, data_bytes)

    full_transcript = ""

    try:
        async with websockets.connect(server_url) as ws:
            print("[Đã kết nối] Đang mở Microphone... Hãy bắt đầu nói tiếng Việt!\n")

            # Task 1: Gửi audio liên tục lên server
            async def sender():
                try:
                    with sd.InputStream(
                        device=device,
                        samplerate=SAMPLE_RATE,
                        channels=1,
                        dtype="int16",
                        blocksize=BLOCK_SIZE,
                        callback=audio_callback,
                    ):
                        while True:
                            chunk_bytes = await audio_queue.get()
                            await ws.send(chunk_bytes)
                except asyncio.CancelledError:
                    pass

            # Task 2: Nhận kết quả và hiển thị gọn gàng trên 1 dòng duy nhất
            async def receiver():
                nonlocal full_transcript
                current_text = "..."
                warned_mute = False

                try:
                    while True:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=0.15)
                            data = json.loads(message)
                            if "text" in data and data["text"]:
                                current_text = data["text"]
                                full_transcript = current_text
                            elif "error" in data:
                                print(f"\n[Lỗi Server]: {data['error']}")
                        except asyncio.TimeoutError:
                            pass

                        # Tính toán độ rộng terminal để không bao giờ bị tràn xuống dòng mới
                        cols = shutil.get_terminal_size((80, 20)).columns
                        bar = make_volume_bar(volume_state["peak"])
                        prefix = f"[Mic: {bar}] [Nhận dạng]: "
                        avail_len = max(10, cols - len(prefix) - 2)

                        # Nếu câu nói dài hơn độ rộng màn hình, hiển thị trượt phần đuôi mới nhất
                        if len(current_text) > avail_len:
                            display_text = "..." + current_text[-(avail_len - 3):]
                        else:
                            display_text = current_text.ljust(avail_len)

                        print(f"\r{prefix}{display_text}", end="", flush=True)

                        # Cảnh báo nếu 20 chunk (~4s) liên tiếp hoàn toàn im lặng
                        if volume_state["silent_chunks"] > 20 and not warned_mute:
                            warned_mute = True
                            print("\n\n⚠️  [LƯU Ý]: Tín hiệu âm lượng Micro đang bằng 0!")
                            print("👉 Kiểm tra phím Mute / Quyền Microphone trong Windows Settings.\n")
                except asyncio.CancelledError:
                    pass

            send_task = asyncio.create_task(sender())
            recv_task = asyncio.create_task(receiver())

            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                if not task.cancelled() and task.exception():
                    raise task.exception()

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"\n[Lỗi]: {exc}")
    finally:
        print("\n\n" + "=" * 70)
        print("   ✅ HOÀN TẤT PHIÊN THU ÂM MICROPHONE")
        if full_transcript:
            print(f"   📝 Văn bản đầy đủ:\n   \"{full_transcript}\"")
        print("=" * 70)


def list_devices():
    """Liệt kê các thiết bị input có sẵn để người dùng chọn nếu cần."""
    print("\nDanh sách thiết bị Microphone trên máy:")
    for idx, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{idx}] {d['name']} (Channels: {d['max_input_channels']})")
    print("\nSử dụng: python stream_mic.py --device <ID_thiet_bi>\n")


def main():
    parser = argparse.ArgumentParser(description="Streaming Microphone to ASR WebSocket API")
    parser.add_argument(
        "--url",
        default="ws://127.0.0.1:8000/ws/stream",
        help="Địa chỉ WebSocket server (mặc định: ws://127.0.0.1:8000/ws/stream)",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Chỉ định ID thiết bị Micro (dùng --list-devices để xem)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Liệt kê danh sách micro trên máy",
    )
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    try:
        asyncio.run(mic_streaming_client(args.url, args.device))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
