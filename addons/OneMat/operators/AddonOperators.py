import bpy

from ..config import __addon_name__
from ..preference.AddonPreferences import ExampleAddonPreferences


# This Example Operator will scale up the selected object

# 基础代码部分
class OneMatOperator(bpy.types.Operator):
    '''一个材质'''
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
    

# 减选Mesh物体操作部分
class OneMat_OT_SelectMesh(bpy.types.Operator):
    '''在当前选择物体中减选Mesh物体'''
    bl_idname = "object.one_mat_select_mesh"
    bl_label = "减选Mesh物体"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.select_set(False)
        return {'FINISHED'}


# 线框模式切换操作部分
class OneMat_OT_ToggleWire(bpy.types.Operator):
    bl_idname = "object.one_mat_toggle_wire"
    bl_label = "线框模式切换"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        wm = context.window_manager
        area = context.area

        if not area or area.type != 'VIEW_3D':
            self.report({'WARNING'}, "请在3D视图中使用")
            return {'CANCELLED'}

        for space in area.spaces:
            if space.type == 'VIEW_3D':
                shading = space.shading

                # 临时属性存储状态
                key_mode = "onemat_prev_shading_type"
                key_xray = "onemat_prev_xray"

                current_mode = shading.type
                current_xray = shading.show_xray

                # 判断是否是目标状态
                is_in_wire = (current_mode == 'WIREFRAME' and current_xray == False)

                if not is_in_wire:
                    # 保存当前状态
                    wm[key_mode] = current_mode
                    wm[key_xray] = current_xray
                    # 切换到 Wireframe + 关闭 X-Ray
                    shading.type = 'WIREFRAME'
                    shading.show_xray = False
                    self.report({'INFO'}, "已切换到线框模式")
                else:
                    # 还原上次状态
                    shading.type = wm.get(key_mode, 'SOLID')
                    shading.show_xray = wm.get(key_xray, True)
                    self.report({'INFO'}, "已恢复上次视图模式")
                break

        return {'FINISHED'}

# 命名第一套UV贴图操作部分
class OBJECT_OT_RenameFirstUVMap(bpy.types.Operator):
    bl_idname = "object.rename_first_uvmap"
    bl_label = "Rename First UVMap"

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj.data.uv_layers:
                obj.data.uv_layers[0].name = "UVMap"
                count += 1
        self.report({'INFO'}, f"已命名 {count} 个对象的第一套 UVMap 为 UVMap")
        return {'FINISHED'} if count > 0 else {'CANCELLED'}


# 删除多余UV贴图操作部分
class OBJECT_OT_RemoveExtraUVMAPS(bpy.types.Operator):
    bl_idname = "object.remove_extra_uvmaps"
    bl_label = "Remove Extra UVMaps"

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                uv_layers = obj.data.uv_layers
                removed = 0
                while len(uv_layers) > 1:
                    uv_layers.remove(uv_layers[-1])
                    removed += 1
                if removed > 0:
                    count += 1
        self.report({'INFO'}, f"已清理 {count} 个对象的多余 UVMap")
        return {'FINISHED'} if count > 0 else {'CANCELLED'}


# 批量创建UV贴图操作部分
class OBJECT_OT_AddUVMapBatch(bpy.types.Operator):
    bl_idname = "object.add_uvmap_batch"
    bl_label = "Batch Add UVMaps"

    def execute(self, context):
        name = context.scene.onemat_uv_name
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.data.uv_layers.new(name=name)
        return {'FINISHED'}

# 检测当前UV贴图操作部分
class OBJECT_OT_CheckCurrentUVMap(bpy.types.Operator):
    bl_idname = "object.check_current_uvmap"
    bl_label = "Check Current UVMap"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            active_uv = obj.data.uv_layers.active.name
            self.report({'INFO'}, f"当前UV贴图：{active_uv}")
            return {'FINISHED'}
        return {'CANCELLED'}

#批量激活部分

# 设置所有选中物体的渲染激活UV
class ONE_MAT_OT_SetRenderUVForSelected(bpy.types.Operator):
    bl_idname = "one_mat.set_render_uv_for_selected"
    bl_label = "设置为渲染UV"
    bl_description = "将当前UV图层设置为所有选中物体的渲染UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        uv_name = context.scene.onemat_uv_name

        for obj in context.selected_objects:
            if not obj or obj.type != 'MESH':
                continue
            o_data = obj.data
            for i, uv in enumerate(o_data.uv_layers):
                if uv.name == uv_name:
                    o_data.uv_layers.active_render_index = i
                    break

        self.report({'INFO'}, f"已将 {uv_name} 设为渲染UV")
        return {'FINISHED'}



# 设置所有选中物体的编辑激活UV
class ONE_MAT_OT_SetActiveUVForSelected(bpy.types.Operator):
    bl_idname = "one_mat.set_active_uv_for_selected"
    bl_label = "设置为编辑UV"
    bl_description = "将当前UV图层设置为所有选中物体的编辑UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        uv_name = context.scene.onemat_uv_name  # 当前UI中选中的UV名称
        
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            
            uv_layers = obj.data.uv_layers
            for i, uv in enumerate(uv_layers):
                if uv.name == uv_name:
                    obj.data.uv_layers.active_index = i
                    break
            else:
                self.report({'WARNING'}, f"{obj.name} 没有 UV 名称为 {uv_name}")
        
        self.report({'INFO'}, f"已将 {uv_name} 设为编辑UV")
        return {'FINISHED'}



