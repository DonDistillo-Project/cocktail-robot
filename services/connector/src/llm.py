import json
from pathlib import Path
from threading import Lock
from typing import Any, Callable, List, NamedTuple, Optional

from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall, ResponseInputParam


class LLMResponse(NamedTuple):
    text: str
    function_calls: List[ResponseFunctionToolCall]


class LLM:
    def __init__(
        self, system_prompt_path: Path, tools_json_path: Path, model: str = "gpt-4.1-mini"
    ):
        self.client = OpenAI()
        self.model = model
        self.lock = Lock()

        self.stream_callback: Optional[Callable[[str], None]] = None

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.history: ResponseInputParam = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        with open(tools_json_path, "r", encoding="utf-8") as f:
            self.tools = json.load(f)

    def generate_response(
        self,
        message_content: str,
        stream_callback: Callable[[str], Any] | None = None,
    ) -> LLMResponse:
        """
        Generate a response for the message passed.

        If **stream_callback** is passed, it will be called for each part of the output text of the LLM's response.
        Function calls need to be retrieved from the Response object that's returned after the entire response was completed.

        Note: Only one response can be generated at a time. This is ensured internally.
        """

        self.lock.acquire()
        try:
            if message_content:
                self.history.append(
                    {
                        "role": "user",
                        "content": message_content,
                    }
                )

            stream = self.client.responses.create(
                model=self.model, input=self.history, tools=self.tools, stream=True
            )

            complete_response = None
            for event in stream:
                match event.type:
                    case "response.created":
                        if stream_callback:
                            stream_callback(event.response.output_text)

                    case "response.output_text.delta":
                        if stream_callback:
                            stream_callback(event.delta)

                    case "response.completed":
                        complete_response = event.response

            function_calls = []
            assert complete_response is not None
            for item in complete_response.output:
                match item.type:
                    case "message":
                        self.history.append(item)  # type: ignore (this is a bug in the OpenAI library, see: https://github.com/openai/openai-python/issues/2323)
                    case "function_call":
                        self.history.append(item)  # type: ignore
                        function_calls.append(item)

            return LLMResponse(complete_response.output_text, function_calls)

        finally:
            self.lock.release()

    def add_function_call_output(self, output: str, function_call: ResponseFunctionToolCall):
        self.history.append(
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": output,
            }
        )
