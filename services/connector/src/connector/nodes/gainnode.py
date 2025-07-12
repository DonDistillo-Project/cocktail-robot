import numpy as np

from .streamnode import Node


class Gain(Node[bytes, bytes]):
    gain: float

    def __init__(self, gain: float, task_name: str) -> None:
        self.gain = gain
        super().__init__(task_name)

    def handle_input(self, data: bytes) -> None:
        adjusted = (np.frombuffer(data, np.int16) * self.gain).astype(np.int16)
        out_bytes = adjusted.tobytes()
        self.output(out_bytes)
