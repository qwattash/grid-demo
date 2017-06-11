"""
N-dimensional world model with generic helper methods for indexing.
"""

import logging

from itertools import starmap
from enum import IntEnum

import numpy as np

logger = logging.getLogger(__name__)

class Material(IntEnum):
    """World tile material cost."""

    AIR = 0
    WALL = 1


class WorldModelND:
    """
    n-D world model.
    This is the base of the algorithm simulations.
    """

    def __init__(self, shape, grid=None):
        """
        :param shape: n-iterable containing the grid size
        along each direction.
        """

        if (np.array(shape) <= 0).any():
            raise ValueError("Invalid world shape %s", shape)

        self._grid_max = np.array(shape) - 1
        """Maximum coordinates of the grid in every dimension."""

        self._dimension = len(shape)
        """The dimension of the grid."""

        self._grid = None
        """The world grid."""

        if grid is None:
            self._grid = np.zeros(shape)
        else:
            self._grid = grid

    def axes_index(self, *args):
        """
        Return the axis indices in the world grid for the given
        coordinates.

        :param coord_idx: coordinate indices for which the axis index is
        returned. E.g. in a 3D world we have x = (x0, x1, x2), the coordinate
        index for x0 is <0> so axes_index(0) will return the grid axis for
        coordinate x0.
        """
        return self._dimension - 1 - np.array(args)

    @property
    def shape(self):
        """
        Return the shape of the world (number of entries in each dimension).
        """
        return self._grid.shape

    @property
    def gmax(self):
        """
        Return grid maximum coordinates.
        Read-only property.
        """
        return np.array(self._grid_max)

    @property
    def dimension(self):
        """
        Return the number of dimensions of the world.
        Read-only property.
        """
        return self._dimension

    def save(self, handle):
        """
        Save the world model to given file

        :param handle: file handle
        """
        np.save(handle, self._grid)

    @classmethod
    def load(cls, handle):
        """
        Load world from file.

        :param handle: the file handle to use
        """
        grid = np.load(handle)
        world = cls(grid.shape, grid)
        return world

    def _normalize_point_input(self, p):
        """
        Check that the input have the correct dimension and
        return the point as a numpy array.
        """
        if p is None:
            return None
        assert len(p) == self.dimension,\
            "dimension do not match world dim:%d, world:%d" % (
                self.dimension, len(p))
        return np.array(p, dtype=int)

    def _check_rect_ordering(self, p, q):
        """
        Check that two points are suitable to represent an n-d rectangle.
        """
        assert (p <= q).sum() == self.dimension, "q coordinates must be >= p"

    def fill(self, p, q, material):
        """
        Fill a n-d rectangle with given material.

        :param p: bottom "left" vertex (closest to origin)
        :param q: top right vertex
        :param material: the material value to set
        """
        p = self._normalize_point_input(p)
        q = self._normalize_point_input(q)
        self._check_rect_ordering(p, q)
        q = q + 1
        if (self._grid.shape < q).any():
            q = self._grid.shape
        logger.debug("World fill %s %s", p, q)
        coords = np.meshgrid(*starmap(np.arange, zip(p, q)), indexing="ij")
        self._grid[coords] = material

    def point(self, p, material):
        """
        Fill a single point with given material.

        :param p: the point coordinates
        :param material: the material to use
        """
        self.fill(p, p, material)

    def all(self):
        """
        Return a view on the whole world.
        """
        return np.array(self._grid)

    def query(self, p, q=None):
        """
        Query a n-d rectangle.

        :param p: bottom "left" vertex (closest to origin)
        :param q: top right vertex (optional)
        """
        if q is None:
            q = p
        p = self._normalize_point_input(p)
        q = self._normalize_point_input(q)
        self._check_rect_ordering(p, q)
        q = q + 1
        if (self._grid.shape < q).any():
            q = self._grid.shape
        logger.debug("World query %s %s", p, q)
        coords = np.meshgrid(*starmap(np.arange, zip(p, q)), indexing="ij")
        return self._grid[coords]

    def replace(self, p, q, grid):
        """
        Replace grid block.

        :param p: bottom left vertex (closest to origin)
        :param q: top right vertex
        :param grid: replacement block
        """
        p = self._normalize_point_input(p)
        q = self._normalize_point_input(q)
        self._check_rect_ordering(p, q)
        q = q + 1
        logger.debug("World replace %s %s grid:%s", p, q, grid.shape)
        coords = np.meshgrid(*starmap(np.arange, zip(p, q)), indexing="ij")
        self._grid[coords] = grid

    def orthogonal_neighbours(self, p):
        """
        Return coordintates of the adjancent point using 4-connectivity.

        In the n-d case it is not really 4, but orthogonal in general.
        :param p: n-d point
        :return: list of n-d points
        """
        pass

    def diagonal_neighbours(self, p):
        """
        Return coordintates of the adjancent point using 4-connectivity.

        In the n-d case it is not really 4, but orthogonal in general.
        :param p: n-d point
        :return: list of n-d points
        """
        pass


class WorldModel3D(WorldModelND):
    """
    3D world model.
    This is the base of the algorithm simulations
    """

    def __init__(self, w, h, d):
        super().__init__((w, h, d))


class WorldModel2D:
    """
    3D world model.
    This is the base of the algorithm simulations
    """

    def __init__(self, w, h):
        super().__init__((w, h))
