import asyncio
import sys

import pyaudio

ADDR = "localhost"
PORT = 9002

SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM


async def play_audio(reader, stream):
    try:
        while True:
            chunk = await reader.read(4096)
            if not chunk:  # server closed
                break
            await asyncio.to_thread(stream.write, chunk)
    except Exception as e:
        print("Playback error:", e)


async def send_input(writer):
    loop = asyncio.get_running_loop()
    try:
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:  # EOF (Ctrl-D)
                break
            line = line.strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit"):
                break
            writer.write(line.encode())
            await writer.drain()
    except KeyboardInterrupt:
        pass


async def main():
    reader, writer = await asyncio.open_connection(ADDR, PORT)

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pa.get_format_from_width(SAMPLE_WIDTH),
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        output=True,
    )

    print("Enter text to speak (Ctrl-D or 'exit' to quit):")

    play_task = asyncio.create_task(play_audio(reader, stream))
    try:
        await send_input(writer)
    finally:
        writer.close()
        await writer.wait_closed()
        play_task.cancel()
        try:
            await play_task
        except asyncio.CancelledError:
            pass
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    asyncio.run(main())
