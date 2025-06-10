import json
from typing import List
from llm import LLM


def start_mixing_mode(rezept: List[dict]) -> str:
    # TODO: validate rezept
    info = "Der Nutzer brach das Rezept bei Schritt 2 ab."

    print("Mixe mit Rezept " + str(rezept))

    return info


def handle_function_calls(llm, function_calls):
    for call in function_calls:
        func_name = call.name
        args_str = call.arguments

        if func_name == "start_mixing_mode":
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                print(
                    "Error: Could not parse arguments for function call (not a valid JSON document):\n"
                    + args_str
                )
            else:
                mix_results = start_mixing_mode(args["rezept"])

                llm.return_function_call(mix_results, call)
                response = llm.generate_response()
                print(response.text)

                handle_function_calls(llm, response.function_calls)


def main():
    print("Hello from connector!", flush=True)

    llm = LLM()
    welcome = llm.generate_response()
    print(welcome.text)
    print(" ")

    while True:
        user_input = input("You: ")
        print(" ")

        response = llm.generate_response(user_input)
        print(response.text)
        print(" ")

        handle_function_calls(llm, response.function_calls)


if __name__ == "__main__":
    main()
