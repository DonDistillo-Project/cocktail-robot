from asyncio import sleep
from dis import Instruction
from time import sleep
from typing import Callable
from enum import Enum

from mixmode import *
from streamnode import Node, BroadcastStream

class StatusCode(Enum):
    ABORT = -1
    CONTINUE = 1
    IGNORED = 0

class MixingMode(Node):
    def __init__(self, name: str):
        self.queue = asyncio.Queue()
        self.tts_writer = None
        self.listening_flag = False
        self.interpretation: StatusCode = StatusCode.IGNORED

        super().__init__(name)

    def data_received(self, data):
        if self.listening_flag:
            self.interpretation = StatusCode(llm_interpreter(data))
            if self.interpretation != StatusCode.IGNORED:
                self.listening_flag = False

    def data_send(self, data):
        super().data_received(data)

    def add_tts_connection(self, tts_writer: Callable[[bytes], Any]):
        self.tts_writer = tts_writer

    def start_mixing(self, recipe):
        """
        Args:
            recipe: The validated recipe object.

        Returns:
            A summary of the mixing process.
        """

        # Example: "User aborted at step 2 due to a missing ingredient."
        summary_of_mixing_process = ""

        print("Mixing mode started with recipe:\n" + recipe.name)



        for schritt in recipe.schritte:

            self.interpretation = StatusCode.IGNORED
            self.listening_flag = False

            if isinstance(schritt, InstructionStep):
                self.tts_writer(schritt.beschreibung.encode())

                #ToDo: Display Info

                #listen to stt and interpret
                self.listening_flag = True
                while self.interpretation == StatusCode.IGNORED:
                    asyncio.sleep(1)

                if self.interpretation == StatusCode.CONTINUE:
                    answer = True
                elif self.interpretation == StatusCode.ABORT:
                    answer = False

            elif isinstance(schritt, IngredientStep):
                # ToDO: waage_tarieren()

                self.data_send(schritt.beschreibung.encode())

                #ToDo: Gewicht an Wage zur überprüfung senden
                x = self.handle_ingredient_step(schritt)

            else:
                summary_of_mixing_process += schritt.beschreibung + " not a defined schritt "
                answer = False

            if answer:
                summary_of_mixing_process += schritt.beschreibung + " \n "
                continue
            elif not answer:
                summary_of_mixing_process += schritt.beschreibung + " \n " + "Process cancelled"
                return summary_of_mixing_process

        return

    def handle_ingredient_step(self, schritt):
        print("placeholder")
        return False
