"""
Qt5 GUI interface.
"""

import sys
import enum
import logging

from itertools import starmap, repeat, chain

import numpy as np

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSizePolicy, QGridLayout
from PyQt5.QtWidgets import QGroupBox, QScrollArea
from PyQt5.QtWidgets import QPushButton, QLabel, QSpinBox, QRadioButton
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QTransform
from PyQt5.QtCore import QRect, QLineF
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from grid_demo.world import WorldModelND, Material
from grid_demo.worldmanager import QtWorldManager, WorldManager
from grid_demo.projection import Project2D

logger = logging.getLogger(__name__)

class ViewType(enum.Enum):
    """User interface grid view type."""

    GRID_2D = 1
    MULTIGRID_3D = 2


class Window(QMainWindow):
    """Top level GUI handler."""

    @staticmethod
    def mainloop():
        """Create the main window and enter the qt main loop."""
        app = QApplication(sys.argv)
        w_main = Window()
        w_main.show()
        sys.exit(app.exec_())

    def __init__(self):
        """
        Main window constructor.

        Initialize the layout and connections between signals in
        the widget and the world/algorithm managers.
        """
        super().__init__()

        self.world_mgr = QtWorldManager(WorldModelND((1, 1)))

        self.setWindowTitle("Pathfinder test")
        self.resize(1024, 768)

        self.main = QWidget()
        self.layout = QHBoxLayout(self.main)
        self.setCentralWidget(self.main)

        # build subwidgets
        main_size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        main_size.setHorizontalStretch(6)
        bar_size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        bar_size.setHorizontalStretch(1)

        selector_bar = QWidget()
        bar_layout = QVBoxLayout(selector_bar)
        selector_bar.setSizePolicy(bar_size)
        self.grid = GridView()
        self.grid.setSizePolicy(main_size)

        self.layout.addSpacing(5)
        self.layout.addWidget(self.grid)
        self.layout.addSpacing(5)
        self.layout.addWidget(selector_bar)
        self.layout.addSpacing(5)

        # build bar subwidgets
        self.gui_selector = GuiSelector()
        self.selector = Selector()
        self.build_selector = BuildSelector()
        bar_layout.addWidget(self.build_selector)
        bar_layout.addWidget(self.selector)
        bar_layout.addWidget(self.gui_selector)


        self.selector.grid_shape_selected.connect(self.world_mgr.model_update)
        self.build_selector.material_selected.connect(
            self.world_mgr.select_material)
        self.gui_selector.view_type_selected.connect(
            self.grid.view_type_changed)
        self.gui_selector.view_type_selected.connect(
            self.world_mgr.broadcast_world)
        self.world_mgr.model_changed.connect(self.grid.model_changed)
        self.world_mgr.model_shape_changed.connect(
            self.grid.model_shape_changed)
        self.grid.pick_position.connect(self.world_mgr.pick_position)

        # initialize everything with defaults
        self.gui_selector.reset_default()
        self.selector.reset_default()


class GuiSelector(QWidget):
    """
    Menu selection to set the GridView display variant
    """

    view_type_selected = pyqtSignal(ViewType)
    """Signal emitted when the user selects a GUI grid view type."""

    def __init__(self):
        """
        Build the radio selector widget.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        box = QGroupBox("Viewport type")
        box_layout = QVBoxLayout(box)
        layout.addWidget(box)

        self.radio_2d = QRadioButton("2D Grid")
        self.radio_3d_ortho = QRadioButton("3D Orthogonal Grids")

        box_layout.addWidget(self.radio_2d)
        box_layout.addWidget(self.radio_3d_ortho)

        self.radio_2d.toggled.connect(self._radio2d_toggle)
        self.radio_3d_ortho.toggled.connect(self._radio3dortho_toggle)

    def reset_default(self):
        """Reset the widget to the default state."""
        self.radio_2d.setChecked(True)
        self.radio_3d_ortho.setChecked(False)
        self.view_type_selected.emit(ViewType.GRID_2D)

    def _radio2d_toggle(self, checked):
        """
        Qt toggle event slot for the 2D view radio button.
        """
        if not checked:
            # prevent user from manually deselecting everything
            # self.radio_2d.setChecked(True)
            pass
        else:
            self.radio_3d_ortho.setChecked(False)
            self.view_type_selected.emit(ViewType.GRID_2D)

    def _radio3dortho_toggle(self, checked):
        """
        Qt toggle event slot for the 3D orthogonal view radio button.
        """
        if not checked:
            # prevent user from manually deselecting everything
            # self.radio_3d_ortho.setChecked(True)
            pass
        else:
            self.radio_2d.setChecked(False)
            self.view_type_selected.emit(ViewType.MULTIGRID_3D)


class Selector(QWidget):
    """
    The selector widget handles the grid setup options in the GUI.
    """

    grid_shape_selected = pyqtSignal(tuple)
    """Signal emitted when the user resizes the grid."""

    def __init__(self):
        """
        Selector widget constructor.
        Build the internal layout of the widget and connect signals
        to sub-widgets.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        box = QGroupBox("Grid Settings", self)
        box_layout = QVBoxLayout(box)
        layout.addWidget(box)

        # width and height of grid and labels
        lb_num_dimensions = QLabel("Number of dimensions:")
        self.in_num_dimensions = QSpinBox()
        self.in_num_dimensions.setRange(2, 100)
        box_layout.addWidget(lb_num_dimensions)
        box_layout.addWidget(self.in_num_dimensions)
        self.in_num_dimensions.valueChanged.connect(self._update_dimensions)

        self.dimension_spinbox = []
        self.dimension_list = QWidget()
        self.dimension_list.setLayout(QVBoxLayout())
        scroll = QScrollArea()
        scroll.setWidget(self.dimension_list)
        box_layout.addWidget(self.dimension_list)

        btn_apply_settings = QPushButton("Apply")
        btn_apply_settings.clicked.connect(self._apply_settings)
        box_layout.addSpacing(10)
        box_layout.addWidget(btn_apply_settings)

    def reset_default(self):
        """Reset the widget to the default state."""
        self._update_dimensions(2)
        self.dimension_spinbox[0].setValue(10)
        self.dimension_spinbox[1].setValue(10)
        self.grid_shape_selected.emit((10, 10))

    @pyqtSlot(int)
    def _update_dimensions(self, value):
        """
        Qt slot for updates on the dimension number input box.

        This adds or remove spinners from the dimension listbox.
        """
        curr_dims = len(self.dimension_spinbox)
        if curr_dims > value:
            extra = self.dimension_spinbox[value:]
            for spinbox in extra:
                spinbox.deleteLater()
        elif curr_dims < value:
            layout = self.dimension_list.layout()
            for _ in range(value - curr_dims):
                spinbox = QSpinBox()
                spinbox.setRange(2, 10000000)
                layout.addWidget(spinbox)
                self.dimension_spinbox.append(spinbox)

    def _apply_settings(self, event): # pylint: disable=unused-argument
        """
        Qt click event slot on the settings confirmation button.

        Trigger the grid_update signal.
        """
        new_shape = (spinbox.value() for spinbox in self.dimension_spinbox)
        self.grid_shape_selected.emit(tuple(new_shape))


class BuildSelector(QWidget):
    """
    Widget that handles the building of objects in the world.
    """

    material_selected = pyqtSignal(Material)
    """Signal emitted when the user selects a material to use."""

    def __init__(self):
        """Initialize subwidgets and connect signals."""
        super().__init__()

        layout = QVBoxLayout(self)
        box = QGroupBox("Build tools", self)
        box_layout = QVBoxLayout(box)
        self.tgl_start = QPushButton("Start")
        self.tgl_start.setCheckable(True)
        self.tgl_end = QPushButton("Target")
        self.tgl_end.setCheckable(True)
        self.tgl_wall = QPushButton("Wall")
        self.tgl_wall.setCheckable(True)
        self.tgl_clear = QPushButton("Clear")
        self.tgl_clear.setCheckable(True)
        # append widgets
        self.tgl_start.toggled.connect(self._start_toggle)
        self.tgl_end.toggled.connect(self._end_toggle)
        self.tgl_wall.toggled.connect(self._wall_toggle)
        self.tgl_clear.toggled.connect(self._clear_toggle)
        box_layout.addWidget(self.tgl_start)
        box_layout.addWidget(self.tgl_end)
        box_layout.addWidget(self.tgl_wall)
        box_layout.addWidget(self.tgl_clear)
        layout.addWidget(box)

    def _start_toggle(self, checked):
        """
        Qt toggle event slot on the start location selector button.
        """
        if not checked:
            return
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        # self.grid_item_type.emit(Material.AIR)

    def _end_toggle(self, checked):
        """
        Qt toggle event slot on the end location selector button.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        # self.select_material.emit(Material.AIR)

    def _wall_toggle(self, checked):
        """
        Qt toggle event slot on the WALL material selector button.

        Trigger the select_material signal.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_clear.setChecked(False)
        self.material_selected.emit(Material.WALL)

    def _clear_toggle(self, checked):
        """
        Qt toggle event slot on the AIR material selector button.

        Trigger the select_material signal.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.material_selected.emit(Material.AIR)


class ViewBuilder:
    """
    Base class for strategy objects that build a world representation in
    the grid view.
    """

    def __init__(self, view):
        """Initialize the builder with the parent view."""
        self._view = view

    def destroy(self):
        """
        Deregister all the sub-widgets and destroy everything.
        """
        logger.debug("Destroy view builder %s", self.__class__)

    def redraw(self, manager):
        """
        Redraw the scene with the given world manager.

        :param manager: a WorldManager to use
        """
        logger.debug("Redraw world %s, %s", self.__class__, manager.size)

    def signal_point_selected(self, p):
        """
        Generate a pick-position signal from a display in
        the grid view.

        :param p: point selected
        """
        self._view.pick_position.emit(p)

    def signal_range_selected(self, p, q):
        """
        Generate a pick-region signal from a display in the grid
        view.

        :param p: lowest coordinate corner
        :param q: highest coordinate corner
        """
        pass


class Grid2DViewBuilder(ViewBuilder):
    """
    Show a single 2-d viewport on the world in the grid view.
    """

    vtype = ViewType.GRID_2D

    def __init__(self, view):
        super().__init__(view)

        layout = view.layout()

        self.xy_display = Grid2DDisplay(self)
        layout.addWidget(self.xy_display, 0, 0)

    def destroy(self):
        self.xy_display.deleteLater()
        super().destroy()

    def redraw(self, manager):
        """
        Set the 2-d slice of the world to draw and
        redraw the display.
        """
        super().redraw(manager)
        assert manager.world.dimension >= 2, "Too few dimensions in the world"
        world_grid = manager.world.all()

        # axis indices
        ax0, ax1 = manager.world.axes_index(0, 1)
        xy_plane = Project2D(ax0, ax1)
        self.xy_display.set_world(xy_plane.projection(world_grid))
        self.xy_display.redraw()


class Grid3DOrthogonalViewBuilder(Grid2DViewBuilder):
    """
    Show three 2-d grid viewports on the world in the grid view.

    Each subgrid shows a projection on a pair of axes.
    """

    vtype = ViewType.MULTIGRID_3D

    def __init__(self, view):
        super().__init__(view)

        layout = view.layout()

        self.yz_display = Grid2DDisplay(self)
        self.xz_display = Grid2DDisplay(self)
        layout.addWidget(self.yz_display, 0, 1)
        layout.addWidget(self.xz_display, 1, 0)

    def destroy(self):
        self.yz_display.deleteLater()
        self.xz_display.deleteLater()
        super().destroy()

    def redraw(self, manager):
        super().redraw(manager)
        world_grid = manager.world.all()

        # axis indices
        ax0, ax1, ax2 = manager.world.axes_index(0, 1, 2)
        if manager.world.dimension >= 3:
            yz_plane = Project2D(ax1, ax2)
            xz_plane = Project2D(ax0, ax2)
        else:
            yz_plane = Project2D(ax1, ax1)
            xz_plane = Project2D(ax0, ax0)

        self.yz_display.set_world(yz_plane.projection(world_grid))
        self.xz_display.set_world(xz_plane.projection(world_grid))
        self.yz_display.redraw()
        self.xz_display.redraw()


class Grid2DDisplay(QWidget):
    """
    Simple 2-d grid display with click event handlers.

    Note that this assumes that the world (or subworld)
    that is given to draw have strictly 2 dimensions.
    """

    def __init__(self, builder):
        """
        Initialize brushes and pens, add the display
        viewport to the parent layout.
        """
        super().__init__()

        self.builder = builder
        """World manager."""

        self.current_world = None

        self.background = QBrush(GridView.colors["background"])
        self.grid_pen = QPen(GridView.colors["grid_line"])
        self.wall_brush = QBrush(GridView.colors["wall"])
        self.start_brush = QBrush(GridView.colors["start"])
        self.end_brush = QBrush(GridView.colors["end"])

        self.last_selected_cell = None
        """Coords of the last grid cell selected by the user."""

    def set_world(self, world):
        """
        Set current world grid to draw.

        :param world: a 2-d numpy array of Material values.
        """
        self.current_world = world

    def redraw(self):
        """Redraw the grid."""
        self.repaint()

    def coords2cell(self, x, y):
        """Convert event coordinates to cell coordinates."""
        max_x, max_y = self.current_world.shape
        cell_width = self.width() / max_x
        cell_height = self.height() / max_y
        cell_x = int(x / cell_width)
        cell_y = int(y / cell_height)
        return (cell_x, cell_y)

    def _draw_frame(self, painter):
        """Draw the widget frame box."""
        max_x, max_y = self.current_world.shape
        self.grid_pen.setWidth(0)
        painter.fillRect(0, 0, max_x, max_y, self.background)
        painter.setPen(self.grid_pen)
        painter.drawRect(0, 0, max_x, max_y)

    def _draw_grid(self, painter):
        """Draw the grid lines."""
        max_x, max_y = self.current_world.shape
        x_ticks = np.arange(0, max_x)
        y_ticks = np.arange(0, max_y)
        x_segs = zip(x_ticks, repeat(0), x_ticks, repeat(max_y))
        y_segs = zip(repeat(0), y_ticks, repeat(max_x), y_ticks)
        grid_lines = chain(starmap(QLineF, x_segs), starmap(QLineF, y_segs))
        painter.drawLines(grid_lines)

    def _draw_world(self, painter):
        """Draw the world contents."""
        logger.debug("current world: %s", self.current_world)
        for (x, y), val in np.ndenumerate(self.current_world):
            if val == Material.WALL:
                painter.fillRect(QRect(x, y, 1, 1), self.wall_brush)

    def paintEvent(self, event):
        """Qt paint event slot handler."""
        if self.current_world is None:
            logger.debug("GridView: no world to paint")
            return
        # get the draw rectangle
        rect = event.rect()
        max_x, max_y = self.current_world.shape
        # build the painter and set the coordinates scale
        # transformation + the zoom transform
        painter = QPainter(self)
        transform = QTransform()
        transform.scale((rect.right() - rect.left()) / max_x,
                        (rect.bottom() - rect.top()) / max_y)
        painter.setTransform(transform)

        self._draw_frame(painter)
        self._draw_grid(painter)
        self._draw_world(painter)

    def mouseMoveEvent(self, evt):
        """
        Qt mouse event handler.
        """
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_selected_cell:
            self.last_selected_cell = cell
            self.builder.signal_point_selected(cell)

    def mousePressEvent(self, evt):
        """
        Qt mouse press event handler.
        """
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_selected_cell:
            self.last_selected_cell = cell
            self.builder.signal_point_selected(cell)

    def mouseReleaseEvent(self, evt): # pylint: disable=unused-argument
        """
        Qt mouse release event handler.
        """
        self.last_selected_cell = None


class GridView(QWidget):
    """
    Top level widget for the world grid view region.

    This will have different internal representations depending on the
    world configuration that the user selects.

    Note that if the world have higher dimension,
    the view restricts to the first N usable coordinates.
    If the world have lower dimensionality the remaining M dimensions
    will be latched at 0.
    """

    pick_position = pyqtSignal(tuple)
    """Signal emitted when a position is picked by the user on the grid."""

    colors = {
        "background": QColor(250, 250, 250),
        "grid_line": QColor(40, 40, 40),
        "wall": QColor(100, 100, 100),
        "start": QColor(0, 100, 0),
        "end": QColor(100, 0, 0),
    }

    def __init__(self):
        """
        Top level grid widget constructor.

        Initialize common structure and signal handler that are dispatched
        to sub-widgets.
        """
        super().__init__()

        self.setLayout(QGridLayout())

        self.view_manager = None
        """Display strategy for 2D, 3D and other world sizes."""

    @pyqtSlot(ViewType)
    def view_type_changed(self, vtype):
        """
        Qt signal slot that change the way the world is displayed,
        according to a ViewType.

        :param vtype: the new ViewType to use
        """
        if self.view_manager is None or self.view_manager.vtype != vtype:
            if self.view_manager:
                self.view_manager.destroy()
                self.view_manager = None
            if vtype == ViewType.GRID_2D:
                self.view_manager = Grid2DViewBuilder(self)
            elif vtype == ViewType.MULTIGRID_3D:
                self.view_manager = Grid3DOrthogonalViewBuilder(self)

    @pyqtSlot(WorldManager)
    def model_changed(self, manager):
        """
        Qt signal slot that receives updates from the world manager,
        whenever some position state has changed.
        """
        self.view_manager.redraw(manager)

    @pyqtSlot(WorldManager)
    def model_shape_changed(self, manager):
        """
        Qt signal slot that receives update from the world manager,
        whenever the world is reshaped.
        """
        self.model_changed(manager)
