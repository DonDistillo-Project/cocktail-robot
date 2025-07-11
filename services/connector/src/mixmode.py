from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class InstructionStep(BaseModel):
    """A general instruction, e.g., 'Kräftig schütteln'."""

    typ: Literal["anweisung"]
    beschreibung: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class IngredientStep(BaseModel):
    """An instruction that entails a certain ingredient being added."""

    typ: Literal["zutat"]
    beschreibung: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    menge: Optional[int | float] = None  # Allows int, float, and None
    einheit: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


Step = Union[IngredientStep, InstructionStep]


class Recipe(BaseModel):
    name: str = Field(..., min_length=1)
    schritte: list[Step] = Field(..., min_length=1)


class StartMixingArguments(BaseModel):
    rezept: Recipe

    model_config = ConfigDict(extra="forbid")


class StopMixingArguments(BaseModel):
    grund: str

    model_config = ConfigDict(extra="forbid")
