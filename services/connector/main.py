import json
from typing import Any, Dict, List, Tuple
from llm import LLM


def start_mixing_mode(rezept: List[dict]) -> str:  # TODO:
    info = "Der Nutzer brach das Rezept bei Schritt 2 ab."

    print("Mixe mit Rezept " + str(rezept))

    return info


def validate_mixmode_args(llm_args: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validiert, ob das Rezept-Dict der spezifizierten Struktur entspricht (siehe Wiki für Spezifikation).

    Returns:
        Ein Tupel (bool, str). (True, "") bei Erfolg.
        (False, "Fehlermeldung") bei einem Validierungsfehler.
    """

    if not isinstance(llm_args, dict):
        return False, "Validierungsfehler: Die LLM-Argumente sind kein Dictionary."

    if "rezept" not in llm_args:
        return (
            False,
            "Validierungsfehler: Im Argumente-Dictionary fehlt der erforderliche Schlüssel 'rezept'.",
        )

    if len(llm_args.keys()) > 1:
        extra_keys = set(llm_args.keys()) - {"rezept"}
        return (
            False,
            f"Validierungsfehler: Das Argumente-Dictionary enthält unerlaubte Schlüssel: {extra_keys}.",
        )

    rezept = llm_args["rezept"]

    if not isinstance(rezept, dict):
        return False, "Fehler: Das Rezept ist kein Dictionary."

    required_rezept_keys = {"name", "schritte"}
    if set(rezept.keys()) != required_rezept_keys:
        return (
            False,
            f"Fehler: Das Rezept muss genau die Schlüssel {required_rezept_keys} enthalten.",
        )

    if not isinstance(rezept.get("name"), str) or not rezept.get("name"):
        return False, "Fehler: 'name' muss ein nicht-leerer String sein."
    if not isinstance(rezept.get("schritte"), list):
        return False, "Fehler: 'schritte' muss eine Liste sein."

    for i, schritt in enumerate(rezept["schritte"]):
        schritt_context = f"Bei Schritt {i + 1}: "

        if not isinstance(schritt, dict):
            return False, schritt_context + "Der Schritt ist kein Dictionary."

        required_base_keys = {"typ", "beschreibung"}
        if not required_base_keys.issubset(schritt.keys()):
            missing_keys = required_base_keys - set(schritt.keys())
            return (
                False,
                schritt_context + f"Dem Schritt fehlen erforderliche Schlüssel: {missing_keys}.",
            )

        typ = schritt.get("typ")
        beschreibung = schritt.get("beschreibung")

        if typ not in ["zutat", "anweisung"]:
            return (
                False,
                schritt_context + f"Ungültiger 'typ': '{typ}'. Erlaubt sind 'zutat', 'anweisung'.",
            )

        if not isinstance(beschreibung, str) or not beschreibung:
            return False, schritt_context + "'beschreibung' muss ein nicht-leerer String sein."

        if typ == "zutat":
            required_zutat_keys = {"name", "menge", "einheit"}
            allowed_keys = required_base_keys.union(required_zutat_keys)

            if not required_zutat_keys.issubset(schritt.keys()):
                missing_keys = required_zutat_keys - set(schritt.keys())
                return (
                    False,
                    schritt_context
                    + f"Einer Zutat fehlen erforderliche Schlüssel: {missing_keys}.",
                )

            if set(schritt.keys()) != allowed_keys:
                extra_keys = set(schritt.keys()) - allowed_keys
                return (
                    False,
                    schritt_context + f"Eine Zutat enthält unerlaubte Felder: {extra_keys}.",
                )

            if not isinstance(schritt.get("name"), str) or not schritt.get("name"):
                return (
                    False,
                    schritt_context + "'name' einer Zutat muss ein nicht-leerer String sein.",
                )
            if (
                not isinstance(schritt.get("menge"), (int, float))
                and schritt.get("menge") is not None
            ):
                return (
                    False,
                    schritt_context
                    + f"'menge' ('{schritt.get('menge')}') muss eine Zahl oder null sein.",
                )
            if not isinstance(schritt.get("einheit"), str) and schritt.get("einheit") is not None:
                return (
                    False,
                    schritt_context
                    + f"'einheit' ('{schritt.get('einheit')}') muss ein String oder null sein.",
                )

        elif typ == "anweisung":
            allowed_keys = required_base_keys
            if set(schritt.keys()) != allowed_keys:
                extra_keys = set(schritt.keys()) - allowed_keys
                return (
                    False,
                    schritt_context + f"Eine Anweisung enthält unerlaubte Felder: {extra_keys}.",
                )

    return True, ""


def handle_function_calls(llm, function_calls):
    for call in function_calls:
        func_name = call.name
        args_str = call.arguments

        if func_name == "start_mixing_mode":
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError as e:
                print(
                    "Error: Could not parse arguments for function call (not a valid JSON document):\n"
                    + args_str
                )
                llm.return_function_call(e.msg, call)
                response = llm.generate_response()
                print(response.text)

                handle_function_calls(llm, response.function_calls)
            else:
                is_valid, error_msg = validate_mixmode_args(args)

                if not is_valid:
                    llm.return_function_call(error_msg, call)
                    response = llm.generate_response()
                    print(response.text)

                    handle_function_calls(llm, response.function_calls)
                else:
                    mix_results = start_mixing_mode(args["rezept"])

                    llm.return_function_call(mix_results, call)
                    response = llm.generate_response()
                    print(response.text)

                    handle_function_calls(llm, response.function_calls)


def main():
    div = "------------------------"
    print("Hello from connector!", flush=True)
    print(div)

    llm = LLM()
    welcome = llm.generate_response()
    print(welcome.text)
    print(div)

    while True:
        user_input = input("You: ")
        print(div)

        response = llm.generate_response(user_input)
        print(response.text)
        print(div)

        handle_function_calls(llm, response.function_calls)


if __name__ == "__main__":
    main()
