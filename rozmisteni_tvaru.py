import arcpy

#definovani pracovního prostoru
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.overwriteOutput = 1

def TvarFeatureClass (featureClass):
    """

    :param featureClas:
    :return: Tvar ve formě seznamu
    """
    # vytvorime kurzor
    seaCur = arcpy.da.SearchCursor(featureClass, ["OBJECTID", "SHAPE@"])

    # pro kazdy zaznam v souboru ke zpracovani
    for row in seaCur:
        geom = row[1]
        part = geom.getPart(0)
        pnt = part.next()
        tvar = []
        while pnt:
            tvar.append([pnt.X, pnt.Y])
            # a ber dalsi
            pnt = part.next()
            # ošetření polygonu s dírou
            if not pnt:
                pnt = part.next()
                if pnt:
                    print("Dira v polygonu:")

    # smazeme kurzor (uvolnime zamek)
    print(tvar)
    del seaCur
    return tvar

def UmisteniTvaru(tvar,souradnice,epsg,output):
    """
    Funkce zadaná tvary rozmístí jako jednotlivé polygony na zadané souřadnice
    :param tvar: Tvar definovaný souřadnicemi v seznamu
    :param souradnice: Souřadnice bodů
    :param epsg: Souřadnicový systém definovaný EPSG
    :param output: Feature Class, do které se polygony zapíšou
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
tvar = TvarFeatureClass("kriz_null_DetectGraphicConfl1")
souradnice = "kriz_vyber_Project"

UmisteniTvaru(tvar,0,epsg,output)






