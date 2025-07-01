from mixing_mode import validate_and_parse_arguments


def test_with_missing_recipe_key():
    """Tests the case where the top-level 'rezept' key is missing."""
    args_without_recipe = {"name": "Wasser", "schritte": []}

    recipe_object, error_message = validate_and_parse_arguments(args_without_recipe)

    assert recipe_object is None
    assert error_message is not None
    assert "rezept" in error_message
    assert "Field required" in error_message


def test_with_missing_key_in_ingredient():
    """Tests if a missing required field in an ingredient leads to a validation error."""
    args = {
        "rezept": {
            "name": "Caipirinha",
            "schritte": [
                {"typ": "zutat", "beschreibung": "Limettenstücke.", "menge": 1, "einheit": "Stück"}
            ],
        }
    }
    recipe_object, error_message = validate_and_parse_arguments(args)

    assert recipe_object is None
    assert error_message is not None
    assert "IngredientStep.name" in error_message
    assert "Field required" in error_message


def test_with_disallowed_field_in_instruction():
    """
    Tests if an additional, not allowed field in an instruction step leads to an error.
    """
    args = {
        "rezept": {
            "name": "Gin Tonic",
            "schritte": [{"typ": "anweisung", "beschreibung": "Glas mit Eis füllen.", "menge": 10}],
        }
    }
    recipe_object, error_message = validate_and_parse_arguments(args)

    assert recipe_object is None
    assert error_message is not None
    assert "menge" in error_message
    assert "Extra inputs are not permitted" in error_message


def test_with_incorrect_data_type():
    """Tests if an incorrect data type (string instead of number) is detected."""
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
    recipe_object, error_message = validate_and_parse_arguments(args)

    assert recipe_object is None
    assert error_message is not None
    assert "IngredientStep.menge" in error_message
    assert "Input should be a valid number" in error_message
