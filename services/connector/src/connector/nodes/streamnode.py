import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

import sounddevice as sd

from .base import Node

logger = logging.getLogger(__name__)


class BroadcastStream[In, Out](Node[In, Out], asyncio.Protocol):
    own_transport: asyncio.Transport
    on_conn_lost: asyncio.Future[bool]
    last_broadcast: datetime = datetime.now()
    stop_flag: bool = False

    input_converter: Callable[[In], bytes]
    output_converter: Callable[[bytes], Out]

    def __init__(
        self,
        name: str,
        on_conn_lost: asyncio.Future[bool],
        in_converter: Callable[[In], bytes] = bytes.__call__,
        out_converter: Callable[[bytes], Out] = lambda x: x,
    ) -> None:
        self.on_conn_lost = on_conn_lost
        self.data_stopped_callbacks = []
        self.input_converter = in_converter
        self.output_converter = out_converter
        super().__init__(name)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.own_transport = transport  # type: ignore

        peername = self.own_transport.get_extra_info("peername")
        logger.info(f"{self.name} Connection made with {peername}")

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info(f"{self.name} Connection lost")
        self.on_conn_lost.set_result(True)

    def handle_input(self, data: In) -> None:
        out_data = self.input_converter(data)
        self._log(f"Writing {len(out_data)} bytes to own transport")
        self.own_transport.write(out_data)

    def data_received(self, data: bytes) -> None:
        self._log(f"Received {len(data)} bytes from own transport")
        out_data = self.output_converter(data)
        self.output(out_data)

    def is_broadcasting(self, delta: timedelta = timedelta(seconds=1)) -> bool:
        return datetime.now() - self.last_broadcast > delta

    def output(self, data: Out):
        self.last_broadcast = datetime.now()
        if not self.stop_flag:
            super().output(data)


class SDStreamNode(Node):
    stream: sd.RawStream

    inqueue: asyncio.Queue[int]
    outqueue: asyncio.Queue[int]

    def __init__(self, name: str) -> None:
        self.inqueue = asyncio.Queue()
        self.outqueue = asyncio.Queue()

        super().__init__(name)

    def data_received(self, data: bytes) -> None:
        logger.info(f"RECEIVED {len(data)}")
        for byte in data:
            self.outqueue.put_nowait(byte)

    def stream_callback(
        self, indata: bytes, outdata: bytes, frames: int, time: Any, status: Any
    ) -> None:
        try:
            indata[:] = bytes(  # type: ignore
                [self.inqueue.get_nowait() for _ in range(len(indata))]
            )
        except asyncio.QueueEmpty:
            logger.debug("Stream inqueue empty")

        try:
            outdata[:] = bytes(  # type: ignore
                [self.outqueue.get_nowait() for _ in range(len(outdata))]
            )
        except asyncio.QueueEmpty:
            logger.debug("Stream outqueue empty")
