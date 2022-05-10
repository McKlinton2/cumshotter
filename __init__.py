bl_info = {
    "name": "Cumshotter",
    "author": "McKlinton",
    "version": (1, 0),
    "blender": (3, 1, 0),
    "location": "View3D > Sidebar > Cumshotter",
    "description": "Cumshot generator",
    "warning": "",
    "wiki_url": "https://github.com/McKlinton2/cumshotter",
    "tracker_url": "https://github.com/McKlinton2/cumshotter/issues",
    "category": "3D View"}


import bpy
from . import ui
from . import logic

def register():
    ui.register()

def unregister():
    ui.unregister()

if __name__ == "__main__":
    register()