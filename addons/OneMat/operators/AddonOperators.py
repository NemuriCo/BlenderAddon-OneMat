import bpy
import bmesh

import bl_ext.user_default.uvpackmaster3 as uvpm3

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
    
############# OneMat Go面板操作部分
#####模型处理
class OneMat_OT_OneMatGoMesh(bpy.types.Operator): 
    '''一键独立化数据,转网格(仅限非MESH对象),应用修改器(保留WeightedNormal和Armature),应用缩放'''
    bl_idname = "object.one_mat_go_mesh"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}]

        if not selected_objects:
            self.report({'WARNING'}, "未选中任何可转换的对象")
            return {'CANCELLED'}

        for obj in selected_objects:
            context.view_layer.objects.active = obj
            obj.select_set(True)

            # 独立化
            bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)

            # ✅ 如果不是 MESH 再转换
            if obj.type != 'MESH':
                try:
                    bpy.ops.object.convert(target='MESH')
                except Exception as e:
                    print(f"[转换失败] {obj.name}: {e}")
                    continue  # 转换失败就跳过后续步骤

            # 再次确认对象为 MESH（有些类型转换失败后依然不是）
            if obj.type != 'MESH':
                print(f"[跳过] {obj.name} 不是 MESH 类型")
                continue

            # ✅ 应用所有非 WeightedNormal 和 Armature 的修改器
            to_keep = {'WEIGHTED_NORMAL', 'ARMATURE'}
            for mod in list(obj.modifiers):  # 避免遍历中删除出错
                if mod.type not in to_keep:
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except Exception as e:
                        print(f"[应用失败] {mod.name} on {obj.name}: {e}")

            # ✅ 应用缩放
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        return {'FINISHED'}

        
#####UV处理
class OneMat_OT_OneMatGoUV(bpy.types.Operator): 
    '''一键将UV贴图设置为烘焙用状态并智能展开UV'''
    bl_idname = "object.one_mat_go_uv"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
            # 统一UV贴图命名
            bpy.ops.object.rename_first_uvmap()

            # 删除多余UV贴图
            bpy.ops.object.remove_extra_uvmaps()

            # 批量添加UV贴图
            name = context.scene.onemat_go_name
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    obj.data.uv_layers.new(name=name)


            # 将第2套UV贴图设置为编辑
            uv_index = 1
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue
                if uv_index < len(obj.data.uv_layers):
                    obj.data.uv_layers.active_index = uv_index
                else:
                    self.report({'WARNING'}, f"{obj.name} 没有第2个UV")

            # 将第1套UV贴图设置为渲染
            uv_index = 0
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue
                uv_layers = obj.data.uv_layers
                if uv_index < len(uv_layers):
                    # 遍历所有 UV 层，设置渲染 UV
                    for i, uv_layer in enumerate(uv_layers):
                        uv_layer.active_render = (i == uv_index)
                else:
                    self.report({'WARNING'}, f"{obj.name} 没有第1个UV")



            # 转入 Edit 模式（如果当前在 Object 模式）
            if bpy.context.object.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            # 选中所有面
            bpy.ops.mesh.select_all(action='SELECT')

            # 执行 Smart UV Project
            bpy.ops.uv.smart_project(
                angle_limit=1.155,  
                island_margin=0.03,
                area_weight=0.0,
                correct_aspect=True,
                scale_to_bounds=False
            )

            # 回到物体模式
            bpy.ops.object.mode_set(mode='OBJECT')

            # 打包UV
            bpy.ops.onemat.uvpackmaster3_pack() 

            self.report({'INFO'}, "操作完成！请点击 Bake 继续")

        
            return {'FINISHED'}
    
#####材质处理
class OneMat_OT_OneMatGoMat(bpy.types.Operator): 
    '''一键为材质添加图像纹理节点'''
    bl_idname = "object.one_mat_go_mat"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
            # 批量添加图像纹理
            scene = context.scene
            prefix = "T_"
            name = context.scene.onemat_go_name
            suffix = "_Color"
            width = 2048
            height = 2048
            use_alpha = True

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
    
#####烘焙
class OneMat_OT_OneMatGoBake(bpy.types.Operator): 
    '''一键烘焙选中物体'''
    bl_idname = "object.one_mat_go_bake"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
            # 减选非Mesh物体
            bpy.ops.onemat.remove_non_mesh_objects()

            # 烘焙
            bpy.ops.onemat.bake_selected()
            return {'FINISHED'}
    
#####贴图
class OneMat_OT_OneMatGoTex(bpy.types.Operator): 
    '''一键为选中烘焙好的贴图创建材质赋予物体'''
    bl_idname = "object.one_mat_go_tex"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
            
            # 删除第1套UV贴图
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    uv_layers = obj.data.uv_layers
                    if len(uv_layers) > 0:
                        uv_layers.remove(uv_layers[0])

            # 统一UV贴图命名
            bpy.ops.object.rename_first_uvmap()

            # 删除所有材质插槽
            bpy.ops.onemat.remove_material_slots()

            # 新建材质赋予
            name_material_go = context.scene.onemat_go_name.strip()
            if not name_material_go:
                self.report({'WARNING'}, "材质名为空")
                return {'CANCELLED'}

            gomat_name = f"M_{name_material_go}"

            # 若材质已存在则复用，否则创建
            if gomat_name in bpy.data.materials:
                mat = bpy.data.materials[gomat_name]
                self.report({'INFO'}, f"材质 '{gomat_name}' 已存在，使用已有材质")
            else:
                mat = bpy.data.materials.new(name=gomat_name)
                mat.use_nodes = True
                self.report({'INFO'}, f"已创建材质: {gomat_name}")

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

                if base == name_material_go:
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
            mat_base_name = name_material_go

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

#####保存
class OneMat_OT_OneMatGoSave(bpy.types.Operator): 
    '''一键保存'''
    bl_idname = "object.one_mat_go_save"
    bl_label = "一键处理"  
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

            return {'FINISHED'}



























######################## Step01 模型处理面板操作部分
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

#打包UV
# 转入 Edit 模式（如果当前在 Object 模式）
class OneMat_UVPack(bpy.types.Operator):
    bl_idname = "object.uvpack"
    bl_label = "打包UV"

    def execute(self, context):
            if bpy.context.object.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            # 选中所有面（可选）
            bpy.ops.mesh.select_all(action='SELECT')

            # 执行 Smart UV Project
            bpy.ops.uv.smart_project(
                angle_limit=1.155,  
                island_margin=0.03,
                area_weight=0.0,
                correct_aspect=True,
                scale_to_bounds=False
            )

            # 回到物体模式
            bpy.ops.object.mode_set(mode='OBJECT')

            # 打包UV
            bpy.ops.onemat.uvpackmaster3_pack() 
            return {'FINISHED'}

# Step03 材质处理面板操作部分
class ONEMAT_OT_SelectNoMaterialObjects(bpy.types.Operator):
    bl_idname = "onemat.select_no_material_objects"
    bl_label = "仅选中无材质物体"
    bl_description = "检查选中物体，保留类型为Mesh且无材质的对象"

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):
        selected_objs = context.selected_objects
        objs_with_no_mat = [
            obj for obj in selected_objs
            if obj.type == 'MESH' and not obj.material_slots
        ]

        bpy.ops.object.select_all(action='DESELECT')

        for obj in objs_with_no_mat:
            obj.select_set(True)

        self.report({'INFO'}, f"找到 {len(objs_with_no_mat)} 个无材质网格物体")
        return {'FINISHED'}
    
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
            bpy.ops.object.bake('INVOKE_DEFAULT',type='DIFFUSE',)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"烘焙失败: {e}")
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

# 创建并赋予材质
class ONEMAT_OT_create_and_assign_material(bpy.types.Operator):
    bl_idname = "onemat.create_and_assign_material"
    bl_label = "创建材质并赋予"
    bl_description = "使用输入的名称创建材质，并绑定到选中物体，同时添加匹配图像贴图"

    def execute(self, context):
        name_input = context.scene.onemat_go_name.strip()
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
    
    
# 保存路径
class ONEMAT_OT_save_all_images(bpy.types.Operator):
    bl_idname = "onemat.save_all_images"
    bl_label = "保存所有贴图"
    bl_description = "将选中物体材质中的图像纹理保存到指定文件夹"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import os

        scene = context.scene
        export_path = bpy.path.abspath(scene.onemat_output_path)

        if not os.path.exists(export_path):
            self.report({'ERROR'}, f"路径不存在: {export_path}")
            return {'CANCELLED'}

        saved_images = set()

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue

                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        image = node.image
                        if image.name in saved_images:
                            continue
                        if not image.has_data:
                            self.report({'WARNING'}, f"图像无数据: {image.name}")
                            continue

                        file_path = os.path.join(export_path, f"{image.name}.png")
                        try:
                            image.filepath_raw = file_path
                            image.file_format = 'PNG'
                            image.save()
                            saved_images.add(image.name)
                        except Exception as e:
                            self.report({'WARNING'}, f"保存失败 {image.name}: {str(e)}")

        self.report({'INFO'}, f"保存完成，共 {len(saved_images)} 张图像")
        return {'FINISHED'}












#########UVPackMaster3打包操作部分
class OneMat_OT_UVPackMaster3_Pack(bpy.types.Operator):
    bl_idname = "onemat.uvpackmaster3_pack"
    bl_label = "保存所有贴图"

    def execute(self, context):

        # Make the object active
        obj_to_pack = bpy.context.view_layer.objects.active

        bpy.ops.object.editmode_toggle()

        # Select all UVs
        bpy.ops.uv.select_all(action='SELECT')
        bm = bmesh.from_edit_mesh(obj_to_pack.data)
        uv_layer = bm.loops.layers.uv.verify()

        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                loop_uv.select = True


        # === PACKING OPERATION BEGIN ===
        # Reset all UVPM parameters to defaults
        bpy.ops.uvpackmaster3.reset_to_defaults()

        # Set values for all required UVPM parameters directly in the script.
        uvpm3_prefs = uvpm3.utils.get_prefs()
        uvpm3_props = uvpm3.utils.get_main_props(bpy.context)

        # To get the python path for the given parameter, open Blender normally (with GUI),
        # right mouse click over the parameter in the packer UI, then select 'Copy Data Path'
        # from the menu. The path will be copied to clipboard. 
        uvpm3_props.precision = 500

        # Select packing mode id - uncomment only one line below
        mode_id = "pack.single_tile"
        # mode_id = "pack.tiles"
        # mode_id = "pack.groups_to_tiles"
        # mode_id = "pack.groups_together"

        # If you want to use the packing mode currently selected in the blend file (e.g. after loading a UVPM preset), uncomment the following line
        # mode_id = uvpm3_props.active_main_mode_id

        pack_op_type = uvpm3.enums.PackOpType.PACK.code
        # pack_op_type = uvpm3.enums.PackOpType.PACK_TO_OTHERS.code
        # pack_op_type = uvpm3.enums.PackOpType.REPACK_WITH_OTHERS.code

        try:
            bpy.ops.uvpackmaster3.pack(mode_id=mode_id, pack_op_type=pack_op_type)
        except Exception as ex:
            print('Pack operation failed: ' + str(ex))

        if uvpm3_prefs.engine_retcode != 0:
            raise RuntimeError('UVPM 3 operation not succeeded (a warning or error occurred)! Return code: {}'.format(int(uvpm3_prefs.engine_retcode)))

        # === PACKING OPERATION END ===

        bpy.ops.object.editmode_toggle()
        return {'CANCELLED'}