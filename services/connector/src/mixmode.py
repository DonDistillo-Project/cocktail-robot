from typing import Any, Dict, List, Tuple, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, ValidationError


class InstructionStep(BaseModel):
    """A general instruction, e.g., 'Kräftig schütteln'."""

    typ: Literal["anweisung"]
    beschreibung: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class IngredientStep(BaseModel):
    """The addition of a specific ingredient."""

    typ: Literal["zutat"]
    beschreibung: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    menge: Optional[float] = None  # Allows int, float, and None
    einheit: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


Step = Union[IngredientStep, InstructionStep]


class Recipe(BaseModel):
    """Represents a recipe with a name and a list of steps."""

    name: str = Field(..., min_length=1)
    schritte: List[Step] = Field(..., min_length=1)


class LLMArguments(BaseModel):
    """Represents the top-level arguments structure from the LLM."""

    rezept: Recipe

    model_config = ConfigDict(extra="forbid")


def validate_and_parse_arguments(args: Dict[str, Any]) -> Tuple[Recipe | None, str | None]:
    """
    Validates the arguments with Pydantic and creates the Recipe object on success.

    Returns:
        A tuple (Recipe object, None) on success.
        A tuple (None, "error message") on a validation error.
    """
    try:
        parsed_args = LLMArguments.model_validate(args)
        return parsed_args.rezept, None
    except ValidationError as e:
        return None, f"Error: args for 'start_mixing_mode' do not meet specification: {e}"


def handle_mixing_mode_call(args: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Handles the 'start_mixing_mode' function call from the LLM.

    Returns:
        A tuple (True, results) on successful validation and execution.
        A tuple (False, error message) on failure.
    """
    recipe, error_message = validate_and_parse_arguments(args)

    if not recipe:
        return False, str(error_message)

    mixing_results = start_mixing_mode(recipe)
    return True, mixing_results


def start_mixing_mode(recipe: Recipe) -> str:
    """
    Args:
        recipe: The validated recipe object.

    Returns:
        A summary of the mixing process.
    """
    # Example: "User aborted at step 2 due to a missing ingredient."
    summary_of_mixing_process = ""

    print("Mixing mode started with recipe:\n" + str(recipe))

    return summary_of_mixing_process
