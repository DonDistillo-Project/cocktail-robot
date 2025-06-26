import asyncio
import logging
from typing import Any, Callable

import numpy as np

DEFAULT_BUF_SIZE = 128

logger = logging.getLogger(__name__)

type BroadcastCallback = Callable[[bytes], Any]


class Node:
    callbacks: set[BroadcastCallback]
    name: str

    def __init__(self, node_name: str) -> None:
        self.name = node_name
        self.callbacks = set()

    def data_received(self, data: bytes) -> None:
        logger.debug(f"{self.name} Received {data} bytes")

        for callback in self.callbacks:
            logger.debug(f"{self.name} Running {callback.__name__}")
            callback(data)

    def add_data_callback(self, callback: BroadcastCallback) -> None:
        logger.debug(f"{self.name} Adding broadcast callback {callback.__name__}")
        self.callbacks.add(callback)


class BroadcastStream(Node, asyncio.Protocol):
    own_transport: asyncio.Transport
    on_conn_lost: asyncio.Future[None]

    def __init__(self, name: str, on_conn_lost: asyncio.Future[None]) -> None:
        self.on_conn_lost = on_conn_lost
        super().__init__(name)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.own_transport = transport  # type: ignore

        peername = self.own_transport.get_extra_info("peername")
        logger.info(f"{self.name} Connection made with {peername}")

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info(f"{self.name} Connection lost")
        self.on_conn_lost.set_result(None)

    def write(self, data: bytes) -> None:
        logger.debug(f"{self.name} Writing {data} bytes")
        self.own_transport.write(data)

    def wait_for_close(self) -> asyncio.Task[None]:
        async def wait_conn_lost(self) -> None:
            await self.on_conn_lost

        return asyncio.create_task(wait_conn_lost(self), name=self.name)


class Gain(Node):
    gain: float

    def __init__(self, gain: float, task_name: str) -> None:
        self.gain = gain
        super().__init__(task_name)

    def data_received(self, data: bytes) -> None:
        return super().data_received(
            (np.frombuffer(data, np.int16) * self.gain).astype(np.int16).tobytes()
        )
