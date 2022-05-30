# def scitani(x,y):
#     z=x+y
#     print(z)
#     return z
#
# #z= scitani(5,6)
# import json
# with open ('znacky.json',encoding='UTF-8') as f:
#     znacky = json.load(f)
#
# znacky2 = znacky['symbols']
#
# for z in znacky2:
#     print(z["name"])
#
# feaclass = arcpy.ListFeatureClasses("*", "Point","JTSK")
#
# for fc in feaclass:
#     print(fc)
#
# def conflictDetection(newDataset,outputConflict):
#     feaclass = arcpy.ListFeatureClasses("*", "Polygon", newDataset)
#
#     # if not arcpy.Exists(outputConflict):
#     #     arcpy.Delete_management(outputConflict)
#     # arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputConflict, "POLYGON")
#
#     for fc in feaclass:
#         print("A: "+fc)
#         arcpy.management.MakeFeatureLayer(fc, "fc.lyr")
#         for fc2 in feaclass:
#             print("B: " + fc2)
#             arcpy.management.MakeFeatureLayer(fc2, "fc2.lyr")
#             arcpy.cartography.DetectGraphicConflict("fc.lyr", "fc2.lyr", "outFcTemp")
#             arcpy.management.Merge(["outFcTemp",outputConflict], "outputMergeTemp")
#             arcpy.management.CopyFeatures("outputMergeTemp", outputConflict)
#
#     arcpy.management.Delete("outFcTemp","outputMergeTemp","fc.lyr","fc2.lyr")

print(range(5))

nets = {0: [[-10, -10], [0, -10], [10, -10]], 1: [[0, 0], [10, 0], [-10, 10]], 2: [[0, 10], [10, 10]]}

print(len(nets[0]))

for i in range(5):
    print(i)

    [[[ < Polygon object at 0x21cd36cd748[0x21cd4034378] >, < Polygon object at
     0x21cd36cd390[0x21cd40343a0] >, < Polygon
    object
    at
    0x21cd36cd588[0x21cd36db3a0] >, < Polygon
    object
    at
    0x21cd36cd860[0x21cd36db2b0] >, < Polygon
    object
    at
    0x21cd36cd898[0x21cd36db288] >, < Polygon
    object
    at
    0x21cd36cd8d0[0x21cd36db198] >]], [[ < Polygon object at 0x21cf8d5e438[0x21cd4073b70] >, < Polygon
    object
    at
    0x21cdae10780[0x21cd36dbd28] >, < Polygon
    object
    at
    0x21cf8d6c2b0[0x21cd36dbfd0] >, < Polygon
    object
    at
    0x21cf8d6c7b8[0x21cf8d5f6e8] >, < Polygon
    object
    at
    0x21cf8d6c4e0[0x21cf8d5faa8] >, < Polygon
    object
    at
    0x21cf8d6cb70[0x21cf8d5fc38] >]], [[ < Polygon object at 0x21cf8d5e588[0x21cd36dbc60] >, < Polygon
    object
    at
    0x21cf8d6c550[0x21cd36db9b8] >, < Polygon
    object
    at
    0x21cf8d6cba8[0x21cf8d5fad0] >, < Polygon
    object
    at
    0x21cf8d6cf98[0x21cf8d5fb20] >, < Polygon
    object
    at
    0x21cf8d6cdd8[0x21cf8d5fb70] >]], [[ < Polygon object at 0x21cf8d5ef60[0x21cd36dbcd8] >, < Polygon
    object
    at
    0x21cd4081400[0x21cd36db940] >, < Polygon
    object
    at
    0x21cf8d80208[0x21cf8d5f0f8] >, < Polygon
    object
    at
    0x21cf8d809b0[0x21cf8d59508] >]], [[ < Polygon object at 0x21cd4020ba8[0x21cf8d5f828] >]], [[ < Polygon object at
                                                                                                0x21cd36cde80[
                                                                                                    0x21cf8d5f3c8] >, < Polygon
    object
    at
    0x21cf8d5e908[0x21cf8d5f300] >, < Polygon
    object
    at
    0x21cf8d6ca58[0x21cf8d5fbe8] >]], [[ < Polygon object at 0x21cf8d6c8d0[0x21cf8d5fd50] >, < Polygon
    object
    at
    0x21cf8d80128[0x21cd36dbe68] >]], [[ < Polygon object at 0x21cd41b7ef0[0x21cd36db828] >, < Polygon
    object
    at
    0x21cd41b7080[0x21cd36dbbc0] >]]]