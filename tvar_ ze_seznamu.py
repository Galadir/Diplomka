import arcpy

#definovani pracovního prostoru
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.overwriteOutput = 1

sr = arcpy.SpatialReference(32633) # EPSG kod
if not arcpy.Exists("tvar_pokus"):
    arcpy.Delete_management("tvar_pokus")
arcpy.CreateFeatureclass_management(arcpy.env.workspace, "tvar_pokus", "POLYGON", "#", "#", "#", sr)
arcpy.AddField_management("tvar_pokus","VALUE","SHORT")

output = "tvar_pokus"


tvar = [
    [0,30],
    [0,0],
    [30,0],
    [30,30],
    [0,30]
]
#InsertCursor, kterým budu vkládat výsledné tvary
insCur = arcpy.da.InsertCursor(output,["SHAPE@","VALUE"])

#proměnná, do které budu ukládat jednotlívé tvary
#features = []

#vytvoření pole, do kterého nahraji souřadnice
part = arcpy.Array()

#nahrání tvaru do pole
for i in tvar:
    pnt = arcpy.Point(i[0],i[1])
    part.add(pnt)

#vytvoření polygonu z pole
polygon = arcpy.Polygon(part)
#vyčištění pole
#part.removeAll()
#features.append(polygon)

print(polygon)
insCur.insertRow((polygon,1))
del insCur
