import arcpy
import os
import sys

# osetreni zadani chybneho poctu vstupu
if len(sys.argv) != 5:
    print('Chybny pocet argumentu')
    exit(-1)

# definovani vstupnich argumentu z prikazové radky
try:
    inputDatabase = os.path.abspath(sys.argv[1])
    inputShape = sys.argv[2]
    inputCoords = sys.argv[3]
    output = sys.argv[4]
except ValueError:
    print('Chybne zadani nektereho z argumentu')
    exit(-2)

# definovani pracovního prostoru
arcpy.env.workspace = inputDatabase
arcpy.env.overwriteOutput = 1


def shapeToList(featureClass):
    """
    :param featureClass: umístění souboru obsahujícícho polygon určující značku na nulových souřadnicích
    :return: Tvar ve formě seznamu
    """
    # tvorba kurzoru
    seaCur = arcpy.da.SearchCursor(featureClass, ["OBJECTID", "SHAPE@"])

    #uložení jednoho záznamu do seznamu shape
    for row in seaCur:
        geom = row[1]
        part = geom.getPart(0)
        pnt = part.next()
        shape = []
        while pnt:
            shape.append([pnt.X, pnt.Y])
            pnt = part.next()

            # ošetření polygonu s dírou
            if not pnt:
                pnt = part.next()
                if pnt:
                    print("Dira v polygonu:")

    del seaCur
    return shape


def shapePlace(shape, coords, output):
    """
    Funkce zadaná tvary rozmístí jako jednotlivé polygony na zadané souřadnice
    :param shape: Tvar definovaný souřadnicemi v seznamu
    :param coords: Souřadnice bodů
    :param output: Feature Class, do které se polygony zapíšou
    :return: 
    """

    # definování outputu
    # sr = arcpy.SpatialReference(epsg) # EPSG kod
    sr = arcpy.Describe(coords).spatialReference

    if not arcpy.Exists(output):
        arcpy.Delete_management(output)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, output, "POLYGON", "#", "#", "#", sr)
    arcpy.AddField_management(output, "SOURADNICE", "TEXT")

    # InsertCursor, kterým budu vkládat výsledné tvary
    insCur = arcpy.da.InsertCursor(output, ["SHAPE@", "SOURADNICE"])
    # SearchCursor na procházení souřadnic bodů
    seaCur = arcpy.da.SearchCursor(coords, ["SHAPE@"])

    for row in seaCur:
        # zjisteni souradnic bodu
        geom = row[0]
        pnt1 = geom.getPart(0)

        # pole do kterého nahraji tvar
        part = arcpy.Array()
        # nahrání tvaru s posunem do pole
        for nod in shape:
            pnt2 = arcpy.Point(nod[0]+pnt1.X, nod[1]+pnt1.Y)
            part.add(pnt2)
        # vytvoření polygonu z pole
        polygon = arcpy.Polygon(part)
        # vyčištění pole
        part.removeAll()
        insCur.insertRow((polygon, str(pnt1.X)+", "+str(pnt1.Y)))
    del insCur


shape1 = shapeToList(inputShape)
shapePlace(shape1, inputCoords, output)
