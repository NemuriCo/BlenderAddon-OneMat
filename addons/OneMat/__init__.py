import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary


# Add-on info
bl_info = {
    "name": "OneMat",
    "author": "沉睡钴&蓝",
    "blender": (4, 5, 3),
    "version": (0, 0, 1),
    "description": "Bake many of your materials into one texture!",
    "warning": "",
    "doc_url": "[documentation url]",
    "tracker_url": "[contact email]",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {
    bpy.types.Scene: {

        ######## 大统一命名
        "onemat_go_name": bpy.props.StringProperty(
            name="名称", 
            default="OneMat"
        ),

        ########## UV
        "onemat_uv_name": bpy.props.StringProperty(
            name="UV贴图名称",
            default="UVMap_OneMatBake"
        ),
        ######## 贴图
        "onemat_material_name": bpy.props.StringProperty(
            name="材质名", 
            default="OneMat"
        ),

        "onemat_uv_index": bpy.props.IntProperty(
            name="UV Index",
            default=0
        ),

        ########## 图像
        "onemat_image_prefix": bpy.props.StringProperty(
            name="前缀", default="T_"
        ),
        "onemat_image_name": bpy.props.StringProperty(
            name="图像名", default="OneMat"
        ),
        "onemat_image_suffix": bpy.props.EnumProperty(
            name="后缀",
            items=[
                ("_Color", "_Color", ""),
                ("_Normal", "_Normal", ""),
                ("_Emissive", "_Emissive", ""),
                ("_Alpha", "_Alpha", ""),
                ("_Metallic", "_Metallic", ""),
                ("_Roughness", "_Roughness", ""),
                ("_BaseColor", "_BaseColor", ""),
                ("Null", "Null", "不添加后缀"),
            ],
            default="_Color"
        ),
        "onemat_image_width": bpy.props.IntProperty(
            name="宽度", default=1024, min=1
        ),
        "onemat_image_height": bpy.props.IntProperty(
            name="高度", default=1024, min=1
        ),
        "onemat_image_alpha": bpy.props.BoolProperty(
            name="Alpha", default=True
        ),
        ######## 图像序号
        "onemat_image_nodes": bpy.props.CollectionProperty(
            type=bpy.types.PropertyGroup
        ),
        "onemat_image_node_index": bpy.props.IntProperty(
        ),

        ########## 烘焙
        "onemat_bake_type": bpy.props.EnumProperty(
            name="烘焙类型",
            items=[
                ('COMBINED', "Combined", ""),
                ('AO', "Ambient Occlusion", ""),
                ('NORMAL', "Normal", ""),
                ('DIFFUSE', "Diffuse", ""),
                ('GLOSSY', "Glossy", ""),
                ('TRANSMISSION', "Transmission", ""),
            ],
            default='DIFFUSE'
        ),
        "onemat_bake_margin": bpy.props.IntProperty(
            name="烘焙边距",
            default=2,  
            min=0
        ),
        "onemat_bake_selected_to_active": bpy.props.BoolProperty(
            name="仅选中 → 激活",
            default=False
        ),
        "onemat_bake_use_clear": bpy.props.BoolProperty(
            name="清除图像",
            default=True
        ),
        "onemat_bake_save_image": bpy.props.BoolProperty(
            name="保存图像",
            default=False
        ),
        "onemat_bake_path": bpy.props.StringProperty(
            name="保存路径",
            subtype='DIR_PATH'
        ),
        "onemat_bake_margin": bpy.props.IntProperty(
            name="烘焙边距",
            default=2,
            min=0
        ),
        "onemat_bake_selected_to_active": bpy.props.BoolProperty(
            name="仅选中 → 激活",
            default=False
        ),
        "onemat_bake_use_clear": bpy.props.BoolProperty(
            name="清除图像",
            default=True
        ),



        
    }
}



# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# 注意不要在__init__.py文件中自定义PropertyGroup类。请在单独的文件中定义它们并在此处导入。
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

def register():
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    print("{} addon is installed.".format(__addon_name__))
    
    


def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)
    print("{} addon is uninstalled.".format(__addon_name__))
