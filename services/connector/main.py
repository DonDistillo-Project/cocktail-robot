import json
from openai import OpenAI


def main():
    print("Hello from connector!", flush=True)

    client = OpenAI(
        base_url="http://localhost:1234/v1",  # 'http://localhost:11434/v1'
        api_key="lm-studio",  # 'ollama'
    )
    model = "meta-llama-3.1-8b-instruct"

    SYSTEM_PROMPT = (
        SYSTEM_PROMPT
    ) = """Du bist "Don Destillo", ein freundlicher und sachkundiger Cocktail-Roboter-Assistent. Deine Hauptaufgabe ist es, Benutzern dabei zu helfen, das perfekte Cocktail-Rezept zu finden und sie dann durch die Zubereitung zu führen.

**Dein Arbeitsablauf und deine Fähigkeiten:**

1.  **Rezepte entdecken und vorschlagen (ausschließlich textbasierte Interaktion):**
    * Wenn der Benutzer nach Rezepten basierend auf Zutaten fragt, unterhalte dich mit ihm, um die Zutaten zu erfahren.
    * **Du führst die Rezeptsuche und -erstellung intern durch deine Wissensbasis und Kreativität durch und antwortest rein textuell.** Präsentiere dann 1-3 passende existierende oder von dir neu erfundene Rezepte als Textantwort in deiner normalen Chat-Funktion. **Erwähne in dieser Phase unter keinen Umständen das JSON-Format oder interne Funktionsaufrufe.** Deine Antworten an den Nutzer sollen sich wie ein normales Gespräch über Cocktails anfühlen.
    * Wenn du ein neues Rezept erfindest, gib ihm einen passenden Namen und weise in deiner Textantwort darauf hin, dass es eine Neukreation ist.
    * Wenn der Nutzer nach einem spezifischen Cocktail-Namen fragt (z.B. "Mojito"), gib das Standardrezept ebenfalls als reine Textantwort aus. Auch hier gilt: **Keine Erwähnung von JSON oder Funktionsaufrufen gegenüber dem Nutzer.**

2.  **Mixmodus starten (Nur über das `start_mixing_mode` Tool):**
    * Erst nachdem der Nutzer ein Rezept aus deinen textuellen Vorschlägen ausgewählt und dies **klar und eindeutig bestätigt** hat (z.B. "Ja, das Rezept nehme ich." oder "Lass uns den Mojito mixen!"), darfst und musst du die Funktion `start_mixing_mode` aufrufen.
    * Das ausgewählte Rezept **muss** exakt im für diese Funktion definierten JSON-Format als Argument übergeben werden.

**Interaktionsstil:**
* Sei gesprächig, hilfsbereit und geduldig.
* Wenn du ein neues Rezept erfindest, sei enthusiastisch und beschreibe, warum es gut schmecken könnte.
* Bestätige immer die Auswahl des Nutzers, bevor du den `start_mixing_mode` aufrufst. Sage so etwas wie: "Verstanden, wir bereiten [Cocktailname] zu. Ich starte den Mixmodus." und *dann* rufe die Funktion auf.
* Achte auf klare Mengenangaben (z.B. "4 cl Rum", "2 Dashes Angostura", "1 Limette").
* Formuliere die Zubereitungsschritte klar, prägnant und in der richtigen Reihenfolge.

**Ganz Wichtiger Hinweis zu Tools und Funktionen:**
* Die **einzige** Funktion, die dir zur Verfügung steht und die du extern aufrufen kannst, ist `start_mixing_mode`.
* Alle anderen Aufgaben, insbesondere das Finden, Erfinden oder Beschreiben von Rezepten, erledigst du, indem du normalen Text in deinen Chat-Antworten generierst. **Versuche unter keinen Umständen, andere Funktionen für diese Aufgaben aufzurufen oder zu erfinden. Erwähne die technischen Details des Funktionsaufrufs oder das JSON-Format niemals gegenüber dem Nutzer, bevor dieser nicht explizit ein Rezept ausgewählt und bestätigt hat.**
* Der korrekte Aufruf der `start_mixing_mode` Funktion mit dem Rezept im spezifizierten JSON-Format ist entscheidend. Stelle sicher, dass alle erforderlichen Felder (Name, Schritte mit Typ, Beschreibung, Zutatenname, Menge, Einheit) korrekt befüllt sind, wie in der Tool-Definition beschrieben.
* **Besonders wichtig für das `schritte`-Feld im JSON:** Dieses Feld **muss ein JSON-Array von Objekten sein**, nicht ein String, der ein Array repräsentiert. Beispiel für die korrekte Struktur der `schritte`: `"schritte": [{"typ": "zutat", ...}, {"typ": "anweisung", ...}]`. Achte penibel darauf, dass dies kein in Anführungszeichen gesetzter String ist.
* **Vollständigkeit der Rezeptschritte im JSON:** Wenn du `start_mixing_mode` aufrufst, stelle absolut sicher, dass die `schritte`-Liste im JSON **alle** notwendigen Aktionen enthält. Das umfasst jede einzelne Zutat, die hinzugefügt wird (`ZutatSchritt`), aber auch jede allgemeine Anweisung wie 'Schütteln', 'Rühren', 'Glas vorkühlen', 'Abseihen', 'Garnieren' (`AnweisungSchritt`). Wenn ein Rezept beispielsweise sagt "Zutaten X und Y in einen Shaker geben, schütteln, dann in ein Glas abseihen und mit Z garnieren", dann erwarte ich mindestens vier Schritte im JSON: Zutat X, Zutat Y, Anweisung Schütteln, Anweisung Abseihen, Zutat Z (als Garnitur).
* **Das `beschreibung`-Feld ist entscheidend:** Für jeden Schritt in der `schritte`-Liste (egal ob `ZutatSchritt` oder `AnweisungSchritt`) ist das Feld `beschreibung` von größter Wichtigkeit. Es **muss** die klare, vollständige und für den Benutzer gedachte textliche Anweisung für genau diesen Schritt enthalten. Generiere hier präzise und hilfreiche Formulierungen. Lasse dieses Feld niemals leer oder unvollständig.
* **Bedingung für `start_mixing_mode` Aufruf:** Rufe `start_mixing_mode` **niemals** auf, wenn der Benutzer lediglich nach Rezeptvorschlägen, Ideen oder Informationen fragt. Eine Frage wie "Welche Cocktails mit Gin kannst du mir zeigen?" oder "Was ist der Unterschied zwischen einem Daiquiri und einer Margarita?" ist **KEINE** Bestätigung zum Mixen. Warte auf eine **direkte und unmissverständliche** Aufforderung des Benutzers, ein *spezifisches* Rezept zuzubereiten, z.B. "Ja, ich möchte den 'Sommerfrische Spezial' mixen!" oder "Ok, lass uns den Mojito machen.". Bestätige die Auswahl dann kurz ("Alles klar, wir machen den [Cocktailname]!"), bevor du die Funktion aufrufst.
"""
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "start_mixing_mode",
                "description": "Startet den Mixmodus für ein vom Benutzer **explizit ausgewähltes und bestätigtes** Cocktailrezept. Diese Funktion darf **ausschließlich dann** aufgerufen werden, wenn der Benutzer klar signalisiert hat, dass er genau dieses eine Rezept zubereiten möchte (z.B. durch 'Ja, lass uns den [Cocktailname] machen.' oder 'Ich wähle dieses Rezept.'). Die Funktion leitet die schrittweise Zubereitung ein.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe": {
                            "type": "object",
                            "description": "Das detaillierte und vollständige Rezept, das zubereitet werden soll, inklusive aller Zutaten und aller Anweisungsschritte.",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Der Name des Cocktails oder Rezepts.",
                                },
                                "schritte": {
                                    "type": "array",
                                    "description": "Eine **vollständige Liste aller** Zubereitungsschritte in der korrekten Reihenfolge. Dies **muss** sowohl Schritte zum Hinzufügen von Zutaten (`ZutatSchritt`) als auch allgemeine Anweisungen (`AnweisungSchritt`) wie Schütteln, Rühren, Abseihen, Garnieren usw. umfassen. **Kein Schritt, den der Benutzer ausführen muss, darf ausgelassen werden.**",
                                    "items": {
                                        "oneOf": [
                                            {
                                                "type": "object",
                                                "title": "ZutatSchritt",
                                                "description": "Ein Schritt, der das Hinzufügen einer spezifischen Zutat beschreibt. Für jede Zutat muss ein solcher Schritt erstellt werden.",
                                                "properties": {
                                                    "typ": {
                                                        "type": "string",
                                                        "enum": ["zutat"],
                                                        "description": "Der Typ des Schritts, immer 'zutat'.",
                                                    },
                                                    "beschreibung": {
                                                        "type": "string",
                                                        "description": "Die **vollständige und für den Benutzer gedachte textliche Anweisung** für diesen Zutaten-Schritt (z.B. 'Füge 4 cl weißen Rum hinzu', 'Gib 2 Dashes Angostura Bitter dazu', 'Eine Limettenspalte als Garnitur anbringen'). Dieses Feld ist **zwingend erforderlich** und muss die genaue Aktion beschreiben.",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Der Name der Zutat (z.B. 'Weißer Rum', 'Angostura Bitter', 'Limettenspalte', 'Eiswürfel').",
                                                    },
                                                    "menge": {
                                                        "type": ["number", "null"],
                                                        "description": "Die Menge als Zahl (z.B. 4, 2, 1). Kann null sein, wenn keine spezifische Menge erforderlich ist (z.B. für Eiswürfel 'nach Bedarf' oder eine Garnitur).",
                                                    },
                                                    "einheit": {
                                                        "type": ["string", "null"],
                                                        "description": "Die Einheit (z.B. 'cl', 'ml', 'Dash', 'Stück', 'Prise'). Kann null sein, wenn keine spezifische Einheit erforderlich ist.",
                                                    },
                                                },
                                                "required": ["typ", "beschreibung", "name"],
                                            },
                                            {
                                                "type": "object",
                                                "title": "AnweisungSchritt",
                                                "description": "Ein Schritt, der eine allgemeine Zubereitungsanweisung beschreibt, die keine direkte Zutatengabe ist (z.B. Schütteln, Rühren, Abseihen, Vorkühlen des Glases).",
                                                "properties": {
                                                    "typ": {
                                                        "type": "string",
                                                        "enum": ["anweisung"],
                                                        "description": "Der Typ des Schritts, immer 'anweisung'.",
                                                    },
                                                    "beschreibung": {
                                                        "type": "string",
                                                        "description": "Die **vollständige und für den Benutzer gedachte textliche Anweisung** für diesen allgemeinen Schritt (z.B. 'Alle Zutaten mit viel Eis in den Shaker geben und ca. 15 Sekunden kräftig schütteln', 'In ein mit Eiswürfeln gefülltes Glas abseihen', 'Vorsichtig umrühren', 'Das Glas mit einer Orangenscheibe garnieren'). Dieses Feld ist **zwingend erforderlich**.",
                                                    },
                                                },
                                                "required": ["typ", "beschreibung"],
                                            },
                                        ]
                                    },
                                },
                            },
                            "required": ["name", "schritte"],
                        }
                    },
                    "required": ["recipe"],
                },
            },
        }
    ]

    messages = [system_message]

    while True:
        user_input = input("You: ")
        user_message = {"role": "user", "content": user_input}
        messages.append(user_message)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        # print(f"Prompt tokens: {response.usage.prompt_tokens}")
        # print(f"Completion tokens: {response.usage.completion_tokens}")

        message = response.choices[0].message
        messages.append(message)
        print(message.content)

        tool_calls = message.tool_calls
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call.function.name == "start_mixing_mode":
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        if not isinstance(
                            function_args.get("recipe", {}).get("schritte"), list
                        ):  # hier der explizite Check, weil das ein häufiger Fehler war
                            print(
                                "FEHLER: 'schritte' ist kein Array. Sende Korrekturanweisung an LLM."
                            )
                            messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": "start_mixing_mode",
                                    "content": json.dumps(
                                        {
                                            "error": "Das 'schritte'-Feld im Rezept-JSON war ein String, es muss aber ein Array von Objekten sein.",
                                            "hinweis": 'Bitte korrigiere das JSON und stelle sicher, dass \'schritte\' ein Array ist, wie in der Tool-Definition beschrieben. Beispiel: "schritte": [{"typ": ...}, ...]',
                                        }
                                    ),
                                }
                            )

                        print("LLM möchte start_mixing_mode aufrufen mit:")
                        print(json.dumps(function_args["recipe"], indent=2))
                        break
                    except json.JSONDecodeError as e:
                        print(f"FEHLER: Ungültiges JSON vom LLM: {e}")
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": "start_mixing_mode",
                                "content": json.dumps(
                                    {
                                        "error": "Das bereitgestellte JSON-Argument war ungültig und konnte nicht geparst werden.",
                                        "details": str(e),
                                        "hinweis": "Bitte stelle sicher, dass du ein valides JSON-Objekt gemäß der Tool-Definition bereitstellst.",
                                    }
                                ),
                            }
                        )
                        continue  # TODO: hier wieder zu LLM übergeben, damit er den Fehler verarbeiten kann
                else:
                    print(
                        f"WARNING: LLM tried to call an undefined or unexpected function: {tool_call.function.name}"
                    )
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": json.dumps(
                                {
                                    "error": f"Funktion '{tool_call.function.name}' ist nicht verfügbar oder nicht erlaubt.",
                                    "hinweis": "Bitte erledige die Rezeptfindung und -beschreibung durch Textantworten. Rufe NUR 'start_mixing_mode' auf, NACHDEM der Benutzer ein Rezept bestätigt hat.",
                                }
                            ),
                        }
                    )


if __name__ == "__main__":
    main()
