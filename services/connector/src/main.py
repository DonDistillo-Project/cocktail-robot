import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from llm import StreamingLLM
from src.streamnode import BroadcastStream, FnNode, Gain, Node

from connector.src.mixmode import Recipe, validate_and_parse_arguments

ESP_HOST = "ESP32"
ESP_ADDR = "192.168.71.16"
ESP_PORT = 1234

STT_ADDR = "localhost"
STT_PORT = 1234
STT_SPRT = 16000

TTS_ADDR = "localhost"
TTS_PORT = 2345
TTS_SPRT = 22500

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


class MixingEvent(Enum):
    TARGET_WEIGHT_STABLE = 0
    TARGET_WEIGHT_SURPASSED = 1


class Mode(Enum):
    SEARCH = 0
    MIXING = 1


@dataclass
class State:
    current_mode: Mode = Mode.SEARCH

    llm_state_search: StreamingLLM = field(default_factory=StreamingLLM)
    llm_state_mixing: StreamingLLM = field(default_factory=StreamingLLM)

    # Only relevant in mixing state
    current_recipe: Recipe | None = None
    current_step: int = 0


class LLMNode(Node[str | MixingEvent, str]):
    state: State
    sentence_queue: asyncio.Queue[str]
    mixing_event_queue: asyncio.Queue[MixingEvent]

    def __init__(self, name: str):
        super().__init__(name)
        self.state = State()
        self.sentence_queue = asyncio.Queue()
        self.mixing_event_queue = asyncio.Queue()

    def input(self, data: str | MixingEvent, sender: Node[Any, str | MixingEvent]) -> None:
        if sender.name == "stt" and isinstance(data, str):
            self._log("Received data from stt")
            self.sentence_queue.put_nowait(data)

        elif sender.name == "scale" and isinstance(data, MixingEvent):
            self._log("Received data from scale")

            if self.state.current_mode == Mode.MIXING:
                self.mixing_event_queue.put_nowait(data)

    def give_mixing_instructions(self) -> None:
        if self.state.current_recipe is not None:
            self.output(self.state.current_recipe.schritte[self.state.current_step].beschreibung)
        else:
            self.output("KEIN REZEPT VORHANDEN / FERTIG")

    def start_mixing_mode(self, recipe: Recipe) -> None:
        self.state.current_mode = Mode.MIXING

        self.state.current_recipe = recipe
        self.state.current_step = 0

    def stop_mixing_mode(self) -> None:
        self.state.current_mode = Mode.SEARCH

    async def handle_sentence_search(self, sentence: str) -> None:
        self._log(f"Generating search mode response for message {sentence}")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.state.llm_state_search.generate_streaming_response,
            sentence,
            self.output,
        )

        for fc in response.function_calls:
            if fc.name == "start_mixing_mode":
                recipe, error = validate_and_parse_arguments(json.loads(fc.arguments))
                if error is None and recipe is not None:
                    self.start_mixing_mode(recipe)
                else:
                    # TODO: Handle bad fcs
                    self._log(f"Error while validating function call: {error}", logging.WARNING)

    async def handle_sentence_mixing(self, sentence: str) -> None:
        self._log(f"Generating mixing mode response for message {sentence}")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.state.llm_state_mixing.generate_streaming_response,
            sentence,
            self.output,
        )

        for fc in response.function_calls:
            if fc.name == "stop_mixing_mode":
                self.stop_mixing_mode()  # TODO: Think about adding fc parameters
                return

    async def await_sentence(self) -> None:
        sentence = await self.sentence_queue.get()

        match self.state.current_mode:
            case Mode.SEARCH:
                await self.handle_sentence_search(sentence)
            case Mode.MIXING:
                await self.handle_sentence_mixing(sentence)

    async def await_mixing_event(self) -> None:
        event = await self.mixing_event_queue.get()
        if not self.state.current_mode == Mode.MIXING:
            return

        assert self.state.current_recipe is not None

        match event:
            case MixingEvent.TARGET_WEIGHT_STABLE:
                self.output("OKAY")
                if self.state.current_step >= len(self.state.current_recipe.schritte):
                    self.output("DONE")
                    self.stop_mixing_mode()
                else:
                    self.state.current_step += 1
                    self.give_mixing_instructions()
                    # TODO: Set next threshold

            case MixingEvent.TARGET_WEIGHT_SURPASSED:
                self.output("DU HAST ZU VIEL HINZUGEFÜGT (du bist dumm)")

    async def loop(self) -> None:
        futures = [
            asyncio.ensure_future(self.await_sentence()),
            asyncio.ensure_future(self.await_mixing_event()),
        ]
        while True:
            if futures[0].done:
                futures[0] = asyncio.ensure_future(self.await_sentence())
            if futures[1].done:
                futures[1] = asyncio.ensure_future(self.await_mixing_event())

            _ = await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)


async def async_main():
    loop = asyncio.get_event_loop()

    logger.info("Creating ESP connection")
    esp_transport, esp_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, bytes]("ESP", loop.create_future()), ESP_ADDR, ESP_PORT
    )

    logger.info("Creating RealtimeSTT connection")
    stt_transport, stt_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, str](
            "STT", loop.create_future(), out_converter=bytes.decode
        ),
        STT_ADDR,
        STT_PORT,
    )

    logger.info("Creating RealtimeTTS connection")
    tts_transport, tts_stream = await loop.create_connection(
        lambda: BroadcastStream[str, bytes]("TTS", loop.create_future()), TTS_ADDR, TTS_PORT
    )

    llm_stream = LLMNode("LLM")

    esp_stream.add_outgoing_node(stt_stream)

    stt_stream.add_outgoing_node(llm_stream)
    stt_stream.add_outgoing_node(
        FnNode(
            lambda data: logger.info(f"Received STT Result: {data}"),
            name="Debug FN",
        )
    )

    llm_stream.add_outgoing_node(tts_stream)

    gain = Gain(0.5, "ESP:SpeakerGain")
    tts_stream.add_outgoing_node(gain)

    gain.add_outgoing_node(esp_stream)
    pending = [
        esp_stream.wait_for_close(),
        stt_stream.wait_for_close(),
        tts_stream.wait_for_close(),
        asyncio.ensure_future(llm_stream.loop()),
        asyncio.ensure_future(asyncio.to_thread(input, "Press ENTER to exit\n")),
    ]

    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        logger.warning(f"Finished Task(s) {[d.get_name() for d in done]}")

        esp_transport.close()
        stt_transport.close()
        tts_transport.close()


if __name__ == "__main__":
    asyncio.run(async_main())
