from typing import Any, Dict, List, Tuple, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, ValidationError


class AnweisungSchritt(BaseModel):
    """Eine allgemeine Anweisung, z.B. 'Kräftig schütteln'."""

    typ: Literal["anweisung"]
    beschreibung: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class ZutatSchritt(BaseModel):
    """Das Hinzufügen einer spezifischen Zutat."""

    typ: Literal["zutat"]
    beschreibung: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    menge: Optional[float] = None  # Erlaubt int, float und None
    einheit: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


Schritt = Union[ZutatSchritt, AnweisungSchritt]


class Rezept(BaseModel):
    name: str = Field(..., min_length=1)
    schritte: List[Schritt] = Field(..., min_length=1)


class LLMArgs(BaseModel):
    rezept: Rezept

    model_config = ConfigDict(extra="forbid")


def validate_and_parse_args(args: Dict[str, Any]) -> Tuple[Rezept | None, str | None]:
    """
    Validiert die Argumente mit Pydantic und erstellt bei Erfolg das Rezept-Objekt.

    Returns:
        Tupel (Rezept-Objekt, None) bei Erfolg.
        Tupel (None, "Fehlermeldung") bei einem Validierungsfehler.
    """
    try:
        parsed_args = LLMArgs.model_validate(args)
        return parsed_args.rezept, None
    except ValidationError as e:
        return None, f"Error: args for 'start_mixing_mode' do not meet specification: {e}"


def handle_mixmode_call(args) -> Tuple[bool, str]:
    rezept, error_msg = validate_and_parse_args(args)

    if not rezept:
        return False, str(error_msg)

    mix_results = start_mixing_mode(rezept)
    return True, mix_results


def start_mixing_mode(rezept: Rezept) -> str:
    info = ""  # Beispiel: "User brach wegen fehlender Zutat bei Schritt 2 ab."

    print("Mixmodus gestartet mit Rezept:\n" + str(rezept))

    return info
