import os

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import AddonPreferences

from ..config import __addon_name__


class ExampleAddonPreferences(AddonPreferences):
    # this must match the add-on name (the folder name of the unzipped file)
    bl_idname = __addon_name__

    # https://docs.blender.org/api/current/bpy.props.html
    # The name can't be dynamically translated during blender programming running as they are defined
    # when the class is registered, i.e. we need to restart blender for the property name to be correctly translated.


    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text="Add-on Preferences View")
        layout.prop(self, "filepath")
        layout.prop(self, "number")
        layout.prop(self, "boolean")
