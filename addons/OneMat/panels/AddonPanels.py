import bpy

from ..config import __addon_name__
from ..operators.AddonOperators import OneMatOperator
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order


class BasePanel(object):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OneMat"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


################### Step01 模型处理面板
@reg_order(0)
######### 物体选择
class OneMat_PT_MeshPanel(BasePanel, bpy.types.Panel):
    bl_label = "Step01 模型处理"
    bl_idname = "onemat_pt_mesh_panel"


    def draw(self, context):
        layout = self.layout

        # 创建一个带边框的 Box 区域
        box = layout.box()
        box.label(text="物体选择")

        # 添加两个按钮
        box.operator("object.one_mat_select_mesh", text="减选Mesh物体")
        box.operator("object.one_mat_toggle_wire", text="线框模式切换")


    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

#################### Step02 UV处理面板
@reg_order(1)

class OneMat_PT_UVPanel(bpy.types.Panel):
    bl_label = "Step02 UV处理"
    bl_idname = "onemat_pt_uv_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneMat"

    def draw(self, context):
        layout = self.layout

        ########## UV贴图统一
        box = layout.box()
        box.label(text="UV贴图统一")

        row = box.row()
        row.operator("object.rename_first_uvmap", text="第1套统一命名为UVMap")

        row = box.row()
        row.operator("object.remove_extra_uvmaps", text="删除多余UVMap")

        ########## 创建UV贴图
        box = layout.box()
        box.label(text="创建UV贴图")

        row = box.row()
        row.prop(context.scene, "onemat_uv_name", text="UV贴图名称")

        row = box.row()
        row.operator("object.add_uvmap_batch", text="批量添加UV贴图")

        box = layout.box()
        box.label(text="UV贴图处理")

        # 没啥用，选择物体后会自动检测
        # row = box.row()
        # row.operator("object.check_current_uvmap", text="检测当前UV贴图", icon='VIEWZOOM')

        row = box.row()
        row.template_list("MESH_UL_uvmaps", "", context.object.data if context.object and context.object.type == 'MESH' else None,
                          "uv_layers", context.scene, "onemat_uv_index", rows=2)
        

        # 没啥用，选择UV贴图后会自动定义序号
        # row = box.row()
        # row.prop(context.scene, "onemat_uv_index", text="目标UV序号")

        row = box.row(align=True)
        row.operator("one_mat.set_active_uv_for_selected", text="设为编辑UV")
        row.operator("one_mat.set_render_uv_for_selected", text="设为渲染UV")

        row = box.row()
        row.operator("object.remove_uvmap_by_index", text="删除指定序号UV贴图", icon='X')

#################### Step03 材质处理面板
@reg_order(2)
class OneMat_PT_MaterialPanel(BasePanel, bpy.types.Panel):
    bl_label = "Step03 材质处理"
    bl_idname = "onemat_pt_material_panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        ######### 添加图像纹理节点
        box = layout.box()
        box.label(text="添加烘焙用图像纹理节点")

        col = box.column(align=True)
        # col.prop(scene, "onemat_image_prefix", text="前缀") # 前缀没啥用省略吧
        col.prop(scene, "onemat_image_name", text="名称")
        col.prop(scene, "onemat_image_suffix", text="后缀")

        row = box.row()
        row.prop(scene, "onemat_image_width", text="宽度")
        
        row = box.row()
        row.prop(scene, "onemat_image_height", text="高度")

        col = box.column(align=True)
        col.prop(scene, "onemat_image_alpha", text="Alpha")
        

        row = box.row()
        row.operator("one_mat.add_texture_to_materials", text="批量添加图像纹理", icon='TEXTURE')

        #########图像纹理节点管理
        box = layout.box()
        box.label(text="图像纹理节点管理")

        row = box.row(align=True)
        row.operator("one_mat.detect_image_texture_nodes", text="检测当前图像纹理节点", icon='FILE_REFRESH')

        # 图像纹理节点列表
        layout = self.layout
        scene = context.scene

        layout.operator("one_mat.refresh_image_nodes", icon="FILE_REFRESH")

        row = box.row()
        row.template_list(
            "UI_UL_list",
            "onemat_image_node_list",
            scene,
            "onemat_image_nodes",
            scene,
            "onemat_image_node_index",
            rows=4
        )
        
        row = layout.row(align=True)
        row.operator("one_mat.activate_image_node", icon="RESTRICT_SELECT_OFF")
        row.operator("one_mat.remove_image_node", icon="X")


        # 图像纹理节点操作
        row = box.row(align=True)
        row.operator("one_mat.set_image_node_active", text="激活图像纹理节点", icon='RESTRICT_VIEW_OFF')
        row.operator("one_mat.remove_selected_image_node", text="删除图像纹理节点", icon='X')
        
#################### Step04 烘焙面板
@reg_order(3)
class ONEMAT_PT_bake_panel(bpy.types.Panel):
    bl_label = "Setp04 烘焙"
    bl_idname = "ONEMAT_PT_bake_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OneMat"

    def draw(self, context):
        layout = self.layout
        props = context.scene       



        box = layout.box()
        box.label(text="烘焙")

        #####减选
        box.operator("onemat.remove_non_mesh_objects", text="减选非Mesh物体")

        #####烘焙类型1
        box.prop(props, "onemat_bake_type", text="烘焙类型")




        ##################### 自发光金属度先不写
        # row = box.row(align=True)
        # row.operator("onemat.bake_metal_to_emission", text="金属度 ➜ 自发光")
        # row.operator("onemat.bake_emission_to_metal", text="自发光 ➜ 金属度")

        ############## 烘焙按钮
        box.operator("onemat.bake_selected", icon='RENDER_STILL')
        ############## 保存图像按钮
        box.operator("onemat.save_active_image_popup", icon='FILE_TICK')

#################### Step05 贴图
@reg_order(4)
class ONEMAT_PT_texture_panel(bpy.types.Panel):
    bl_label = "Setp05 贴图"
    bl_idname = "onemat_pt_texture_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OneMat"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="贴图")

        # 删除材质插槽按钮
        box.operator("onemat.remove_material_slots", text="删除所有材质插槽", icon="X")
        
        row = box.row()
        row.prop(context.scene, "onemat_material_name", text="材质名")

        box.operator("onemat.create_and_assign_material", icon="MATERIAL")

        