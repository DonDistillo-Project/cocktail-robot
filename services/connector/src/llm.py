import json
from pathlib import Path
from typing import Any, List, NamedTuple, Tuple, Callable, Optional

from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall

from mixmode import handle_mixing_mode_call

OPENAI_MODEL = "gpt-4-mini"
MAX_FUNCTION_CALL_RETRY_ATTEMPTS = 3
RESOURCES_DIR = Path(__file__).parent.parent / "resources"


class Response(NamedTuple):
    text: str
    function_calls: List[ResponseFunctionToolCall]


class StreamingLLM:
    def __init__(self, model=OPENAI_MODEL):
        self.client = OpenAI()
        self.model = model
        self.is_processing = False

        self.stream_callback: Optional[Callable[[str], None]] = None

        system_prompt_path = RESOURCES_DIR / "system_prompt.md"
        tools_json_path = RESOURCES_DIR / "tools.json"

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.SYSTEM_PROMPT = f.read()

        self.history = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            }
        ]

        with open(tools_json_path, "r", encoding="utf-8") as f:
            self.tools = json.load(f)

    def can_process(self) -> bool:
        return not self.is_processing

    def generate_streaming_response(
        self,
        message_content: str = "",
        stream_callback: Callable[[str], Any] = None,
    ) -> Response:
        """
        Generate response with streaming.
        Returns the complete response text.
        """
        if self.is_processing:
            return ""

        self.is_processing = True
        try:
            if message_content:
                self.history.append(
                    {
                        "role": "user",
                        "content": message_content,
                    }
                )

            self.client.responses.with_streaming_response()
            stream = self.client.responses.create(
                model=self.model, messages=self.history, tools=self.tools, stream=True
            )

            for event in stream:
                if event.type == "":  # TODO: whats the text type we're looking for?
                    text_chunk = event  # TODO: how do we get the delta

                    if stream_callback:
                        stream_callback(text_chunk)

            full_response = None  # TODO: the final event from the stream returns the entire response (including function calls and full output text)
            self.history.extend()  # TODO: append to history

            function_calls = []
            for output in full_response.output:
                if output.type == "function_call":
                    function_calls.append(output)

            # TODO: where should the function call be handled?

            return Response(
                text=full_response.output_text, function_calls=full_response.function_calls
            )

        finally:
            self.is_processing = False

    def add_function_call_output(self, output: str, function_call: ResponseFunctionToolCall):
        self.history.append(
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": output,
            }
        )

    @staticmethod
    def dispatch_function_call(function_call: ResponseFunctionToolCall) -> Tuple[bool, str]:
        """
        Dispatches a function call to the appropriate handler.

        Returns:
            (True, function call output) if the function call was syntactically correct and executed.
            (False, error message) otherwise.
        """
        function_name = function_call.name
        arguments_str = function_call.arguments

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            return (
                False,
                f"Error: Could not parse arguments for function call to '{function_name}':\n {e.msg}",
            )

        if function_name == "start_mixing_mode":
            return handle_mixing_mode_call(arguments)
        else:
            return False, f"Function '{function_name}' does not exist"
