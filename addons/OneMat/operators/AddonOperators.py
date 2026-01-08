import bpy

from ..config import __addon_name__
from ..preference.AddonPreferences import ExampleAddonPreferences


# This Example Operator will scale up the selected object
class OneMatOperator(bpy.types.Operator):
    '''ExampleAddon'''
    # 操作的唯一标识符，用于找到和调用操作
    bl_idname = "object.one_mat_operator"
    bl_label = "OneMatOperator"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    # 操作的前提条件
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    # 执行操作的方法
    def execute(self, context: bpy.types.Context):
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, ExampleAddonPreferences)
        # use operator
        # bpy.ops.transform.resize(value=(2, 2, 2))

        # manipulate the scale directly
        # context.active_object.scale *= addon_prefs.number
        context.active_object.location.x += addon_prefs.number
        return {'FINISHED'}
