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
    
# Step01 模型处理面板操作部分
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


# Step02 UV处理面板操作部分
# 命名第一套UV贴图操作部分
class OneMat_OT_RenameFirstUVMap(bpy.types.Operator):
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
class OneMat_OT_RemoveExtraUVMAPS(bpy.types.Operator):
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
class OneMat_OT_AddUVMapBatch(bpy.types.Operator):
    bl_idname = "object.add_uvmap_batch"
    bl_label = "Batch Add UVMaps"

    def execute(self, context):
        name = context.scene.onemat_uv_name
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.data.uv_layers.new(name=name)
        return {'FINISHED'}

# 检测当前UV贴图操作部分
# class OneMat_OT_CheckCurrentUVMap(bpy.types.Operator):
#     bl_idname = "object.check_current_uvmap"
#     bl_label = "Check Current UVMap"

#     def execute(self, context):
#         obj = context.active_object
#         if obj and obj.type == 'MESH':
#             active_uv = obj.data.uv_layers.active.name
#             self.report({'INFO'}, f"当前UV贴图：{active_uv}")
#             return {'FINISHED'}
#         return {'CANCELLED'}

#批量处理UV贴图操作部分

# 设置所有选中物体的编辑激活UV
class OneMat_OT_SetActiveUVForSelected(bpy.types.Operator):
    bl_idname = "one_mat.set_active_uv_for_selected"
    bl_label = "设置为编辑UV"
    bl_description = "将当前UV图层设置为所有选中物体的编辑UV"

    def execute(self, context):
        uv_index = context.scene.onemat_uv_index
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            if uv_index < len(obj.data.uv_layers):
                obj.data.uv_layers.active_index = uv_index
            else:
                self.report({'WARNING'}, f"{obj.name} 没有第 {uv_index} 个UV")
        return {'FINISHED'}

# 设置所有选中物体的渲染激活UV
class OneMat_OT_SetRenderUVForSelected(bpy.types.Operator):
    bl_idname = "one_mat.set_render_uv_for_selected"
    bl_label = "设置为渲染UV"
    bl_description = "将当前UV图层设置为所有选中物体的渲染UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        uv_index = context.scene.onemat_uv_index
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            uv_layers = obj.data.uv_layers
            if uv_index < len(uv_layers):
                # 遍历所有 UV 层，设置渲染 UV
                for i, uv_layer in enumerate(uv_layers):
                    uv_layer.active_render = (i == uv_index)
            else:
                self.report({'WARNING'}, f"{obj.name} 没有第 {uv_index} 个UV")
        return {'FINISHED'}

# 删除指定序号的UV贴图
class OneMat_RemoveUVMapByIndex(bpy.types.Operator):
    bl_idname = "object.remove_uvmap_by_index"
    bl_label = "删除指定序号UV贴图"

    def execute(self, context):
        uv_index = context.scene.onemat_uv_index
        removed_count = 0

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            uv_layers = obj.data.uv_layers
            if uv_index < len(uv_layers):
                uv_layers.remove(uv_layers[uv_index])
                removed_count += 1
            else:
                self.report({'WARNING'}, f"{obj.name} 没有第 {uv_index} 个UV")

        self.report({'INFO'}, f"已从 {removed_count} 个对象中删除第 {uv_index} 个 UV")
        return {'FINISHED' if removed_count > 0 else 'CANCELLED'}


# Step03 材质处理面板操作部分
class OneMat_OT_AddTextureToMaterials(bpy.types.Operator):
    bl_idname = "one_mat.add_texture_to_materials"
    bl_label = "添加图像纹理"
    bl_description = "为选中物体的所有材质添加图像纹理节点"

    def execute(self, context):
        scene = context.scene
        prefix = scene.onemat_image_prefix
        name = scene.onemat_image_name
        suffix = scene.onemat_image_suffix
        width = scene.onemat_image_width
        height = scene.onemat_image_height
        use_alpha = scene.onemat_image_alpha

        # 如果选择的是 Null，则不使用后缀
        image_name = f"{prefix}{name}" if suffix == "Null" else f"{prefix}{name}{suffix}"

        # 如果图像不存在则创建
        if image_name not in bpy.data.images:
            bpy.data.images.new(
                name=image_name,
                width=width,
                height=height,
                alpha=use_alpha,
                float_buffer=False,
            )

        image = bpy.data.images[image_name]

        # 遍历所有选中物体的材质
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # 查找是否已有同名图像节点
                tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name == image_name), None)

                if not tex_node:
                    tex_node = nodes.new(type="ShaderNodeTexImage")
                    tex_node.image = image
                    tex_node.label = image_name
                    tex_node.name = image_name
                    tex_node.location = (-300, 300)

                # 设置为活动纹理节点
                for n in nodes:
                    if hasattr(n, "select"):
                        n.select = False
                tex_node.select = True
                nodes.active = tex_node

        self.report({'INFO'}, f"已添加图像：{image_name}")
        return {'FINISHED'}
    
class ONEMAT_OT_DetectImageTextureNodes(bpy.types.Operator):
    bl_idname = "one_mat.detect_image_texture_nodes"
    bl_label = "检测图像纹理节点"

    def execute(self, context):
        # TODO: 实现节点检测逻辑
        return {'FINISHED'}

class ONEMAT_OT_SetImageNodeActive(bpy.types.Operator):
    bl_idname = "one_mat.set_image_node_active"
    bl_label = "激活所选图像纹理节点"

    def execute(self, context):
        # TODO: 实现激活逻辑
        return {'FINISHED'}

class ONEMAT_OT_RemoveSelectedImageNode(bpy.types.Operator):
    bl_idname = "one_mat.remove_selected_image_node"
    bl_label = "删除所选图像纹理节点"

    def execute(self, context):
        # TODO: 实现删除逻辑
        return {'FINISHED'}
