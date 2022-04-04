import arcpy
import json
import time
import math


# definovani pracovního prostoru
inputDatabase = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.workspace = inputDatabase
arcpy.env.overwriteOutput = 1

def shapeDefinition(shapeInput,scale,epsg):
    """
    Definuje tvar v metrech podle zadaného měřítka a souřadnicového systému.

    :param shapeInput: definice tvaru znaku v milimetrech jako seznam
    :param scale: meritkove cislo
    :param epsg: definice souradnicoveho systemu
    :return: seznam souradnic hranic znaku v bode 0
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

    return shapeOutput

def detectConflicts(clusterGeom):
    """
    Určí, zda mezi vstupními geometriemi dochází k průniku.

    :param clusterGeom: seznam acrpy geometrií, mezi kterými je třeba určit konflikt
    :return: Počet konfliktů ke kterým mezi geometriemi dochází
    """
    confNum = 0 # výsledná číselná hodnota
    confLoc = []

    for i in range(len(clusterGeom)):
        confLoc.append(0)


    # procházení konfliktních situací
    for g1 in range(len(clusterGeom)):
        for g2 in range(len(clusterGeom)):
            if g1 != g2 and g1 < g2:
                conf = clusterGeom[g1].disjoint(clusterGeom[g2])
                if not conf:
                    confNum += 1
                    confLoc[g1] += 1
                    confLoc[g2] += 1

                #print(str(g1) + " x " + str(g2) + " = " + str(conf))
                print("confLoc = " + str(confLoc))
    return confNum, confLoc

def netMake1(layersNumber, distance):
    """
    Vytvoří pravidelnou čtvercovou síť bodů na základě zadané vzdálenosti mezi body.

    :param layersNumber: počet vrstev v pravidelné síti (1 vrstva = síť 3x3, 2 vrstvy = síť 5x5)
    :param distance: vzdálenost mezi jednotlivými body
    :return:
    """
    net = {}
    size = layersNumber * 2 + 1
    num = 0
    # procházení bodů v síti
    for i in range(-layersNumber,layersNumber+1):
        y = i*distance
        for j in range(-layersNumber, layersNumber+1):
            x = j*distance
            # váha pozice pro její hodnocení jako přímá vzdálenost !!! KLÍČOVÉ PŘI UPRAVÁCH ALGORITMU !!!
            weight = math.sqrt(x**2+y**2)
            net[num] = {"xy":[x,y],"weight":weight}
            num += 1
    return net

def shapePlace(symbolsJSON, inputDataset, outputFeature, outputBuffer, epsg, scale):
    """
    Vytváří polygonovou vrstvu, kde jsou místo bodů z vybranych trid
    v datasetu ZABAGED vytvoreny polygony odpovídající kartografickému
    znaku pro danou třídu v zadaném měřítku a souřadnicovém systému.

    Krome toho vytvari vrstvu, která kolem zmíněných polygonů
    utvoří obalovou zonu podle maximálního povoleného posunu znaku.

    :param symbolsJSON: cesta k souboru s definici znakoveho klice
    :param inputDataset: cesta k datasetu vstupnich bodovych vrstev – nazvy trid musi byt shodne
    :param outputFeature: cesta k výslednému souboru s polygony
    :param outputBuffer: cesta k výslednému souboru s obalovými zónami podle maximálního povoleného posunu znaku
    :param epsg: souradnicovy system zadany EPSG kodem
    :param scale: meritkove cislo, pro ktere maji byt vypocitany velikosti polygonu
    :return:
    """
    print("DEFINUJI ZNAKY JAKO POLGONY NA ZADANÝCH SOUŘADNICÍCH")

    # definování souradnicoveho systemu
    sr = arcpy.SpatialReference(epsg) # EPSG kod
    # sr = arcpy.Describe(inputDataset).spatialReference

    # vytvoreni souboru k ukladani polygonů
    if not arcpy.Exists(outputFeature):
        arcpy.Delete_management(outputFeature)
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, outputFeature, "POLYGON", "#", "#", "#", sr)

    # přidání odpovídajících polí atributové tabulky
    arcpy.AddField_management(outputFeature, "X1", "DOUBLE")
    arcpy.AddField_management(outputFeature, "Y1", "DOUBLE")
    arcpy.AddField_management(outputFeature, "CLASS", "TEXT")
    arcpy.AddField_management(outputFeature, "SHIFT", "TEXT")
    arcpy.AddField_management(outputFeature, "CLUSTER", "SHORT")
    arcpy.AddField_management(outputFeature, "FID_ZBG", "TEXT")


    insCur = arcpy.da.InsertCursor(outputFeature,["SHAPE@", "X1", "Y1", "CLASS","SHIFT","CLUSTER","FID_ZBG"])

    # prochazeni definovanych znacek
    with open(symbolsJSON, encoding='UTF-8') as f:
        jsonLoad = json.load(f)

    symbols = jsonLoad['symbols']

    # list všech zpracovaných tříd pro kontrolu při výstupu
    controlOutput = []

    # vykreslení symbolů na souřadnice
    for symbol in symbols:
        print("zpracovavam " + symbol["name"])

        coords = inputDataset + "/" + symbol["name"]
        shape = shapeDefinition(symbol["definition"],scale,epsg)

        # výjimka pro případ chybného definování názvu znaku
        try:
            seaCur = arcpy.da.SearchCursor(coords, ["SHAPE@","FID_ZBG"])
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
            insCur.insertRow((polygon, pnt1.X,pnt1.Y,symbol["name"],symbol["allowedShift"],0,row[1]))

    del insCur

    # vypsání tříd z datasetu, které nebyly zpracovány
    controlInput = arcpy.ListFeatureClasses("","All",inputDataset)
    control = list(set(controlInput) - set(controlOutput))
    print("Nezpracované třídy: {}".format(control))
    print("Z celkových {} tříd bylo {} zpracováno a {} nezpracováno.".format(len(controlInput),len(controlOutput), len(control)))

    # vytvoreni souboru s obalovými zónami
    arcpy.analysis.Buffer(outputFeature, outputBuffer, "SHIFT")

def clusterDefinition(inputFeature,inputBuffer):
    """
    Přiřadí do souboru inputFeature atribut určující u každého polygonu příslušnost ke konkrétnímu shluku.

    :param inputFeature: umístění souboru se znaky
    :param inputBuffer: umístění souboru s obalovými zónami
    :return:
    """
    print("\nDEFINUJI SHLUKY ZNAKŮ")
    seconds1 = time.time()

    # vytvoření vrstvy všech konfliktů
    arcpy.analysis.Intersect(inputBuffer, "intersectFeatureClass")
    arcpy.management.Dissolve("intersectFeatureClass", "outOverlapTemp", ["Shape_Area"], "#", "SINGLE_PART")

    #přiřazení konfliktů k znakům
    #arcpy.intelligence.FindOverlaps(inputBuffer, "outOverlapTemp", "outCentroidTemp")
    arcpy.analysis.SpatialJoin(inputBuffer, "outOverlapTemp", "outSpatialTemp", "JOIN_ONE_TO_MANY", "KEEP_COMMON",
                               "#", "CONTAINS", 0)

    arcpy.management.Sort("outSpatialTemp", "outSortTemp", [["JOIN_FID", "ASCENDING"]])

    # rozřazování do clusterů
    seaCur = arcpy.da.SearchCursor("outSortTemp",["ORIG_FID","JOIN_FID"])
    controlShape = 1
    clusterNum = 1
    outputDict = {}
    for row in seaCur:
        if controlShape == row[1]:
            id=row[0]

            # kontrola skutečnosti, že znak není v žádném clusteru
            if id not in outputDict:
                outputDict[id]=clusterNum

            # přepsání clusteru, pokud už je znak zařazen
            else:
                x = outputDict[id]
                for kay,value in outputDict.items():
                    if value == x:
                        outputDict[kay] = clusterNum

        # přechod na další konflikt
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

    print("Přehled přiřazení do clusterů:" + str(outputDict))

    # zapsání clusteru do zdrojového souboru
    with arcpy.da.UpdateCursor(inputFeature, ['OBJECTID', 'CLUSTER']) as upCurs:
        for row in upCurs:
            #row[1] = 2
            try: row[1] = outputDict[row[0]]
            except KeyError: continue
            upCurs.updateRow(row)

    del seaCur
    #arcpy.management.Delete("'outSpatialTemp';'outSortTemp';'outOverlapTemp';'outCentroidTemp';'intersectFeatureClass'")

    seconds2 = time.time()
    print("Clustery byly definovány za {} sekund".format((seconds2 - seconds1)))

def clusterSolve(inputFeature,cluster,distance,outputFeature):
    """
    Vrátí nejlepší řešení konfliktu mezi znaky v jednom shluku podle zadaných parametrů.

    :param inputFeature: cesta k souboru, ze kterého je brána geometrie
    :param cluster: cluster, pro který je problém řešený
    # DALŠÍ PARAMETRY MOHOU BÝT KLÍČOVÉ PŘI UPRAVÁCH ALGORITMU !!!
    :param distance: Rozestupy mezi pozicemi v síti
    :param outputFeature: cesta k souboru, do kterého jsou ukládány polygony znaků v nejlepší konfiguraci
    :return:
    """

    seconds1 = time.time()

    print("\nŘEŠÍM CLUSTER {}".format(cluster))
    dict = {} # slovník, který obsahuje identifikaci znaku a seznam geometrií na možných pozicích po provedení posunu


    # výběr znaků ve shluku z celkové množiny znaků
    clust = arcpy.SelectLayerByAttribute_management(inputFeature, "NEW_SELECTION","CLUSTER = "+str(cluster))


    # vybrané atributy !!! MŮŽE BÝT KLÍČOVÉ PRO ZADÁNÍ PARAMETRŮ PŘI UPRAVÁCH ALGORITMU !!!
    seaCur = arcpy.da.SearchCursor(clust, ["SHAPE@","OBJECTID", "CLASS","SHIFT","X1","Y1","FID_ZBG"])

    symbolNum = 0 # identifikační číslo znaku v slovníku – spojité od 0 do n
    for row in seaCur:
        # definování sítě pro jednotlivé znaky !!! KLÍČOVÉ PRO ZADÁNÍ PARAMETRŮ PŘI UPRAVÁCH ALGORITMU !!!
        net = netMake1(int(int(row[3]) / distance), distance)

        geomAll = [] # seznam geometrií pro body v síti jednoho znaku
        weightAll = [] # seznam váhy jednotlivých geometrií
        geom = row[0] # jedna geometrie v seznamu

        # vytvoření geometrie na místa v síti
        for netPoint in net: #procházím body v síti
            part = arcpy.Array() # pole do kterého nahraji tvar
            for point in geom: # procházím body z polygonu znaku
                for nod in point: # procházím souřadnice v bodě
                    pnt = arcpy.Point(nod.X+net[netPoint]["xy"][0], nod.Y+net[netPoint]["xy"][1])
                    part.add(pnt)
            # vytvoření polygonu z pole
            polygon = arcpy.Polygon(part)
            geomAll.append(polygon)
            weightAll.append(net[netPoint]["weight"])
            # vyčištění pole
            part.removeAll()

        dict[symbolNum] = {"id":row[6],"geom":geomAll,"weight":weightAll,"x":row[4],"y":row[5],"class":row[2]} #class by mělo být nahrazeno nějakým unikátním id
        # arcpy.CopyFeatures_management(geomAll, "tvar"+str(symbolNum))

        symbolNum += 1
    del seaCur

    print("Obsah clusteru: " + str(dict))

    # ověření, jestli opravdu existuje konflikt, v případě, že jsme bez konfliktu, je nejvhodnějším výstupem výchozí rozložení
    geometries = arcpy.CopyFeatures_management(clust, arcpy.Geometry())
    detectNum,detectLoc = detectConflicts(geometries)
    if detectNum == 0:
        # vložení původních geometrií do výstupu s potřebnými informacemi
        insCur = arcpy.da.InsertCursor(outputFeature, ["SHAPE@", "X1", "Y1", "FID_ZBG", "CLASS"])
        for pos in range(len(dict)):
            insCur.insertRow((geometries[pos], dict[pos]["x"], dict[pos]["y"], dict[pos]["id"],dict[pos]["class"]))
        del insCur
        print("Cluster {} je bez konfliktů.".format(cluster))
        return

    # vymazání sítě pro znaky, které nejsou v původním nastavení v konfliktu
    for d in range(len(dict)):
        if detectLoc[d] == 0:
            dict[d]["geom"] = [geometries[d]]
            dict[d]["weight"] = [0.0]

    def configuration(dict):
        """

        :param cfg:
        :param dict:
        :return:
        """
        outputGeometries = []
        winner = []
        winnerWeight = 999999999999999
        maxWeight = 0
        for wg in range(len(dict)):
            maxActual = max(dict[wg]["weight"])
            if maxActual > maxWeight:
                maxWeight = maxActual

        cfg = []  # konfigurace pozicí znaků

        # nastavení nul jakožto výchozích pozic v konfiguraci
        for num in range(len(dict)):
            cfg.append(0)

        # rekurzivní procházení konfigurací vázaných na její určitou pozici
        def next(cfg, i, winnerWeight, winner,dict):
            while cfg[i] < len(dict[i]["geom"]) - 1:
                #print(cfg)

                # otestování konfliktu
                clusterGeom =[] # všechny geometrie aktuální konfigurace
                actualWeight = 0
                for g in range(len(dict)):
                    clusterGeom.append(dict[g]["geom"][cfg[g]])
                    actualWeight += dict[g]["weight"][cfg[g]]


                # tvorba výstupu
                detect,detectLoc = detectConflicts(clusterGeom)

                print("Pro konfiguraci {} nalezeno {} konfliktů.".format(cfg,detect))

                if detect != 0:
                    actualWeight += detect*maxWeight

                if actualWeight < winnerWeight:
                    winner = list(cfg)
                    winnerWeight = actualWeight
                    # print("Tato konfigurace je aktuálně nejlepší s váhou: {}".format(winnerWeight))


                # konec testování a tvorby výstupu

                cfg[i] += 1

                j = i
                while j != 0:
                    j -= 1
                    winnerWeight, winner = next(cfg, j, winnerWeight, winner,dict)

            cfg[i] = 0
            return winnerWeight, winner

        # procházení pozic v konfiguraci a volání funkce

        for x in range(len(cfg)):
            # print("další forcyklus")
            winnerWeight, winner = next(cfg, x, winnerWeight, winner,dict)

        if winner == []:
            print("Při současném nastacení pro shluk neexistuje žádné lepší řešení než výchozí")
            # arcpy.CopyFeatures_management(geometries, "best164")
            winner += cfg
        return winner

    winnerCFG = configuration(dict)

    seconds2 = time.time()
    print("Cluster {}, který obsahuje {} znaků, je vyřešen za {} sekund.".format(cluster,len(dict),(seconds2-seconds1)))

    insCur = arcpy.da.InsertCursor(outputFeature, ["SHAPE@","X1","Y1","FID_ZBG","CLASS"])
    for pos in range(len(dict)):
        insCur.insertRow((dict[pos]["geom"][winnerCFG[pos]],dict[pos]["x"],dict[pos]["y"],dict[pos]["id"],dict[pos]["class"]))
    del insCur

mainFeature = "FeatureTest2"
mainBuffer = mainFeature + "_Buffer"
mainOutput = "bestOutput9"
mainSR = 5514

#shapePlace("znacky.json","JTSK_1","T2feature","T2buffer",mainSR,10000)
#clusterDefinition(mainFeature,mainBuffer)

seaCur_clust = arcpy.da.SearchCursor(mainFeature, ["CLUSTER"])
clusters = []
clusterGeometries = []

for row in seaCur_clust:
    if row[0] not in clusters:
        clusters.append(row[0])

arcpy.CreateFeatureclass_management(arcpy.env.workspace, mainOutput, "POLYGON", "#", "#", "#", mainSR)

# přidání odpovídajících polí atributové tabulky
arcpy.AddField_management(mainOutput, "X1", "DOUBLE")
arcpy.AddField_management(mainOutput, "Y1", "DOUBLE")
arcpy.AddField_management(mainOutput, "CLASS", "TEXT")
arcpy.AddField_management(mainOutput, "FID_ZBG", "TEXT")

# clustery seřazené podle počtu prvků
#clusters = [118, 88, 94, 117, 110]
clusters = [29]

for cluster in clusters:
    clusterSolve(mainFeature,cluster,5,mainOutput)


