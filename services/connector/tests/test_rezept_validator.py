from main import validate_mixmode_args


def test_mit_gueltigem_rezept():
    valid_cocktail = {
        "name": "Mojito",
        "schritte": [
            {
                "typ": "zutat",
                "beschreibung": "Minzblätter ins Glas geben.",
                "name": "Minze",
                "menge": 10,
                "einheit": "Blätter",
            },
            {"typ": "anweisung", "beschreibung": "Mit einem Stößel leicht andrücken."},
        ],
    }
    is_valid, error_message = validate_mixmode_args(valid_cocktail)
    assert is_valid is True


def test_mit_fehlendem_schluessel_bei_zutat():
    invalid_cocktail = {
        "name": "Caipirinha",
        "schritte": [
            {
                "typ": "zutat",
                "beschreibung": "Limettenstücke ins Glas geben.",
                # "name" fehlt
                "menge": 1,
                "einheit": "Stück",
            }
        ],
    }
    is_valid, error_message = validate_mixmode_args(invalid_cocktail)
    assert is_valid is False
    assert "fehlen erforderliche Schlüssel: {'name'}" in error_message


def test_mit_unerlaubtem_feld_bei_anweisung():
    invalid_cocktail = {
        "name": "Gin Tonic",
        "schritte": [
            {
                "typ": "anweisung",
                "beschreibung": "Glas mit Eis füllen.",
                "menge": 10,  # Unerlaubtes Feld
            }
        ],
    }
    is_valid, error_message = validate_mixmode_args(invalid_cocktail)
    assert is_valid is False
    assert "enthält unerlaubte Felder: {'menge'}" in error_message


def test_ohne_schritte_schluessel():
    rezept_ohne_schritte = {"name": "Wasser"}
    is_valid, error_message = validate_mixmode_args(rezept_ohne_schritte)
    assert is_valid is False
    # print(error_message)
    assert "schritte" in error_message
