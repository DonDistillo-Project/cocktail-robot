import asyncio
import logging
from typing import Any, Callable
from abc import ABC, abstractmethod
import numpy as np

DEFAULT_BUF_SIZE = 128

logger = logging.getLogger(__name__)


class Node[In, Out]:
    outgoing_nodes: set["Node[Out, Any]"]

    name: str

    def __init__(self, node_name: str) -> None:
        self.name = node_name
        self.outgoing_nodes = set()

    def __str__(self) -> str:
        return self.name

    def _log(
        self,
        message: str,
        level: int = logging.DEBUG,
        log_format="N:{self.name}: {message}",
    ) -> None:
        logger.log(level, log_format.format_map(locals()))

    def add_outgoing_node(self, other: "Node[Out,Any]") -> None:
        self.outgoing_nodes.add(other)

    def input(self, data: In, sender: "Node[Any,In]") -> None:
        self._log(f"Received data from {sender}")
        self.handle_input(data)

    def output(self, data: Out) -> None:
        for node in self.outgoing_nodes:
            self._log(f"Running callback for node {node}")
            node.input(data, self)

    def handle_input(self, data: In) -> None: ...


class FnNode[In, Out](Node[In, Out]):
    fn: Callable[[In], None]

    def __init__(self, fn: Callable[[In], None], *args, **kwargs) -> None:
        self.fn = fn

        super().__init__(*args, **kwargs)

    def handle_input(self, data: In) -> None:
        self.fn(data)


class BroadcastStream[In, Out](Node[In, Out], asyncio.Protocol):
    own_transport: asyncio.Transport
    on_conn_lost: asyncio.Future[None]

    input_converter: Callable[[In], bytes]
    output_converter: Callable[[bytes], Out]

    def __init__(
        self,
        name: str,
        on_conn_lost: asyncio.Future[None],
        in_converter: Callable[[In], bytes] = bytes.__call__,
        out_converter: Callable[[bytes], Out] = lambda x: x,
    ) -> None:
        self.on_conn_lost = on_conn_lost
        super().__init__(name)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.own_transport = transport  # type: ignore

        peername = self.own_transport.get_extra_info("peername")
        logger.info(f"{self.name} Connection made with {peername}")

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info(f"{self.name} Connection lost")
        self.on_conn_lost.set_result(None)

    def wait_for_close(self) -> asyncio.Task[None]:
        async def wait_conn_lost(self) -> None:
            await self.on_conn_lost

        return asyncio.create_task(wait_conn_lost(self), name=self.name)

    def handle_input(self, data: In) -> None:
        out_data = self.input_converter(data)
        self._log(f"Writing {len(out_data)} bytes to own transport")
        self.own_transport.write(out_data)

    def data_received(self, data: bytes) -> None:
        self._log(f"Received {len(data)} bytes from own transport")
        out_data = self.output_converter(data)
        self.output(out_data)


class Gain(Node[bytes, bytes]):
    gain: float

    def __init__(self, gain: float, task_name: str) -> None:
        self.gain = gain
        super().__init__(task_name)

    def handle_input(self, data: bytes) -> None:
        adjusted = (np.frombuffer(data, np.int16) * self.gain).astype(np.int16)
        out_bytes = adjusted.tobytes()
        self.output(out_bytes)
