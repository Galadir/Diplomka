import arcpy

#definovani pracovního prostoru
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.overwriteOutput = 1

def UmisteniTvaru(tvar,souradnice,epsg,output):"""
Funkce zadaná tvary rozmístí jako jednotlivé polygony na zadané souřadnice
    :param tvar: Tvar definovaný souřadnicemi v seznamu
    :param souradnice: Souřadnice bodů
    :param epsg: Souřadnicový systém definovaný EPSG
    :param output: Feature Layer, do které se polygony zapíšou
    :return: 
    """
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    if not arcpy.Exists(output):
        arcpy.Delete_management(output)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, output, "POLYGON", "#", "#", "#", sr)
    arcpy.AddField_management(output,"VALUE","SHORT")

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
