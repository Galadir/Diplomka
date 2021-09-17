import arcpy

#definovani pracovního prostoru
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.overwriteOutput = 1

def UmisteniTvaru(tvar,souradnice,epsg,output):
    """
    Funkce zadaná tvary rozmístí jako jednotlivé polygony na zadané souřadnice
    :param tvar: Tvar definovaný souřadnicemi v seznamu
    :param souradnice: Souřadnice bodů
    :param epsg: Souřadnicový systém definovaný EPSG
    :param output: Feature Layer, do které se polygony zapíšou
    :return: 
    """

    #definování outputu
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    if not arcpy.Exists(output):
        arcpy.Delete_management(output)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, output, "POLYGON", "#", "#", "#", sr)
    arcpy.AddField_management(output,"VALUE","SHORT")

    #InsertCursor, kterým budu vkládat výsledné tvary
    insCur = arcpy.da.InsertCursor(output,["SHAPE@","VALUE"])

    # vytvoření pole, do kterého nahraji souřadnice
    part = arcpy.Array()
    #proměnná, do které budu ukládat jednotlívé tvary
    features = []

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


output = "tvar_pokus"
epsg = 32633
tvar = [
    [0,20],
    [0,0],
    [30,0],
    [30,30],
    [0,20]
]


UmisteniTvaru(tvar,0,epsg,output)






