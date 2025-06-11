import json
from openai import OpenAI
from openai.types.responses import ResponseFunctionToolCall
from typing import Literal, NamedTuple, List


class Response(NamedTuple):
    text: str
    function_calls: List[ResponseFunctionToolCall]


class LLM:
    def __init__(self, model="gpt-4.1-mini"):
        self.client = OpenAI()
        self.model = model

        with open("../resources/system_prompt.md", "r", encoding="utf-8") as f:
            self.SYSTEM_PROMPT = f.read()
        system_message = {
            "role": "system",
            "content": self.SYSTEM_PROMPT,
        }
        self.history = [system_message]

        with open("../resources/tools.json", "r", encoding="utf-8") as f:
            self.tools = json.load(f)

    def generate_response(
        self,
        message_content: str = "",
        role: Literal["user", "function_call"] = "user",
    ) -> Response:
        if message_content != "":
            self.history.append(
                {
                    "role": role,
                    "content": message_content,
                }
            )

        response = self.client.responses.create(
            model=self.model,
            input=self.history,
            tools=self.tools,
        )

        self.history.extend(response.output)

        function_calls = []
        for output in response.output:
            if output.type == "function_call":
                function_calls.append(output)

        return Response(text=response.output_text, function_calls=function_calls)

    def add_function_call_output(self, output: str, function_call: ResponseFunctionToolCall):
        self.history.append(
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": output,
            }
        )
