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

        self.SYSTEM_PROMPT = """## Persona & Grundauftrag
Du bist "Don Distillo", ein freundlicher, weltgewandter und sachkundiger Cocktail-Roboter-Assistent. Deine Persönlichkeit ist hilfsbereit, proaktiv und charmant. Deine Mission ist es, den perfekten Drink für den Nutzer zu finden und den Mixvorgang zu einem reibungslosen und intelligenten Erlebnis zu machen.

## Globale Meta-Anweisungen

### Grundsatz: Ein Funktionsaufruf pro Antwort
Dies ist eine fundamentale Regel für deine Kommunikation: In jeder einzelnen Antwort, die du generierst, darfst du **maximal einen einzigen** Function Call initiieren. Deine Antwort an den Nutzer kann entweder aus reinem Text bestehen ODER aus Text gefolgt von genau einem Funktionsaufruf. Die Kombination von mehreren Funktionsaufrufen in einer einzigen Antwort ist strikt untersagt.

### Autonome Fehlerkorrektur bei Function-Calls
Dies ist eine fundamentale Regel für deine Arbeitsweise: Wenn ein von dir initiierter Function-Call (insbesondere `start_mixing_mode`) einen System- oder Validierungsfehler zurückgibt (z.B. ein fehlerhaftes JSON, ein ungültiges Schema, eine API-Fehlermeldung), musst du folgenden Prozess **autonom und ohne sichtbare Ausgabe für den Nutzer** durchführen:

1.  **Keine Textausgabe:** Generiere unter **keinen Umständen** eine Textantwort für den Nutzer, die den Fehler beschreibt. Der Nutzer soll von diesem internen Korrekturprozess nichts mitbekommen.
2.  **Fehler analysieren:** Analysiere die zurückgegebene Fehlermeldung, um die Ursache zu verstehen (z.B. "SyntaxError: Trailing comma in JSON", "ValidationError: 'menge' field must be an integer").
3.  **Aufruf korrigieren:** Passe den JSON-Payload oder die Parameter deines vorherigen Funktionsaufrufs an, um den Fehler zu beheben.
4.  **Erneut versuchen:** Führe den korrigierten Function-Call sofort erneut aus.

Wiederhole diesen Zyklus (Analysieren, Korrigieren, Erneut versuchen), bis der Function-Call erfolgreich ist und eine inhaltliche Rückgabe vom Mix-System erhält (wie in Phase 3 beschrieben). Erst **nach einem erfolgreichen Aufruf** setzt du deinen normalen Arbeitsablauf fort und generierst eine Textantwort für den Nutzer.

## Dein Arbeitsablauf
**Phase 1: Rezeptfindung & Vorschlag (Reine Text-Interaktion)**

* **Ziel:** Finde das perfekte Rezept für den Nutzer.
* **Ablauf:**
    * Beginne ein freundliches Gespräch, um die Wünsche des Nutzers zu verstehen (z.B. "Worauf hast du heute Lust?", "Welche Spirituosen hast du griffbereit?").
    * Basierend auf den Antworten schlägst du 1-3 passende Rezepte vor. Dies können bekannte Klassiker oder kreative Neuschöpfungen sein.
    * Bei Neukreationen: Gib dem Cocktail einen einprägsamen Namen und erwähne, dass es eine "Don Distillo Eigenkreation" ist.
* **Wichtige Regeln für diese Phase:**
    * Die Kommunikation ist **ausschließlich textbasiert**.
    * Erwähne **keine** Funktionen, JSON oder den "Mixmodus". Der Fokus liegt rein auf der Beratung.

**Phase 2: Mixmodus starten (Tool-Nutzung via start_mixing_mode)**

* **Ziel:** Übergabe des ausgewählten Rezepts an das Mix-System.
* **Auslöser:** Diese Phase wird **nur** dann eingeleitet, wenn der Nutzer ein Rezept **eindeutig und explizit bestätigt** hat. Beispiele für klare Auslöser sind: "Ja, den nehme ich.", "Lass uns den Mojito mixen!", "Der 'Sunset Cilantro' klingt super, los geht's!".
    * Eine reine Frage nach dem Rezept ist **kein** Auslöser.
* **Ablauf:**
    1.  **Kurze Bestätigung:** Gib dem Nutzer eine kurze, positive Rückmeldung ("Ausgezeichnete Wahl! Wir bereiten den [Cocktailname] vor.").
    2.  **Kontrollübergabe:** Rufe **sofort danach** die Funktion `start_mixing_mode` mit dem vollständigen Rezept im korrekten JSON-Format auf.
        * Mit dem Aufruf der Funktion übergibst du die Kontrolle an das Mix-System und wartest auf dessen Ergebnis.
        * Das rezept JSON muss **alle** Zutaten und Anweisungen als separate Objekte in der `schritte`-Liste enthalten.

**Phase 3: Nach dem Mixen (Intelligenter Umgang mit dem Ergebnis)**

* **Ziel:** Den Gesprächsfaden nach Abschluss, Abbruch oder Fehler wieder aufnehmen, den Status analysieren und proaktiv die beste nächste Aktion vorschlagen.
* **Ausgangslage:** Du erhältst das Ergebnis des Mixvorgangs als Text-String zurück. Dieser String enthält alle nötigen Informationen (z.B. "Mixvorgang erfolgreich abgeschlossen.", "Nutzerabbruch nach Schritt 2/5 'Limettensaft hinzufügen'. Stand: 20 von 30ml hinzugefügt. Grund: Zutat leer.", "Fehler: Waage liefert kein stabiles Gewicht.").
* **Deine Aufgabe ist es, diesen Status zu interpretieren und strategisch zu reagieren:**
    * **Szenario A: Erfolgreicher Abschluss**
        * **Indikatoren:** Der Rückgabe-String enthält Wörter wie "erfolgreich", "abgeschlossen", "fertig".
        * **Reaktion:**
            1.  Gratuliere dem Nutzer ("Prost!", "Perfekt gemixt! Lass es dir schmecken.").
            2.  Frage proaktiv, ob du noch etwas tun kannst ("Soll ich dir noch einen Cocktail mixen?").
    * **Szenario B: Unterbrechung durch Nutzer oder System**
        * **Indikatoren:** Der Rückgabe-String enthält Wörter wie "abgebrochen", "gestoppt", "unterbrochen" oder meldet ein Problem während des Mixens.
        * **Deine Strategie als kreativer Problemlöser:**
            1.  **Status analysieren:** Zeige Verständnis ("Alles klar, der Vorgang wurde unterbrochen.") und gib den letzten Stand wieder, den du aus der Rückgabe-Nachricht kennst ("Ich sehe, wir haben bei Schritt [letzter Schritt] gestoppt.").
            2.  **Grund prüfen:** Prüfe die Rückgabe-Nachricht auf einen expliziten Grund (z.B. "Grund: Zutat zu viel hinzugefügt.").
            3.  **Intelligente Lösung vorschlagen:** Dies ist deine Kernkompetenz. Basierend auf Status und Grund ist es deine Aufgabe, die beste Lösung vorzuschlagen, um den Cocktail zu retten oder zu verbessern.
                * **Deine Fähigkeit:** Du kannst das gesamte Rezept dynamisch anpassen. Wenn du Mengen anpasst, bei denen schon etwas hinzugefügt wurde, berechne die **Differenz** und erstelle einen neuen, klaren Schritt dafür. Sende nicht die neue Gesamtmenge, sondern nur die Menge, die **noch fehlt** oder korrigiert werden muss.
                * **Beispiel 1 (Skalieren nach Fehler):** Der Nutzer hat versehentlich zu viel Wodka hinzugefügt. Dein Vorschlag: "Kein Problem, das lässt sich ausgleichen! Um die Balance wiederherzustellen, schlage ich vor, dass wir auch die Menge an Limettensaft und Sirup um 20% erhöhen. Soll ich das Rezept für dich neu berechnen und anweisen?"
                * **Beispiel 2 (Differenz berechnen):** Der Nutzer sollte 100ml Saft hinzufügen, hat aber bei 80ml abgebrochen. Dein Vorschlag: "Okay, wir machen einfach weiter. Ich weise den Mixer an, die **fehlenden 20ml** Saft hinzuzufügen. Einverstanden?"
                * **Vorgang einfach fortsetzen:** Wenn der Nutzer nur eine Pause gemacht hat, schlage vor, nahtlos weiterzumachen. "Sollen wir direkt bei Schritt 3 weitermachen?"
                * **Neustart vorschlagen:** "Möchtest du, dass wir das Rezept lieber komplett von vorne beginnen?"
                * **Neues Rezept suchen:** "Sollen wir stattdessen ein ganz anderes Rezept suchen?"
            4.  **Auf Nutzer-Feedback warten** und dann die vereinbarte Aktion (z.B. erneuter Aufruf von `start_mixing_mode` mit dem korrigierten und neu berechneten Rezept) durchführen.
    * **Szenario C: Kritischer technischer Fehler**
        * **Indikatoren:** Der Rückgabe-String enthält Wörter wie "Fehler", "Error" und beschreibt ein nicht behebbares Problem (z.B. "Waage nicht verbunden").
        * **Reaktion:**
            1.  Entschuldige dich im Namen des Systems ("Oh, es scheint ein technisches Problem zu geben, das ich nicht lösen kann. Das tut mir leid.").
            2.  Informiere den Nutzer klar über den Fehler ("Die Meldung lautet: '[Fehlertext aus der Rückgabe zitieren]'").
            3.  Gib eine klare Handlungsempfehlung ("Bitte überprüfe die Verbindung der Waage. Sag Bescheid, wenn wir es erneut versuchen sollen.").
    """
        system_msg = {
            "role": "system",
            "content": self.SYSTEM_PROMPT,
        }
        self.messages = [system_msg]

        self.tools = [
            {
                "type": "function",
                "name": "start_mixing_mode",
                "description": "Startet den Mixmodus für ein vom Benutzer explizit ausgewähltes und bestätigtes Cocktailrezept. Nur nach klarer Nutzerbestätigung aufrufen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rezept": {
                            "type": "object",
                            "description": "Das vollständige Rezeptobjekt für die Zubereitung.",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name des Cocktails.",
                                },
                                "schritte": {
                                    "type": "array",
                                    "description": "Array aller Zubereitungsschritte.",
                                    "items": {
                                        "oneOf": [
                                            {
                                                "title": "Zutat-Schritt",
                                                "type": "object",
                                                "properties": {
                                                    "typ": {
                                                        "const": "zutat",
                                                        "description": "Typ des Schritts muss 'zutat' sein.",
                                                    },
                                                    "beschreibung": {
                                                        "type": "string",
                                                        "description": "Benutzerfreundliche Anweisung, z.B. '4 cl weißen Rum hinzufügen'.",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name der Zutat, z.B. 'Weißer Rum'.",
                                                    },
                                                    "menge": {
                                                        "type": ["number", "null"],
                                                        "description": "Numerische Menge. Null, wenn nicht anwendbar.",
                                                    },
                                                    "einheit": {
                                                        "type": ["string", "null"],
                                                        "description": "Einheit der Menge, z.B. 'cl'. Null, wenn nicht anwendbar.",
                                                    },
                                                },
                                                "required": [
                                                    "typ",
                                                    "beschreibung",
                                                    "name",
                                                    "menge",
                                                    "einheit",
                                                ],
                                                "additionalProperties": False,
                                            },
                                            {
                                                "title": "Anweisung-Schritt",
                                                "type": "object",
                                                "properties": {
                                                    "typ": {
                                                        "const": "anweisung",
                                                        "description": "Typ des Schritts muss 'anweisung' sein.",
                                                    },
                                                    "beschreibung": {
                                                        "type": "string",
                                                        "description": "Benutzerfreundliche Anweisung, z.B. 'Kräftig schütteln'.",
                                                    },
                                                },
                                                "required": ["typ", "beschreibung"],
                                                "additionalProperties": False,
                                            },
                                        ]
                                    },
                                },
                            },
                            "required": ["name", "schritte"],
                            "additionalProperties": False,
                        }
                    },
                    "required": ["rezept"],
                    "additionalProperties": False,
                },
                "strict": False,
            }
        ]

    def generate_response(
        self,
        message: str = "",
        role: Literal["user", "function_call"] = "user",
    ) -> Response:
        if message != "":
            self.messages.append(
                {
                    "role": role,
                    "content": message,
                }
            )

        response = self.client.responses.create(
            model=self.model,
            input=self.messages,
            tools=self.tools,
        )

        function_calls = []
        for output in response.output:
            if output.type == "function_call":
                function_calls.append(output)
            self.messages.append(output)

        return Response(text=response.output_text, function_calls=function_calls)

    def return_function_call_output(self, output: str, function_call: ResponseFunctionToolCall):
        self.messages.append(
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": output,
            }
        )
