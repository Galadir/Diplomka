import arcpy
import json
import time
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
    Vytváří polygonovou vrstvu, kde jsou místo bodů z vybranych trid
    v datasetu ZABAGED vytvoreny polygony odpovídající kartografickému
    znaku pro danou třídu v zadaném měřítku a souřadnicovém systému.

    Krome toho vytvari polygonovou vrstvu, která kolem zmíněných polygonů
    utvoří obalovou zonu podle maximálního povoleného posunu znaku.

    :param symbolsJSON: cesta k souboru s definici znakoveho klice
    :param inputDataset: cesta k datasetu vstupnich bodovych vrstev – nazvy trid musi byt shodne
    :param outputFeature: cesta k výslednému souboru s polygony
    :param outputBuffer: cesta k výslednému souboru s obalovými zónami podle maximálního povoleného posunu znaku
    :param epsg: souradnicovy system zadany EPSG kodem
    :param scale: meritkove cislo, pro ktere maji byt vypocitany velikosti polygonu
    :return:
    """

    # definování souradnicoveho systemu
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    # sr = arcpy.Describe(inputDataset).spatialReference

    # vytvoreni datasetu k ukladani polygonů
    if not arcpy.Exists(outputFeature):
        arcpy.Delete_management(outputFeature)

    arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputFeature, "POLYGON", "#", "#", "#", sr)

    # přidání odpovídajících polí atributové tabulky
    arcpy.AddField_management(outputFeature, "X1", "DOUBLE")
    arcpy.AddField_management(outputFeature, "Y1", "DOUBLE")
    arcpy.AddField_management(outputFeature, "CLASS", "TEXT")
    arcpy.AddField_management(outputFeature, "SHIFT", "TEXT")
    arcpy.AddField_management(outputFeature, "CLUSTER", "SHORT")


    insCur = arcpy.da.InsertCursor(outputFeature,["SHAPE@", "X1", "Y1", "CLASS","SHIFT","CLUSTER"])

    # prochazeni definovanych znacek
    with open(symbolsJSON, encoding='UTF-8') as f:
        jsonLoad = json.load(f)

    symbols = jsonLoad['symbols']

    # list všech zpracovaných tříd pro kontrolu při výstupu
    controlOutput = []

    for symbol in symbols:
        print("zpracovavam " + symbol["name"])

        coords = inputDataset + "/" + symbol["name"]
        shape = shapeDefinition(symbol["definition"],scale,epsg)

        # výjimka pro případ chybného definování názvu znaku
        try:
            seaCur = arcpy.da.SearchCursor(coords, ["SHAPE@"])
        except RuntimeError:
            print("\nNEZPRACOVÁNO '" + coords + "': soubor s tímto názvem pravděpodobně neexistuje \n \n")
            continue

        # přidání symbolu do seznamu zpracovaných tříd pro kontrolu výstupu
        controlOutput.append(symbol["name"])

        # SearchCursor na procházení souřadnic bodů
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
            insCur.insertRow((polygon, pnt1.X,pnt1.Y,symbol["name"],symbol["allowedShift"],0))

    del insCur

    # vypsání tříd z datasetu, které nebyly zpracovány
    controlInput = arcpy.ListFeatureClasses("","All",inputDataset)
    control = list(set(controlInput) - set(controlOutput))
    print("Nezpracované třídy: {}".format(control))
    print("Z celkových {} tříd bylo {} zpracováno a {} nezpracováno.".format(len(controlInput),len(controlOutput), len(control)))

    # vytvoreni souboru s obalovými zónami
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
    seconds1 = time.time()

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
    seconds2 = time.time()
    print(seconds2 - seconds1)

def clusterDefinition2(inputFeature,inputBuffer,outputFeature ):
    seconds1 = time.time()

    arcpy.management.Dissolve(inputBuffer, "cluster")

    arcpy.analysis.Identity(inputFeature, "cluster", outputFeature, "ONLY_FID")
    arcpy.management.Delete("cluster")
    seconds2 = time.time()
    print(seconds2 - seconds1)

def clusterDefinition3(inputFeature,inputBuffer):
    seconds1 = time.time()

    #arcpy.analysis.Intersect(inputBuffer, "intersectFeatureClass")
    arcpy.intelligence.FindOverlaps(inputBuffer, "outOverlapTemp", "outCentroidTemp")
    arcpy.analysis.SpatialJoin(inputBuffer, "outOverlapTemp", "outSpatialTemp", "JOIN_ONE_TO_MANY", "KEEP_COMMON",
                               "#", "CONTAINS", 0)

    arcpy.management.Sort("outSpatialTemp", "outSortTemp", [["JOIN_FID", "ASCENDING"]])


    seaCur = arcpy.da.SearchCursor("outSortTemp",["ORIG_FID","JOIN_FID"])
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
    arcpy.management.Delete("'outSpatialTemp';'outSortTemp';'outOverlapTemp';'outCentroidTemp'")

    seconds2 = time.time()
    print(seconds2 - seconds1)

def nullCluster(inputFeature):
    with arcpy.da.UpdateCursor(inputFeature, ['OBJECTID', 'CLUSTER']) as upCurs:
        for row in upCurs:
            row[1] = 0
            upCurs.updateRow(row)

#shape2 = shapeDefinition(inputShape_local,10000,"5514")
shapePlace("znacky.json","JTSK","T6shapePlace_comb","T6shapePlace_buff",5514,10000)
#nullCluster("T4shapePlace_comb")
#clusterDefinition3("T4shapePlace_comb","T4shapePlace_buff")
#clusterDefinition2("T4shapePlace_comb","T4shapePlace_buff","T4shapePlace_clust2")

#conflictDetection("NOVY","CONFLICTpOKUS1")


