import asyncio
from enum import Enum
from src.streamnode import Node
from struct import pack, unpack
import logging

logger = logging.getLogger(__name__)


class ESPfIDs(bytes, Enum):
    startRecipe = b"\x00"
    doStep = b"\x01"
    finishRecipe = b"\x02"
    abortRecipe = b"\x03"
    zeroScale = b"\x04"


class PyfIDs(bytes, Enum):
    notifyWeight = b"\x00"


type ESPControlCallbackArgs = tuple[PyfIDs, ...]


class ESPControlNode(Node[bytes, ESPControlCallbackArgs], asyncio.Protocol):
    own_transport: asyncio.Transport
    on_conn_lost: asyncio.Future[None]
    buf: bytes

    def __init__(self, name: str, on_conn_lost: asyncio.Future[None]) -> None:
        self.on_conn_lost = on_conn_lost
        self.buf = b""
        super().__init__(name)

    def write_id(self, id: ESPfIDs) -> None:
        self.handle_input(id.value)

    def write_str(self, s: str) -> None:
        self.handle_input(len(s).to_bytes())
        self.handle_input(s.encode())

    def startRecipe(self, recipe_name: str) -> None:
        self.write_id(ESPfIDs.startRecipe)
        self.write_str(recipe_name)

    def doIngredientStep(
        self,
        stable_offset: float,
        delta_target: float,
        instruction: str,
        # todo: remove stable_offset
    ) -> None:
        self.write_id(ESPfIDs.doStep)
        self.handle_input(pack("dd", stable_offset, delta_target))
        self.write_str(instruction)

    # todo: implement doInstructionStep for instructions only

    def finishRecipe(self) -> None:
        self.write_id(ESPfIDs.finishRecipe)

    def abortRecipe(self) -> None:
        self.write_id(ESPfIDs.abortRecipe)

    def zeroScale(self) -> None:
        self.write_id(ESPfIDs.zeroScale)

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

    def handle_input(self, data: bytes) -> None:
        self._log(f"Writing {len(data)} bytes ({data}) to own transport")
        self.own_transport.write(data)

    def data_received(self, data: bytes) -> None:
        self._log(f"Received {len(data)} bytes from own transport")
        self.buf += data

        if len(self.buf) >= 9:
            cut = self.buf[:9]
            self.buf = self.buf[9:]

            self.output((PyfIDs(cut[0:1]), *unpack("d", cut[1:9])))
