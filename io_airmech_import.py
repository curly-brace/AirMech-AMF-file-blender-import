bl_info = {
    'name': 'Import AirMech AMF files',
    'author': 'curly brace',
        "version": (1, 0, 0),
    "blender": (2, 77, 0),
    'location': 'File > Import > AirMech AMF or Add > Mesh > AirMech AMF',
    'description': 'Imports AMF model files from AirMech (which is not a well known 3d printing format)'
        'It is not full and quick-n-dirty made. I needed only to be able to view textured object.'
        'So some things, that require bones to be positioned and scaled, may appear out of place',
    'category': 'Import-Export',
}

import bpy
import struct
import bmesh
from bpy_extras.io_utils import unpack_list
from bpy.props import StringProperty

class AirMech(bpy.types.Operator):
    """Import AirMech AMF files"""
    bl_idname = 'import_airmech.amf'
    bl_label = 'Import AirMech AMF files'
    bl_description = 'Imports AMF model files from AirMech (which is not a well known 3d printing format)'
    bl_options = {'REGISTER', 'UNDO'}

    filename = StringProperty(name="File Name", description="Name of the file")
    directory = StringProperty(name="Directory", description="Directory of the file")


    def execute(self, context):
        filename = self.filename
        directory = self.directory

        if not filename.endswith('.amf'):
            self.report({'ERROR'},"Selected file has invalid extension (amf)")
            return {'CANCELLED'}

        self.go_import(directory + filename)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def go_import(self, file):
        f = open(file, 'rb').read()

        sections = {
            b'GEOMOBJ_C\x00':[],
            b'SKELETON_C\x00':[],
            b'MESHOBJ_C\x00':[],
            b'END\x00':[],
            b'BSPHERE\x00':[],
            b'OBS\x00':[],
            b'P_VERTS\x00':[], #!
        #    b'VERTS\x00':[],
            b'TVERTS\x00':[],
            b'VERTNORMALS\x00':[],
            b'TS_TANGENTS\x00':[],
            b'TS_BITANGENTS\x00':[],
            b'TS_NORMALS\x00':[],
            b'SHADOW_GEOMETRY\x00':[],
            b'M_I\x00':[],
            b'FACES_T\x00':[], #!
        #    b'FACES\x00':[],
            b'SHADOW_MESH_ONLY\x00':[],
            b'BONEREFS\x00':[],
            b'MESHTRANSFORM\x00':[],
            b'MESHFRAME\x00':[],
            b'FACEGROUPS\x00':[],
            b'SKINWEIGHTGROUPS\x00':[]
        }

        section_offset = 0

        def read_bytes(count):
            nonlocal f, section_offset
            section_offset += count
            return f[section_offset - count:section_offset]

        for name in sections.keys():
            idx = 0

            while True:
                idx = f.find(name, idx)

                if idx == -1:
                    break

                sections[name].append(idx)
                idx += len(name)

        sections = {k:v for k,v in sections.items() if len(v) > 0}
        indexes = sorted([i[0] for i in sections.values()])

        verts_start = sections[b'P_VERTS\x00'][0] + len(b'P_VERTS\x00')
        verts_end = indexes[indexes.index(sections[b'P_VERTS\x00'][0]) + 1] - 1
        verts_len = verts_end - verts_start

        section_offset = verts_start
        verts= []

        v_rows = struct.unpack('i', read_bytes(4))[0]
        v_cols = struct.unpack('i', read_bytes(4))[0]
        section_offset += 4

        for row in range(v_rows):
            vals = []
            for col in range(int(v_cols / 4)):
                vals.append(struct.unpack('f', read_bytes(4))[0])

            idx = ['x','y','z','nx','ny','nz','hz','u','v']
            verts.append({})

            for i in range(len(idx)):
                if len(vals) > i:
                    verts[-1][idx[i]] = vals[i]
                else:
                    verts[-1][idx[i]] = 0.0

        faces_start = sections[b'FACES_T\x00'][0] + len(b'FACES_T\x00')
        faces_end = indexes[indexes.index(sections[b'FACES_T\x00'][0]) + 1] - 1
        faces_len = faces_end - faces_start

        section_offset = faces_start
        faces = []

        face_cnt = struct.unpack('i', read_bytes(4))[0]

        if face_cnt != 0:
            section_offset += 4
            vert_cnt = struct.unpack('i', read_bytes(4))[0]


            for v in range(face_cnt):
                v1 = struct.unpack('i', read_bytes(2) + b'\x00\x00')[0]
                v2 = struct.unpack('i', read_bytes(2) + b'\x00\x00')[0]
                v3 = struct.unpack('i', read_bytes(2) + b'\x00\x00')[0]

                faces.append((v1, v2, v3))

        me = bpy.data.meshes.new('airmech_mesh')
        obj = bpy.data.objects.new('airmech_object', me)

        scene = bpy.context.scene
        scene.objects.link(obj)
        obj.select = True

        verts = [((v['x'], v['y'], v['z']), (v['u'], 1 - v['v'])) for v in verts]

        vert_list = [v[0] for v in verts]

        me.from_pydata(vert_list, [], faces)

        me.uv_textures.new()
        uvs = me.uv_layers[0]

        for l in me.loops:
            v = verts[l.vertex_index]
            uvs.data[l.index].uv = v[1]

        me.update()


# Registering / Unregister
def menu_func(self, context):
    self.layout.operator(AirMech.bl_idname, text="AirMech AMF", icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
