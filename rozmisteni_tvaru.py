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
    arcpy.AddField_management(output,"SOURADNICE","TEXT")


    #InsertCursor, kterým budu vkládat výsledné tvary
    insCur = arcpy.da.InsertCursor(output,["SHAPE@","SOURADNICE"])
    #SearchCursor na procházení souřadnic bodů
    seaCur = arcpy.da.SearchCursor(souradnice, ["SHAPE@"])

    for row in seaCur:
        #zjisteni souradnic bodu
        geom = row[0]
        pnt1 = geom.getPart(0)

        #pole do kterého nahraji tvar
        part = arcpy.Array()
        #nahrání tvaru s posunem do pole
        for nod in tvar:
            pnt2 = arcpy.Point(nod[0]+pnt1.X,nod[1]+pnt1.Y)
            part.add(pnt2)
        #vytvoření polygonu z pole
        polygon = arcpy.Polygon(part)
        #vyčištění pole
        part.removeAll()
        insCur.insertRow((polygon,str(pnt1.X)+", "+str(pnt1.Y)))
    del insCur


output = "tvar_pokus"
epsg = 32633
tvar = TvarFeatureClass("kriz_null_DetectGraphicConfl1")
souradnice = "kriz_vyber_Project"

UmisteniTvaru(tvar,souradnice,epsg,output)






