# AddonProperties.py
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class BakeTypeItem(PropertyGroup):
    use_color = BoolProperty(name="Color", default=False)
    use_normal = BoolProperty(name="Normal", default=False)
    use_emissive = BoolProperty(name="Emissive", default=False)
    use_alpha = BoolProperty(name="Alpha", default=False)

