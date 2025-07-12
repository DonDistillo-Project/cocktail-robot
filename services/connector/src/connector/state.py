from enum import Enum

from openai.types.responses import ResponseFunctionToolCall

from .llm import LLM
from .mixmode_types import Recipe


class Mode(Enum):
    RECIPE_SEARCH = 0
    MIXING = 1


class StateError(RuntimeError):
    """Raised when the application state is invalid for the requested operation."""


class State:
    current_llm: LLM
    current_mode: Mode

    # Only relevant in MIXING state
    current_recipe: Recipe | None = None
    current_step: int = -1
    last_call_to_mixmode: ResponseFunctionToolCall | None = None

    # LLMs for different modes
    _llm_recipe_search: LLM
    _llm_mixing: LLM

    def __init__(self, llm_recipe_search: LLM, llm_mixing: LLM):
        self._llm_recipe_search = llm_recipe_search
        self._llm_mixing = llm_mixing

    def init_recipe_search_mode(self):
        self.current_mode = Mode.RECIPE_SEARCH
        self.current_llm = self._llm_recipe_search

    def init_mixing_mode(self, recipe: Recipe, call: ResponseFunctionToolCall):
        self.current_mode = Mode.MIXING
        self.current_llm = self._llm_mixing

        self.current_recipe = recipe
        self.current_step = 0
        self.last_call_to_mixmode = call
