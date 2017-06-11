"""
Naive projection algorithms.
"""

import logging
import numpy as np

from grid_demo.world import Material

logger = logging.getLogger(__name__)

class Projection:
    """Projection base class."""

    def projection(self, grid):
        """
        Perform the projection.

        :param grid: the n-d world to project.
        :return: m-d grid with projected values
        """
        raise NotImplementedError("Called abstract projection with %s", grid)


class ProjectMD(Projection):
    """
    N-d grid to M-d projection.
    The only restriction posed by the projector is that m <= n.
    """

    def __init__(self, axes):
        """
        Constructor, initialize the projection given the axes indices.

        :param axes: project on the plane given by the two axes.
        """
        self.axes = np.unique(axes)

    def _get_full_index(self, axes, dimension):
        """
        Return in indexin object for the world with generic
        slices in the correct axes.

        :param axes: the indices on the projection axes.
        :param dimension: the maximum world dimension
        :return: list of index elements
        """
        indexer = [slice(None)] * dimension
        for axis_idx, idx in zip(self.axes, axes):
            indexer[axis_idx] = idx
        return tuple(indexer)

    def projection(self, grid):
        assert len(grid.shape) >= len(self.axes),\
            "Invalid projection source space"
        grid_shape = np.array(grid.shape)
        out_shape = grid_shape[self.axes]
        slice_shape = np.delete(grid_shape, self.axes)
        pgrid = np.zeros(out_shape)
        for idx in np.ndindex(*out_shape):
            full_index = self._get_full_index(idx, len(grid.shape))
            ndslice = np.reshape(grid[full_index], np.prod(slice_shape))
            solid = (ndslice != Material.AIR)
            if solid.any():
                material = ndslice[ndslice != Material.AIR][0]
            else:
                material = Material.AIR
            pgrid[idx] = material
        return pgrid


class Project2D(ProjectMD):
    """
    N-d grid to 2-d projection output.

    This also ensures that if the projected space is 1-d
    the output will be in a 2d space.
    """

    def __init__(self, ax0, ax1):
        super().__init__((ax0, ax1))

    def projection(self, grid):
        pgrid = super().projection(grid)
        if len(pgrid.shape) == 1:
            return np.reshape(pgrid, (pgrid.shape[0], 1))
        return pgrid
