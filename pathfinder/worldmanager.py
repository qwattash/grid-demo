"""
World managers act as an interface for the world model from the
various GUI and other possible user interfaces.
"""
import logging
import numpy as np

from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)

from pathfinder.world import Material, WorldModelND

logger = logging.getLogger(__name__)

class WorldManager:
    """
    Base class for the GUI interface to the world.
    """

    def __init__(self, world):
        """
        Base manager constructor.

        :param world: the initial :class:`pathfinder.world.WorldModel`
        """
        super().__init__()
        self.world = world
        self.current_material = Material.AIR

    @property
    def size(self):
        """Shortcut for the world maximum coordinates."""
        return self.world.gmax

    def resize(self, new_shape):
        """
        Try to update the size of the world.
        If the size changes return True.

        :param new_shape: new world shape tuple
        :return: True if the world was replaced
        """
        if (new_shape != self.size).any():
            new_world = WorldModelND(new_shape)
            min_shape = np.minimum(self.size, new_shape)
            zero = np.zeros(len(min_shape))
            common = self.world.query(zero, min_shape)
            if (common.shape != zero).all():
                new_world.replace(zero, min_shape, common)
            self.world = new_world
            return True
        return False

    def set_material(self, material):
        """
        Set the material used to build blocks in the world.

        :param material: the :class:`pathfinder.world.Material` to use
        """
        self.current_material = material

    def build(self, p, q):
        """
        Set a n-d rectangle of the world to the currently selected material.

        :param p: lower-coordinate corner
        :param q: higher-coordinate corner
        """
        self.world.fill(p, q, self.current_material)


class QtWorldManager(WorldManager, QObject):
    """Gui interface for the world manager."""

    model_changed = pyqtSignal(WorldManager)
    """Signal emitted when a cell in the world changes."""

    model_shape_changed = pyqtSignal(WorldManager)
    """
    Signal emitted when the world changes number of
    dimensions or is resized.
    """

    @pyqtSlot(tuple)
    def model_update(self, shape):
        """
        PyQt slot that handles updates to the model shape/size.
        This is used to request a change of dimensions or
        grid limits by a Widget.

        :param shape: n-tuple containing the maximum size
        along each dimension.
        """
        if (shape != self.size).any():
            self.resize(shape)

    @pyqtSlot(Material)
    def select_material(self, material):
        """
        PyQt slot that receives the material selection by Widgets.

        :param material: the :class:`pathfinder.world.Material` selected.
        """
        self.set_material(material)

    @pyqtSlot(tuple)
    def pick_position(self, pos):
        """
        PyQt slot that receives a single point selection. This is
        used by widgets to build an individual voxel.

        :param pos: n-tuple holding the point coordinates
        """
        self.build(np.array(pos), np.array(pos))
        self.model_changed.emit(self)

    def resize(self, new_shape):
        changed = super().resize(new_shape)
        if changed:
            self.model_shape_changed.emit(self)
        return changed
