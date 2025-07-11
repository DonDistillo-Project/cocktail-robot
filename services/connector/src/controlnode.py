import asyncio
from enum import Enum
from src.streamnode import Node
from struct import pack, unpack
import logging
from itertools import chain

logger = logging.getLogger(__name__)


NAN = float("nan")


class ESPfIDs(bytes, Enum):
    startRecipe = b"\x00"
    doStep = b"\x01"
    finishRecipe = b"\x02"
    abortRecipe = b"\x03"
    zeroScale = b"\x04"


class PyfIDs(bytes, Enum):
    notifyWeight = b"\x00"


type ESPControlCallbackArgs = tuple[PyfIDs, ...]


class WeightWatcher(Node[ESPControlCallbackArgs, float]):
    weight_history: list[float]
    history_len: int = 5
    tolerance: float = 1.0

    def __init__(
        self, node_name: str, tolerance: float = 1.0, history_len: int = 5
    ) -> None:
        self.weight_history = []
        self.history_len = history_len
        self.tolerance = tolerance
        super().__init__(node_name)

    def check_weight_stable(self) -> float | None:
        if len(self.weight_history) != self.history_len:
            return None

        avg = sum(self.weight_history) / len(self.weight_history)
        if all(abs(w - avg) < self.tolerance for w in self.weight_history):
            return avg

    def handle_input(self, data: tuple[PyfIDs, ...]) -> None:
        id, *args = data
        if id != PyfIDs.notifyWeight and len(args) != 1:
            return

        if isinstance((weight := args[0]), float):
            self.weight_history = [
                w
                for w, _ in zip(
                    chain([weight], self.weight_history), range(self.history_len)
                )
            ]

        if (stable_weight := self.check_weight_stable()) is not None:
            self.output(stable_weight)


class ESPControlNode(Node[bytes, ESPControlCallbackArgs], asyncio.Protocol):
    own_transport: asyncio.Transport
    weight_watcher: WeightWatcher
    on_conn_lost: asyncio.Future[None]
    buf: bytes

    def __init__(
        self,
        name: str,
        on_conn_lost: asyncio.Future[None],
        weight_watcher: WeightWatcher | None,
    ) -> None:
        self.on_conn_lost = on_conn_lost
        self.buf = b""
        if weight_watcher is None:
            weight_watcher = WeightWatcher("ESPWeightWatcher")
        self.weight_watcher = weight_watcher
        self.add_outgoing_node(self.weight_watcher)
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
        delta_target: float,
        instruction: str,
    ) -> None:
        self.write_id(ESPfIDs.doStep)

        if (
            stable_offset := self.weight_watcher.check_weight_stable()
        ) is None:  # If no stable weight: Use esp internal zeroing
            stable_offset = NAN

        self.handle_input(pack("dd", stable_offset, delta_target))
        self.write_str(instruction)

    def doInstructionStep(self, instruction: str):
        self.write_id(ESPfIDs.doStep)
        self.handle_input(pack("dd", NAN, NAN))
        self.write_str(instruction)

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
