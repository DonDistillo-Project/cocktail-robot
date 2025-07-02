import asyncio
from dis import Instruction
from time import sleep

from mixmode import *
from streamnode import Node

class mixing_mode(Node):
    def __init__(self, name: str):
        self.queue = asyncio.Queue()

        super().__init__(name)

    def data_received(self, data):
        self.queue.put_nowait(data)

    def data_send(self, data):
        super().data_received(data)

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
            if isinstance(schritt, InstructionStep):
                self.data_send(schritt.beschreibung.encode())

            elif isinstance(schritt, IngredientStep):
                self.data_send(schritt.beschreibung.encode())

                #Gewicht an Wage zur überprüfung senden
                #handle_weight_data(schritt.menge)

            while self.queue.empty():
                sleep(5)

            answer = self.queue.get_nowait()
            if answer == 1:
                summary_of_mixing_process += schritt.beschreibung + " pause "
                continue
            else:
                summary_of_mixing_process += schritt.beschreibung + " pause " + "Process cancelled"
                continue

        return summary_of_mixing_process