import asyncio
import sys

import pyaudio

ADDR = "localhost"
PORT = 9001

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM
CHUNK_MS = 50  # send ~50ms frames
FRAMES_PER_CHUNK = SAMPLE_RATE * CHUNK_MS // 1000


async def send_mic_audio(writer, stream):
    try:
        while True:
            # PyAudio read is blocking; run it in a thread.
            data = await asyncio.to_thread(
                stream.read, FRAMES_PER_CHUNK, exception_on_overflow=False
            )
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except asyncio.CancelledError:
        pass


async def print_server_text(reader):
    try:
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                break
            sys.stdout.write(chunk.decode(errors="ignore"))
            sys.stdout.flush()
    except asyncio.CancelledError:
        pass


async def main():
    reader, writer = await asyncio.open_connection(ADDR, PORT)

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pa.get_format_from_width(SAMPLE_WIDTH),
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_CHUNK,
    )

    print("Recording… press Ctrl-C to stop.")
    recv_task = asyncio.create_task(print_server_text(reader))
    send_task = asyncio.create_task(send_mic_audio(writer, stream))

    try:
        await asyncio.gather(send_task, recv_task)
    finally:
        for t in (send_task, recv_task):
            t.cancel()
        stream.stop_stream()
        stream.close()
        pa.terminate()
        writer.close()
        await writer.wait_closed()
        print("\nDisconnected.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
