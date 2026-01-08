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


# 模型处理面板
@reg_order(0)
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

# UV处理面板
@reg_order(1)
class OneMat_PT_UVPanel(bpy.types.Panel):
    bl_label = "Step02 UV处理"
    bl_idname = "onemat_pt_uv_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneMat"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="UV贴图统一")

        row = box.row()
        row.operator("object.rename_first_uvmap", text="第1套统一命名为UVMap")

        row = box.row()
        row.operator("object.remove_extra_uvmaps", text="删除多余UVMap")

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

# 材质处理面板
@reg_order(2)
class OneMat_PT_MaterialPanel(BasePanel, bpy.types.Panel):
    bl_label = "Step03 材质处理"
    bl_idname = "onemat_pt_material_panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="添加烘焙用图像纹理节点")

        col = box.column(align=True)
        # col.prop(scene, "onemat_image_prefix", text="前缀") # 前缀没啥用省略吧
        col.prop(scene, "onemat_image_name", text="名称")
        col.prop(scene, "onemat_image_suffix", text="后缀")

        row = box.row(align=True)
        row.prop(scene, "onemat_image_width", text="宽度")
        row.prop(scene, "onemat_image_height", text="高度")

        col = box.column(align=True)
        col.prop(scene, "onemat_image_alpha", text="Alpha")
        

        row = box.row()
        row.operator("one_mat.add_texture_to_materials", text="批量添加图像纹理", icon='TEXTURE')

        
