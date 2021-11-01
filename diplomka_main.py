import arcpy
import json
import os

## definovani vstupu pres prikazovy radek (NEAKTUALNI)
# import sys
#
# # osetreni zadani chybneho poctu vstupu
# if len(sys.argv) != 5:
#     print('Chybny pocet argumentu')
#     exit(-1)
#
# # definovani vstupnich argumentu z prikazové radky
# try:
#     inputDatabase = os.path.abspath(sys.argv[1])
#     inputShape = sys.argv[2]
#     inputCoords = sys.argv[3]
#     output = sys.argv[4]
# except ValueError:
#     print('Chybne zadani nektereho z argumentu')
#     exit(-2)

# definovani vstupu ve skriptu (NEAKTUALNI)
inputDatabase = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
# inputShape = "ctverec_null_polygon"
# inputCoords = "kriz_vyber_5514"
# output = "shapesInPlacesSquere5514"

# definovani pracovního prostoru
arcpy.env.workspace = inputDatabase
arcpy.env.overwriteOutput = 1

def shapeDefinition(shapeInput,scale,epsg):
    """

    :param shapeInput: definice tvaru znaku
    :param scale:
    :param epsg:
    :return:
    """
    shapeOutput = []
    if epsg in [32633,5514]:
        for point in shapeInput:
            coord = []
            for num in point:
                 coord.append(num*(scale/1000))
            shapeOutput.append(coord)
    else:
        raise ValueError("Pro zadaný souřadnicový systém ve funkci shapeDefinition není definován výpočet")

    print(shapeOutput)
    return shapeOutput

def shapePlace(symbolsJSON, inputDataset, outputDataset, epsg, scale):
    """

    :param symbolsJSON:
    :param inputDataset:
    :param outputDataset:
    :param epsg:
    :param scale:
    :return:
    """

    # definování souradnicoveho systemu
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    # sr = arcpy.Describe(inputDataset).spatialReference

    # vytvoreni datasetu k ukladani
    if not arcpy.Exists(outputDataset):
        arcpy.Delete_management(outputDataset)
    arcpy.CreateFeatureDataset_management(arcpy.env.workspace, outputDataset, sr)

    # prochazeni definovanych znacek
    with open(symbolsJSON, encoding='UTF-8') as f:
        symbolsLoad = json.load(f)

    symbols = symbolsLoad['symbols']

    for symbol in symbols:
        print("zpracovavam " + symbol["name"])
        arcpy.CreateFeatureclass_management(outputDataset, symbol["name"]+"2", "POLYGON", "#", "#", "#", sr)

        output = outputDataset + "/" + symbol["name"]+"2"
        coords = inputDataset + "/" + symbol["name"]
        shape = shapeDefinition(symbol["definition"],scale,epsg)

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

def conflictDetection(newDataset,outputConflict):
    feaclass = arcpy.ListFeatureClasses("*", "Polygon", newDataset)

    if not arcpy.Exists(outputConflict):
        arcpy.Delete_management(outputConflict)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputConflict, "POLYGON")

    for fc in feaclass:
        print("A: "+fc)
        for fc2 in feaclass:
            print("B: " + fc2)
            if fc2 == fc:
                arcpy.intelligence.FindOverlaps(fc, "outFcTemp", "outCentroidTemp")
                arcpy.management.Merge(["outFcTemp", outputConflict], "outputMergeTemp")
                arcpy.management.CopyFeatures("outputMergeTemp", outputConflict)
            else:
                arcpy.analysis.Intersect([fc,fc2], "outFcTemp")
                arcpy.management.Merge(["outFcTemp",outputConflict], "outputMergeTemp")
                arcpy.management.CopyFeatures("outputMergeTemp", outputConflict)

    arcpy.management.Delete(["outFcTemp","outputMergeTemp","outCentroidTemp"])



#shape2 = shapeDefinition(inputShape_local,10000,"5514")
#shapePlace("znacky.json","JTSK","NOVY",5514,10000)
#conflictDetection("NOVY","CONFLICTpOKUS1")


