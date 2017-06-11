from setuptools import setup, find_packages

setup(name="grid-demo",
      version="2.0",
      description="Demo algorithm evaluator on a grid.",
      author="Alfredo Mazzinghi",
      packages=find_packages(),
      entry_points={
          "gui_scripts": [
              "grid-demo-gui=tools.grid_demo_gui:main",
          ]
      })
