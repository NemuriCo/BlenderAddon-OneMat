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

# 图像纹理节点管理 
class ONEMAT_OT_DetectImageTextureNodes(bpy.types.Operator):
    bl_idname = "one_mat.detect_image_texture_nodes"
    bl_label = "检测图像纹理节点"

    def execute(self, context):
        scene = context.scene
        scene.onemat_image_nodes.clear()

        image_names = set()

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes:
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            image_names.add(node.image.name)

        for name in sorted(image_names):
            item = scene.onemat_image_nodes.add()
            item.name = name

        scene.onemat_image_node_index = 0
        self.report({'INFO'}, f"找到 {len(image_names)} 个图像纹理节点")
        return {'FINISHED'}

class ONEMAT_OT_SetImageNodeActive(bpy.types.Operator):
    bl_idname = "one_mat.set_image_node_active"
    bl_label = "激活所选图像纹理节点"

    def execute(self, context):
        scene = context.scene
        if scene.onemat_image_node_index >= len(scene.onemat_image_nodes):
            self.report({'WARNING'}, "未选择图像纹理节点")
            return {'CANCELLED'}

        selected_name = scene.onemat_image_nodes[scene.onemat_image_node_index].name

        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes:
                    nodes = mat.node_tree.nodes
                    tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name == selected_name), None)
                    if tex_node:
                        for n in nodes:
                            if hasattr(n, "select"):
                                n.select = False
                        tex_node.select = True
                        nodes.active = tex_node
                        count += 1

        self.report({'INFO'}, f"已设为活动节点：{selected_name}（{count} 个材质）")
        return {'FINISHED'}

class ONEMAT_OT_RemoveSelectedImageNode(bpy.types.Operator):
    bl_idname = "one_mat.remove_selected_image_node"
    bl_label = "删除所选图像纹理节点"

    def execute(self, context):
        scene = context.scene
        if scene.onemat_image_node_index >= len(scene.onemat_image_nodes):
            self.report({'WARNING'}, "未选择图像纹理节点")
            return {'CANCELLED'}

        target_name = scene.onemat_image_nodes[scene.onemat_image_node_index].name
        count = 0

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes:
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    for node in nodes:
                        if node.type == 'TEX_IMAGE' and node.image and node.image.name == target_name:
                            # 断开所有连接
                            for input in node.inputs:
                                for link in input.links:
                                    links.remove(link)
                            nodes.remove(node)
                            count += 1

        # 从列表中移除
        scene.onemat_image_nodes.remove(scene.onemat_image_node_index)
        scene.onemat_image_node_index = max(0, scene.onemat_image_node_index - 1)

        self.report({'INFO'}, f"已删除图像节点：{target_name}（{count} 个节点）")
        return {'FINISHED'}


############Setp04 烘焙面板操作部分

#######减选非Mesh物体
class ONEMAT_OT_remove_non_mesh_objects(bpy.types.Operator):
    bl_idname = "onemat.remove_non_mesh_objects"
    bl_label = "减选非Mesh物体"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                obj.select_set(False)
        return {'FINISHED'}
    



##################### 自发光金属度先不写
# class ONEMAT_OT_bake_metal_to_emission(bpy.types.Operator):
#     bl_idname = "onemat.bake_metal_to_emission"
#     bl_label = "金属度 ➜ 自发光"

#     def execute(self, context):
#         for obj in context.selected_objects:
#             if obj.type != 'MESH':
#                 continue
#             for slot in obj.material_slots:
#                 mat = slot.material
#                 if not mat or not mat.use_nodes:
#                     continue
#                 for node in mat.node_tree.nodes:
#                     if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
#                         for link in node.inputs['Metallic'].links:
#                             mat.node_tree.links.remove(link)
#                         node.inputs['Metallic'].default_value = 0.0
#                         node.inputs['Emission Strength'].default_value = 1.0
#         return {'FINISHED'}


# class ONEMAT_OT_bake_emission_to_metal(bpy.types.Operator):
#     bl_idname = "onemat.bake_emission_to_metal"
#     bl_label = "自发光 ➜ 金属度"

#     def execute(self, context):
#         for obj in context.selected_objects:
#             if obj.type != 'MESH':
#                 continue
#             for slot in obj.material_slots:
#                 mat = slot.material
#                 if not mat or not mat.use_nodes:
#                     continue
#                 for node in mat.node_tree.nodes:
#                     if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
#                         for link in node.inputs['Emission'].links:
#                             mat.node_tree.links.remove(link)
#                         node.inputs['Emission'].default_value = (0, 0, 0, 1)
#                         node.inputs['Metallic'].default_value = 1.0
#         return {'FINISHED'}

##########烘焙按钮
class ONEMAT_OT_bake_selected(bpy.types.Operator):
    bl_idname = "onemat.bake_selected"
    bl_label = "烘焙当前图像"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "请选择一个网格物体")
            return {'CANCELLED'}

        try:
            bpy.ops.object.bake('INVOKE_DEFAULT')
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"烘焙失败: {e}")
            return {'CANCELLED'}
        
##########保存图像
last_saved_image_path = ""

class ONEMAT_OT_save_active_image_popup(bpy.types.Operator):
    """保存当前活动图像"""
    bl_idname = "onemat.save_active_image_popup"
    bl_label = "保存当前图像为..."


    def invoke(self, context, event):
        # 设置默认路径为上一次使用路径或当前 .blend 所在目录
        global last_saved_image_path
        self.filepath = last_saved_image_path or bpy.path.abspath("//T_Image.png")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        global last_saved_image_path

        # 获取当前 Image Editor 中的图像
        area = next((a for a in context.screen.areas if a.type == 'IMAGE_EDITOR'), None)
        if not area:
            self.report({'ERROR'}, "未找到 Image Editor")
            return {'CANCELLED'}

        for space in area.spaces:
            if space.type == 'IMAGE_EDITOR' and space.image:
                image = space.image
                if not image.has_data:
                    self.report({'ERROR'}, f"图像 '{image.name}' 没有可保存的数据")
                    return {'CANCELLED'}

                # 设置图像保存路径
                image.filepath_raw = self.filepath
                image.file_format = 'PNG'  # 可改为其他格式
                try:
                    image.save()
                except RuntimeError as e:
                    self.report({'ERROR'}, f"保存失败：{e}")
                    return {'CANCELLED'}

                # 记录最后使用路径
                last_saved_image_path = self.filepath

                self.report({'INFO'}, f"图像已保存至: {self.filepath}")
                return {'FINISHED'}

        self.report({'ERROR'}, "未找到活动图像")
        return {'CANCELLED'}
    
#####################Step05 贴图
# 删除材质插槽
class ONEMAT_OT_remove_material_slots(bpy.types.Operator):
    bl_idname = "onemat.remove_material_slots"
    bl_label = "Remove Material Slots"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.data.materials.clear()
        self.report({'INFO'}, "已删除材质插槽")
        return {'FINISHED'}

class ONEMAT_OT_create_and_assign_material(bpy.types.Operator):
    bl_idname = "onemat.create_and_assign_material"
    bl_label = "创建材质并赋予"
    bl_description = "使用输入的名称创建材质，并绑定到选中物体，同时添加匹配图像贴图"

    def execute(self, context):
        name_input = context.scene.onemat_material_name.strip()
        if not name_input:
            self.report({'WARNING'}, "材质名为空")
            return {'CANCELLED'}

        mat_name = f"M_{name_input}"

        # 若材质已存在则复用，否则创建
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
            self.report({'INFO'}, f"材质 '{mat_name}' 已存在，使用已有材质")
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            self.report({'INFO'}, f"已创建材质: {mat_name}")

        # 图像名匹配逻辑（忽略前后缀）
        matched_image = None

        for img in bpy.data.images:
            base = img.name.split('.')[0]  # 去除扩展名

            # 去前缀
            if base.startswith("T_"):
                base = base.replace("T_", "", 1)

            # 去后缀（一个个判断）
            if base.endswith("_Color"):
                base = base[:-len("_Color")]
            elif base.endswith("_Normal"):
                base = base[:-len("_Normal")]
            elif base.endswith("_Emissive"):
                base = base[:-len("_Emissive")]
            elif base.endswith("_Alpha"):
                base = base[:-len("_Alpha")]
            elif base.endswith("_Metallic"):
                base = base[:-len("_Metallic")]
            elif base.endswith("_Roughness"):
                base = base[:-len("_Roughness")]
            elif base.endswith("_BaseColor"):
                base = base[:-len("_BaseColor")]

            if base == name_input:
                matched_image = img
                break

        # 如果图像匹配成功，添加到材质节点
        if matched_image:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

        # 添加主要节点
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (600, 0)

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (300, 0)

        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # 定义贴图类型与连接目标
        map_info = {
            "_Color":      ("Base Color", "Color"),
            "_BaseColor":  ("Base Color", "Color"),
            "_Normal":     ("Normal", "Color"),      # 后面处理法线贴图特殊处理
            "_Metallic":   ("Metallic", "Color"),
            "_Roughness":  ("Roughness", "Color"),
            "_Emissive":   ("Emission Color", "Color"),
            "_Alpha":      ("Alpha", "Color"),
        }

        # 当前材质名（剥除前缀 M_）
        mat_base_name = name_input

        y_offset = 0

        for suffix, (bsdf_input, tex_output) in map_info.items():
            # 构造可能的图像名（允许前缀 T_）
            candidates = [
                f"{mat_base_name}{suffix}",
                f"T_{mat_base_name}{suffix}",
            ]

            matched_image = None
            for img in bpy.data.images:
                img_base = img.name.split('.')[0]
                if img_base in candidates:
                    matched_image = img
                    break

            if matched_image:
                # 创建图像节点
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.image = matched_image
                tex_node.label = f"{bsdf_input}_Tex"
                tex_node.location = (-300, y_offset)

                if suffix == "_Normal":
                    # 添加法线贴图处理节点
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (0, y_offset)
                    links.new(tex_node.outputs["Color"], normal_map.inputs["Color"])
                    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
                else:
                    links.new(tex_node.outputs[tex_output], bsdf.inputs[bsdf_input])

                y_offset -= 300  # 每个贴图往下排

        # 赋予所有选中物体
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)

        return {'FINISHED'}
