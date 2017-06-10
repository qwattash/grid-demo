"""
A* algorithm worker.
"""
from threading import Thread


class AStar(Thread):
    """
    XXX the thread and parametrization should be abstracted to
    a generic Algorithm class.

    Plain A* path finding.

    This is the simplest implementation of A* on a N-d grid.
    """

    def __init__(self, world, start, end):
        super().__init__()
        self.world = world
        self.start = start
        self.end = end

        self.v_open = []
        self.v_closed = []

    def run(self):
        pass
