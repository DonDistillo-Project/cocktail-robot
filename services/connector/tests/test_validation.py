from mixing_mode import validate_and_parse_args


def test_mit_fehlendem_rezept_schluessel():
    """Prüft den Fall, dass der Top-Level 'rezept'-Schlüssel fehlt."""
    args_ohne_rezept = {"name": "Wasser", "schritte": []}

    rezept_obj, error_message = validate_and_parse_args(args_ohne_rezept)

    assert rezept_obj is None
    assert error_message is not None
    assert "rezept" in error_message
    assert "Field required" in error_message


def test_mit_fehlendem_schluessel_bei_zutat():
    """Prüft, ob ein fehlendes, erforderliches Feld zu einem Validierungsfehler führt."""
    args = {
        "rezept": {
            "name": "Caipirinha",
            "schritte": [
                {"typ": "zutat", "beschreibung": "Limettenstücke.", "menge": 1, "einheit": "Stück"}
            ],
        }
    }
    rezept_obj, error_message = validate_and_parse_args(args)

    assert rezept_obj is None
    assert error_message is not None
    assert "ZutatSchritt.name" in error_message
    assert "Field required" in error_message


def test_mit_unerlaubtem_feld_bei_anweisung():
    """
    Prüft, ob ein zusätzliches, nicht erlaubtes Feld zu einem Fehler führt.
    """
    args = {
        "rezept": {
            "name": "Gin Tonic",
            "schritte": [{"typ": "anweisung", "beschreibung": "Glas mit Eis füllen.", "menge": 10}],
        }
    }
    rezept_obj, error_message = validate_and_parse_args(args)

    assert rezept_obj is None
    assert error_message is not None
    assert "menge" in error_message
    assert "Extra inputs are not permitted" in error_message


def test_mit_falschem_datentyp():
    """Prüft, ob ein falscher Datentyp (string statt number) erkannt wird."""
    args = {
        "rezept": {
            "name": "Rum Cola",
            "schritte": [
                {
                    "typ": "zutat",
                    "beschreibung": "Rum.",
                    "name": "Rum",
                    "menge": "vier",
                    "einheit": "cl",
                }
            ],
        }
    }
    rezept_obj, error_message = validate_and_parse_args(args)

    assert rezept_obj is None
    assert error_message is not None
    assert "ZutatSchritt.menge" in error_message
    assert "Input should be a valid number" in error_message
