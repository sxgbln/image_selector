bl_info = {
    "name": "Image Selector",
    "blender": (4, 1, 0),
    "category": "Material",
    "author": "Your Name",
    "version": (1, 0, 1),
    "description": "Create materials with multiple image textures selected by the user",
    "location": "Properties > Material",
    "support": "COMMUNITY",
}

import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper

class IMAGE_OT_open_filebrowser(Operator, ImportHelper):
    """Open a file browser to select image files"""
    bl_idname = "image.open_filebrowser"
    bl_label = "Select Images"
    bl_options = {'REGISTER', 'UNDO'}
    
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        images = [self.directory + f.name for f in self.files]
        print("Selected images:", images)
        
        if len(images) < 2:
            self.report({'ERROR'}, "Please select at least two images.")
            return {'CANCELLED'}

        if bpy.context.active_object is not None:
            obj = bpy.context.active_object

            mat_name = "CustomMaterial"
            material = (bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name))
            obj.active_material = material
            
            material.use_nodes = True
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            
            nodes.clear()

            principled_node = nodes.new("ShaderNodeBsdfPrincipled")
            principled_node.location = (400, 0)
            
            mat_output = nodes.new('ShaderNodeOutputMaterial')
            mat_output.location = (600, 100)
            
            links.new(principled_node.outputs["BSDF"], mat_output.inputs["Surface"])
            
            value_node = nodes.new("ShaderNodeValue")
            value_node.location = (0, 400)
            
            tex_coord_node = nodes.new("ShaderNodeTexCoord")
            tex_coord_node.location = (-1100, 0)
            
            mapping_node = nodes.new("ShaderNodeMapping")
            mapping_node.location = (-900, 0)
            
            links.new(tex_coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            
            x_offset = -300
            y_offset = 300
            y_spacing = -300
            
            num_nodes = len(images)
            thresholds = [i - 0.1 for i in list(range(1, num_nodes + 1))[::-1]]

            previous_color_node = None
            previous_alpha_node = None

            for x in range(1, num_nodes + 1):
                # Color mixing nodes
                mix_color_node_location = (x_offset + (x * 200), y_offset + (x * y_spacing))
                image_texture_node_location = (mix_color_node_location[0] - 300, mix_color_node_location[1])
                math_node_location = (image_texture_node_location[0] - 200, image_texture_node_location[1])
                
                mix_color_node = nodes.new("ShaderNodeMixRGB")
                mix_color_node.location = mix_color_node_location
                mix_color_node.name = f"MixRGB_Node_{x}"
                mix_color_node.label = f"Mix RGB {x}"
                
                image_texture_node = nodes.new('ShaderNodeTexImage')
                image_texture_node.location = image_texture_node_location
                image_texture_node.name = f"img_Node_{x}"
                image_texture_node.label = f"IMG Node {x}"
                image_texture_node.image = bpy.data.images.load(images[x-1])
                image_texture_node.image.alpha_mode = 'PREMUL'  # Set alpha to premultiplied
                links.new(mapping_node.outputs["Vector"], image_texture_node.inputs["Vector"])
                
                math_node = nodes.new("ShaderNodeMath")
                math_node.location = math_node_location
                math_node.name = f"Math_Node_{x}"
                math_node.label = f"Math {x}"
                math_node.operation = "GREATER_THAN"
                math_node.inputs[1].default_value = thresholds[x-1]
                links.new(math_node.outputs["Value"], mix_color_node.inputs["Fac"])
                links.new(value_node.outputs["Value"], math_node.inputs["Value"])
                links.new(image_texture_node.outputs["Color"], mix_color_node.inputs["Color2"])
                
                if previous_color_node is not None:
                    links.new(mix_color_node.outputs["Color"], previous_color_node.inputs["Color1"])
                else:
                    links.new(mix_color_node.outputs["Color"], principled_node.inputs["Base Color"])
                
                previous_color_node = mix_color_node

                # Alpha mixing nodes
                mix_alpha_node_location = (mix_color_node_location[0], mix_color_node_location[1] - 150)
                mix_alpha_node = nodes.new("ShaderNodeMixRGB")
                mix_alpha_node.location = mix_alpha_node_location
                mix_alpha_node.blend_type = 'MIX'
                mix_alpha_node.inputs[0].default_value = 1.0
                
                links.new(image_texture_node.outputs["Alpha"], mix_alpha_node.inputs["Color2"])
                links.new(math_node.outputs["Value"], mix_alpha_node.inputs["Fac"])

                if previous_alpha_node is not None:
                    links.new(mix_alpha_node.outputs["Color"], previous_alpha_node.inputs["Color1"])
                else:
                    links.new(mix_alpha_node.outputs["Color"], principled_node.inputs["Alpha"])
                
                previous_alpha_node = mix_alpha_node

            print("Nodes created and modified successfully!")
        else:
            print("No active object selected.")
        
        return {'FINISHED'}

class MATERIAL_PT_custom_panel(Panel):
    """Creates a Panel in the Material properties window"""
    bl_label = "Custom Material Tools"
    bl_idname = "MATERIAL_PT_custom_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        layout.operator("image.open_filebrowser", text="Select Images")

classes = (
    IMAGE_OT_open_filebrowser,
    MATERIAL_PT_custom_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
