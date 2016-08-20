# AirMech-AMF-file-blender-import
####Blender import script for AirMech amf models

quick-n-dirty implementation, but handles mesh and uv data, so you will get a mesh, that can be viewed with a texture by just loading the texture file.

Most models rely on bones to place some moving parts. That parts appear at 0,0,0 after import. I don't care, because it is very easy to place them right. But it is hard to tinker with binary file in hex-editor :feelsgood:

BTW: i will include the script for quickbms that unpacks HPK files in which AMFs are located.
