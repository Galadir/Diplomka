def scitani(x,y):
    z=x+y
    print(z)
    return z

#z= scitani(5,6)
import json
with open ('znacky.json',encoding='UTF-8') as f:
    znacky = json.load(f)

znacky2 = znacky['symbols']

for z in znacky2:
    print(z["name"])

feaclass = arcpy.ListFeatureClasses("*", "Point","JTSK")

for fc in feaclass:
    print(fc)

def conflictDetection(newDataset,outputConflict):
    feaclass = arcpy.ListFeatureClasses("*", "Polygon", newDataset)

    # if not arcpy.Exists(outputConflict):
    #     arcpy.Delete_management(outputConflict)
    # arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputConflict, "POLYGON")

    for fc in feaclass:
        print("A: "+fc)
        arcpy.management.MakeFeatureLayer(fc, "fc.lyr")
        for fc2 in feaclass:
            print("B: " + fc2)
            arcpy.management.MakeFeatureLayer(fc2, "fc2.lyr")
            arcpy.cartography.DetectGraphicConflict("fc.lyr", "fc2.lyr", "outFcTemp")
            arcpy.management.Merge(["outFcTemp",outputConflict], "outputMergeTemp")
            arcpy.management.CopyFeatures("outputMergeTemp", outputConflict)

    arcpy.management.Delete("outFcTemp","outputMergeTemp","fc.lyr","fc2.lyr")
