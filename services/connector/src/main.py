import json
from typing import Tuple
from openai.types.responses import ResponseFunctionToolCall
from llm import LLM
from mixing_mode import handle_mixing_mode_call

MAX_FUNCTION_CALL_RETRY_ATTEMPTS = 3


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


def main():
    separator = "------------------------"
    print("Hello from connector!", flush=True)
    print(separator)

    llm = LLM()
    welcome_message = llm.generate_response()
    print(welcome_message.text)
    print(separator)

    while True:
        user_input = input("User: ")
        print(separator)

        response = llm.generate_response(user_input)
        if response.text != "":
            print(f"Don Distillo: {response.text}")
            print(separator)

        attempts = 0
        was_successful = False
        while (
            len(response.function_calls) > 0
            and not was_successful
            and attempts < MAX_FUNCTION_CALL_RETRY_ATTEMPTS
        ):
            function_call = response.function_calls[0]
            was_successful, output = dispatch_function_call(function_call)
            llm.add_function_call_output(output=output, function_call=function_call)
            response = llm.generate_response()
            attempts += 1

        if attempts > 0:
            print(f"Don Distillo: {response.text}")
            print(separator)


if __name__ == "__main__":
    main()
