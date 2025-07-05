import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Any, List

import numpy as np
from llm import LLM
from mixmode import Recipe, StartMixingArguments, StopMixingArguments
from openai.types.responses import ResponseFunctionToolCall
from pydantic import ValidationError
from src.streamnode import BroadcastStream, FnNode, Node

ESP_HOST = "ESP32"
ESP_ADDR = "192.168.71.16"
ESP_PORT = 1234

STT_ADDR = "localhost"
STT_PORT = 1234
STT_SPRT = 16000

TTS_ADDR = "localhost"
TTS_PORT = 2345
TTS_SPRT = 22500

OPENAI_MODEL = "gpt-4.1-mini"

RESOURCES_DIR = Path(__file__).parent.parent / "resources" / "llm"


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


class Gain(Node[bytes, bytes]):
    gain: float

    def __init__(self, gain: float, task_name: str) -> None:
        self.gain = gain
        super().__init__(task_name)

    def handle_input(self, data: bytes) -> None:
        adjusted = (np.frombuffer(data, np.int16) * self.gain).astype(np.int16)
        out_bytes = adjusted.tobytes()
        self.output(out_bytes)


class MixingEvent(Enum):
    TARGET_WEIGHT_STABLE = 0
    TARGET_WEIGHT_SURPASSED = 1


class Mode(Enum):
    RECIPE_SEARCH = 0
    MIXING = 1


class StateError(RuntimeError):
    """Raised when the application state is invalid for the requested operation."""


class State:
    current_llm: LLM
    current_mode: Mode

    # Only relevant in MIXING state
    current_recipe: Recipe | None = None
    current_step: int = -1
    last_call_to_mixmode: ResponseFunctionToolCall | None = None

    # LLMs for different modes
    _llm_recipe_search: LLM
    _llm_mixing: LLM

    def __init__(self, llm_recipe_search: LLM, llm_mixing: LLM):
        self._llm_recipe_search = llm_recipe_search
        self._llm_mixing = llm_mixing

    def init_recipe_search_mode(self):
        self.current_mode = Mode.RECIPE_SEARCH
        self.current_llm = self._llm_recipe_search

    def init_mixing_mode(self, recipe: Recipe, call: ResponseFunctionToolCall):
        self.current_mode = Mode.MIXING
        self.current_llm = self._llm_mixing

        self.current_recipe = recipe
        self.current_step = 0
        self.last_call_to_mixmode = call


class LLMNode(Node[str | MixingEvent, str]):
    state: State
    sentence_queue: asyncio.Queue[str]
    mixing_event_queue: asyncio.Queue[MixingEvent]

    def __init__(self, name: str):
        super().__init__(name)

        llm_recipe_search = LLM(
            RESOURCES_DIR / "RECIPE_SEARCH" / "system_prompt.md",
            RESOURCES_DIR / "RECIPE_SEARCH" / "tools.json",
            model=OPENAI_MODEL,
        )
        llm_mixing = LLM(
            RESOURCES_DIR / "MIXING" / "system_prompt.md",
            RESOURCES_DIR / "MIXING" / "tools.json",
            model=OPENAI_MODEL,
        )

        self.state = State(llm_recipe_search, llm_mixing)
        self.state.init_recipe_search_mode()

        self.sentence_queue = asyncio.Queue()
        self.mixing_event_queue = asyncio.Queue()

        self.func_call_handler_map = {
            Mode.RECIPE_SEARCH: {
                "start_mixing_mode": self.handle_start_mixing_mode_call,
            },
            Mode.MIXING: {
                "stop_mixing_mode": self.handle_stop_mixing_mode_call,
                "next_recipe_step": self.handle_next_recipe_step_call,
            },
        }

    def input(self, data: str | MixingEvent, sender: Node[Any, str | MixingEvent]) -> None:
        if sender.name == "STT" and isinstance(data, str):
            self._log("Received data from STT")
            self.sentence_queue.put_nowait(data)

        elif sender.name == "scale" and isinstance(data, MixingEvent):
            self._log("Received data from scale")

            if self.state.current_mode == Mode.MIXING:
                self.mixing_event_queue.put_nowait(data)

    def give_mixing_instructions(self) -> None:
        if self.state.current_mode != Mode.MIXING:
            return
        assert self.state.current_recipe is not None  # always set when in Mode.MIXING

        step = self.state.current_recipe.schritte[self.state.current_step]

        self.output(step.beschreibung)  # TTS
        # TODO: setup scale
        # TODO: show instruction on display

    def stop_mixing_mode(self, reason: str) -> None:
        if self.state.current_mode != Mode.MIXING:
            return  # nothing to be done
        assert self.state.last_call_to_mixmode is not None  # always set when in Mode.MIXING

        self.output("DONE")
        self.state._llm_recipe_search.add_function_call_output(
            output=reason,
            function_call=self.state.last_call_to_mixmode,
        )

        self.state.init_recipe_search_mode()

    class StepResult(Enum):
        ADVANCED = "advanced"
        FINISHED = "finished"

    def next_recipe_step(self) -> StepResult:
        if self.state.current_mode != Mode.MIXING:
            msg = "next_recipe_step() was called while not in MIXING mode."
            self._log(msg)
            raise StateError(msg)
        assert self.state.current_recipe is not None

        if self.state.current_step >= len(self.state.current_recipe.schritte):
            self.stop_mixing_mode(reason="Das Rezept wurde erfolgreich zubereitet.")
            return LLMNode.StepResult.FINISHED
        else:
            self.state.current_step += 1
            self.give_mixing_instructions()
            return LLMNode.StepResult.ADVANCED

    def handle_start_mixing_mode_call(self, call: ResponseFunctionToolCall) -> str:
        try:
            args = StartMixingArguments.model_validate_json(call.arguments)
        except ValidationError as e:
            self._log(
                f"Error while parsing or validating function call to '{call.name}': {e}",
                logging.WARNING,
            )
            raise e

        self.state.init_mixing_mode(args.rezept, call)
        self.give_mixing_instructions()

        return "Mixing mode started"

    def handle_stop_mixing_mode_call(self, call: ResponseFunctionToolCall) -> str:
        try:
            args = StopMixingArguments.model_validate_json(call.arguments)
        except ValidationError as e:
            self._log(
                f"Error while parsing or validating function call to '{call.name}': {e}",
                logging.WARNING,
            )
            raise e

        self.stop_mixing_mode(reason=args.grund)

        return "Mixing mode stopped"

    def handle_next_recipe_step_call(self, call: ResponseFunctionToolCall) -> str:
        result = self.next_recipe_step()
        assert self.state.current_recipe is not None

        match result:
            case LLMNode.StepResult.ADVANCED:
                return f"Next step initiated ({self.state.current_step + 1}/{len(self.state.current_recipe.schritte)})"
            case LLMNode.StepResult.FINISHED:
                return "No steps left; recipe now finished."

    def _dispatch_function_calls_recursion(
        self, function_calls: List[ResponseFunctionToolCall], attempts_left: int
    ) -> None:
        if attempts_left == 0:
            return
        attempts_left -= 1

        if len(function_calls) == 0:
            return
        if len(function_calls) > 1:
            self._log(
                f"LLM tried calling multiple functions at once. Only executing the first one ('{function_calls[0].name}') ..."
            )
            for fc in function_calls[1:]:
                self.state.current_llm.add_function_call_output(
                    "Skipped this function call. Please call only one function at a time.", fc
                )

        call = function_calls[0]

        handler_map = self.func_call_handler_map[self.state.current_mode]
        call_handler = handler_map.get(call.name, None)

        if call_handler is None:
            msg = f"LLM tried calling '{call.name}' which doesn't exist (in mode {self.state.current_mode})"
            self._log(msg)

            self.state.current_llm.add_function_call_output(msg, call)

            response = self.state.current_llm.generate_response()
            self._dispatch_function_calls_recursion(response.function_calls, attempts_left)

            return

        self._log(f"LLM made function call to '{call.name}'")
        calling_llm = self.state.current_llm
        try:
            result = call_handler(call)
        except (StateError, ValidationError) as e:
            calling_llm.add_function_call_output(str(e), call)

            if self.state.current_llm != calling_llm:
                return  # don't retry

            response = self.state.current_llm.generate_response()
            self._dispatch_function_calls_recursion(response.function_calls, attempts_left)
        else:
            calling_llm.add_function_call_output(result, call)

    def dispatch_function_calls(
        self, function_calls: List[ResponseFunctionToolCall], max_attempts: int = 3
    ) -> None:
        self._dispatch_function_calls_recursion(function_calls, max_attempts)

    async def await_sentence(self) -> None:
        sentence = await self.sentence_queue.get()

        mode = self.state.current_mode
        self._log(f"Generating {mode.name} mode response for message '{sentence}'")

        llm = self.state.current_llm
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,  # default thread pool
            llm.generate_response,
            sentence,
            self.output,
        )

        self.dispatch_function_calls(response.function_calls)

    async def await_mixing_event(self) -> None:
        event = await self.mixing_event_queue.get()

        if not self.state.current_mode == Mode.MIXING:
            return

        match event:
            case MixingEvent.TARGET_WEIGHT_STABLE:
                self.output("OKAY")
                self.state.current_llm.add_system_message(
                    "User added expected amount of ingredient. Next step ..."
                )
                self.next_recipe_step()

            case MixingEvent.TARGET_WEIGHT_SURPASSED:
                self.output("DU HAST ZU VIEL HINZUGEFÜGT (du bist dumm)")
                self.state.current_llm.add_system_message("User added more than expected.")

    async def loop(self) -> None:
        async def continuous_task(coro_func):
            while True:
                await coro_func()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(continuous_task(self.await_sentence))
            tg.create_task(continuous_task(self.await_mixing_event))


async def async_main():
    loop = asyncio.get_event_loop()

    logger.info("Creating ESP connection")
    on_esp_conn_lost = loop.create_future()
    esp_transport, esp_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, bytes]("ESP", on_esp_conn_lost),
        ESP_ADDR,
        ESP_PORT,
    )

    logger.info("Creating RealtimeSTT connection")
    on_stt_conn_lost = loop.create_future()
    stt_transport, stt_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, str]("STT", on_stt_conn_lost, out_converter=bytes.decode),
        STT_ADDR,
        STT_PORT,
    )

    logger.info("Creating RealtimeTTS connection")
    on_tts_conn_lost = loop.create_future()
    tts_transport, tts_stream = await loop.create_connection(
        lambda: BroadcastStream[str, bytes]("TTS", on_tts_conn_lost),
        TTS_ADDR,
        TTS_PORT,
    )

    llm_node = LLMNode("LLM")

    esp_stream.add_outgoing_node(stt_stream)

    stt_stream.add_outgoing_node(llm_node)
    stt_stream.add_outgoing_node(
        FnNode(
            lambda data: logger.info(f"Received STT Result: {data}"),
            name="Debug FN",
        )
    )

    llm_node.add_outgoing_node(tts_stream)

    gain = Gain(0.5, "ESP:SpeakerGain")
    tts_stream.add_outgoing_node(gain)

    gain.add_outgoing_node(esp_stream)

    pending = [
        on_esp_conn_lost,
        on_stt_conn_lost,
        on_tts_conn_lost,
        asyncio.ensure_future(llm_node.loop()),
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
