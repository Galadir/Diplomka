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
    Definuje tvar v metrech podle zadaného měřítka a souřadnicového systému.

    :param shapeInput: definice tvaru znaku
    :param scale: meritkove cislo
    :param epsg: definice souradnicoveho systemu
    :return: seznam souradnic hranic prvku v bode 0
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

def shapePlace(symbolsJSON, inputDataset, outputFeature, outputBuffer, epsg, scale):
    """

    :param symbolsJSON: cesta k souboru s definici znaku v mm
    :param inputDataset: feature dataset bodovych vrstev
    :param outputFeature: jmeno datasetu s polygonovymi vrstvami
    :param outputBuffer: jméno souboru s bufferem definujícím maximální posun
    :param epsg: souradnicovy system
    :param scale: meritkove cislo
    :return:
    """

    # definování souradnicoveho systemu
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    # sr = arcpy.Describe(inputDataset).spatialReference

    # vytvoreni datasetu k ukladani
    if not arcpy.Exists(outputFeature):
        arcpy.Delete_management(outputFeature)

    arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputFeature, "POLYGON", "#", "#", "#", sr)

    arcpy.AddField_management(outputFeature, "SOURADNICE", "TEXT")
    arcpy.AddField_management(outputFeature, "KATEGORIE", "TEXT")
    arcpy.AddField_management(outputFeature, "SHIFT", "TEXT")
    arcpy.AddField_management(outputFeature, "CLUSTER", "SHORT")


    insCur = arcpy.da.InsertCursor(outputFeature,["SHAPE@", "SOURADNICE","KATEGORIE","SHIFT","CLUSTER"])

    # prochazeni definovanych znacek
    with open(symbolsJSON, encoding='UTF-8') as f:
        symbolsLoad = json.load(f)

    symbols = symbolsLoad['symbols']

    for symbol in symbols:
        print("zpracovavam " + symbol["name"])

        coords = inputDataset + "/" + symbol["name"]
        shape = shapeDefinition(symbol["definition"],scale,epsg)

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
            insCur.insertRow((polygon, str(pnt1.X)+", "+str(pnt1.Y),symbol["name"],symbol["allowedShift"],0))

    del insCur

    # vytvoreni bufferu resici mozne posuny
    arcpy.analysis.Buffer(outputFeature, outputBuffer, "SHIFT")


def conflictDetection(newDataset,outputConflict):
    """

    :param newDataset: dataset s polygonovymi vrstvami
    :param outputConflict: jmeno feature class s ulozenymi konflikty
    :return:
    """
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

def clusterDefinition(inputFeature,inputBuffer):
    arcpy.analysis.Intersect(inputBuffer, "intersectFeatureClass")


    seaCur = arcpy.da.SearchCursor("intersectFeatureClass",["ORIG_FID","Shape_Area"])
    controlShape = 1
    clusterNum = 1
    outputDict = {}
    for row in seaCur:
        if controlShape == row[1]:
            id=row[0]
            if id not in outputDict:
                outputDict[id]=clusterNum
            else:
                x = outputDict[id]
                for kay,value in outputDict.items():
                    if value == x:
                        outputDict[kay] = clusterNum
        else:
            controlShape = row[1]
            clusterNum += 1
            id = row[0]
            if id not in outputDict:
                outputDict[id] = clusterNum
            else:
                x = outputDict[id]
                for kay, value in outputDict.items():
                    if value == x:
                        outputDict[kay] = clusterNum

    print(outputDict)
    with arcpy.da.UpdateCursor(inputFeature, ['OBJECTID', 'CLUSTER']) as upCurs:
        for row in upCurs:
            #row[1] = 2
            try: row[1] = outputDict[row[0]]
            except KeyError: continue
            upCurs.updateRow(row)

    del seaCur

def nullCluster(inputFeature):
    with arcpy.da.UpdateCursor(inputFeature, ['OBJECTID', 'CLUSTER']) as upCurs:
        for row in upCurs:
            row[1] = 0
            upCurs.updateRow(row)

#shape2 = shapeDefinition(inputShape_local,10000,"5514")
#shapePlace("znacky.json","JTSK","shapePlace_comb","shapePlace_buff",5514,10000)
clusterDefinition("shapePlace_comb","shapePlace_buff")
#nullCluster("shapePlace_comb")
#conflictDetection("NOVY","CONFLICTpOKUS1")


