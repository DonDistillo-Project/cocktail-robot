import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class Node[In, Out]:
    name: str
    outgoing_nodes: set["Node[Out, Any]"]
    default_logging_level: int = logging.DEBUG

    def __init__(
        self, node_name: str, default_logging_level: int = logging.DEBUG
    ) -> None:
        self.name = node_name
        self.outgoing_nodes = set()
        self.default_logging_level = default_logging_level

    def __str__(self) -> str:
        return self.name

    def _log(
        self,
        message: str,
        level: int = default_logging_level,
        log_format="N:{self.name}: {message}",
    ) -> None:
        logger.log(level, log_format.format_map(locals()))

    def add_outgoing_node(self, other: "Node[Any, Any]") -> None:
        """
        Add an outgoing connection to another node.

        The other node's input type must be compatible with this node's
        output type. This means if this node outputs type Out, the other
        node must accept Out (possibly as part of a Union).
        """

        self.outgoing_nodes.add(other)

    def input(self, data: In, sender: "Node[Any, In]") -> None:
        self._log(f"Received data from {sender}")
        self.handle_input(data)

    def output(self, data: Out) -> None:
        for node in self.outgoing_nodes:
            self._log(f"Running callback for node {node}")
            node.input(data, self)

    def handle_input(self, data: In) -> None: ...


class FnNode[In, Out](Node[In, Out]):
    fn: Callable[[In], None]

    def __init__(self, fn: Callable[[In], None], *args, **kwargs) -> None:
        self.fn = fn

        super().__init__(kwargs["name"])

    def handle_input(self, data: In) -> None:
        self.fn(data)
