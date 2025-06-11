import json
from typing import Tuple
from openai.types.responses import ResponseFunctionToolCall
from llm import LLM
from mixing_mode import handle_mixmode_call


def dispatch_function_call(function_call: ResponseFunctionToolCall) -> Tuple[bool, str]:
    """
    Returns:
        (True, function call output) if function call was syntactically correct,
        (False, error message) otherwise.
    """
    func_name = function_call.name
    args_str = function_call.arguments

    try:
        args = json.loads(args_str)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Error: Could not parse arguments for function call to '{func_name}':\n {e.msg}",
        )

    if func_name == "start_mixing_mode":
        return handle_mixmode_call(args)
    else:
        return False, f"Function '{func_name}' does not exist"


def main():
    div = "------------------------"
    print("Hello from connector!", flush=True)
    print(div)

    llm = LLM()
    welcome = llm.generate_response()
    print(welcome.text)
    print(div)

    while True:
        user_input = input("User: ")
        print(div)

        response = llm.generate_response(user_input)
        if response.text != "":
            print(f"Don Distillo: {response.text}")
            print(div)

        attempts = 0
        success = False
        while len(response.function_calls) > 0 and not success and attempts < 3:
            function_call = response.function_calls[0]
            success, output = dispatch_function_call(function_call)
            llm.return_function_call_output(output=output, function_call=function_call)
            response = llm.generate_response()
            attempts += 1

        if attempts > 0:
            print(f"Don Distillo: {response.text}")
            print(div)


if __name__ == "__main__":
    main()
