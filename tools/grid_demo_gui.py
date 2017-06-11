"""
Pathfinder GUI entry point
"""

import logging

from grid_demo.gui import Window

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.DEBUG)
    Window.mainloop()

if __name__ == "__main__":
    main()


