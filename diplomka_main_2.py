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
    :param epsg: definice souřadnicového systemu
    :return: shapeOutput = seznam souradnic hranic znaku v bode 0
    """
    shapeOutput = []
    # převod pro metrické souřadnicové systémy
    if epsg in [32633,5514]:
        for point in shapeInput:
            coord = []
            for num in point:
                # přepočítání dle zadaného měřítka do metrů
                 coord.append(num*(scale/1000))
            shapeOutput.append(coord)
    else:
        raise ValueError("Pro zadaný souřadnicový systém ve funkci shapeDefinition není definován výpočet")

    return shapeOutput

def detectConflicts(clusterGeom):
    """
    Určí, zda mezi vstupními geometriemi dochází k průniku.

    :param clusterGeom: seznam acrpy geometrií, mezi kterými je třeba určit konflikt
    :return: confNum = Počet konfliktů ke kterým mezi geometriemi dochází, confLoc = seznam definující umístění konfliktů
    """
    confNum = 0 # výsledná číselná hodnota
    confLoc = [] # seznam s přehledem konfliktů vzhledem ke znakům ve shluku

    # nastavení hodnot výstupního seznamu s přehledem konfliktů na 0
    for i in range(len(clusterGeom)):
        confLoc.append(0)


    # procházení konfliktních situací
    for g1 in range(len(clusterGeom)):
        for g2 in range(len(clusterGeom)):
            if g1 != g2 and g1 < g2:
                # určení konfliktu arcpy geometrii, FALSE, pokud existuje konflikt
                conf = clusterGeom[g1].disjoint(clusterGeom[g2])
                if not conf:
                    confNum += 1
                    confLoc[g1] += 1
                    confLoc[g2] += 1

                #print(str(g1) + " x " + str(g2) + " = " + str(conf))
    print("Počty konfliktů vzhledem k znakům ve shluku: " + str(confLoc))
    return confNum, confLoc

def netMake1(layersNumber, distance):
    """
    Vytvoří pravidelnou čtvercovou síť bodů na základě zadané vzdálenosti mezi body.

    :param layersNumber: počet vrstev v pravidelné síti (1 vrstva = síť 3x3, 2 vrstvy = síť 5x5)
    :param distance: vzdálenost mezi jednotlivými body
    :return: net = slovník jednotlivých pozic v síti, kde hodnotou je umístění jeho váha
    """
    net = {} # seznam pozic v síti
    size = layersNumber * 2 + 1
    num = 0 # aktuální id místa v síti

    # procházení bodů v síti
    for i in range(-layersNumber,layersNumber+1):
        y = i*distance
        for j in range(-layersNumber, layersNumber+1):
            x = j*distance
            # váha pozice pro její hodnocení jako přímá vzdálenost !!! KLÍČOVÉ PŘI UPRAVÁCH ALGORITMU !!!
            weight = math.sqrt(x**2+y**2)
            # vytvoření pozice v síti "xy" = pozice vzhledem k původnímu umístění, "weight" = váha pozice
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
    :return: xxx vytváří soubor s polygony znaků a jejich buffer
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
    :return: xxx přepisuje atribut CLUSTER v atributové tabulce feature class
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

def rasterComparsion(conf, dict):
    """
    Převede polygony znaků v konfiguraci na rastry a pomocí raster calculater je sečte, aby se určila velikost překryvů.

    :param conf: aktuální konfigurace znaků
    :param dict: slovník s přehledem všech znaků a jejich geometrií
    :return: tableSum = součet všech hodnot větších než 1 ve výsledném rastru
    """

    dictNum = 0  # volba objektu ve slovníku

    rasterNames = [] # seznam pojmenování rastrů pro jednotlivé znaky podle ID znaku ve slovníku (dict) a umístění konkrétní geometrie v seznamu, který slovník obsahuje
    expression = "" # výraz pro raster calculater

    for cg in conf:
        rasterName = "r"+str(dictNum)+str(cg) # jmeno konkrétního rastru
        if expression != "":
            expression += "+"

        # vytvoření rastru pro znak, pokud ještě neexistuje
        if not arcpy.Exists(rasterName):
            # feature class z geometrie, kvůli vstupu do PolygonToRaster NEJDE NĚJAK VYNECHAT?
            arcpy.management.CopyFeatures(dict[dictNum]["geom"][cg],"temp_cgGeom")
            arcpy.conversion.PolygonToRaster("temp_cgGeom", "OBJECTID", "temp_" + rasterName, "MAXIMUM_AREA", "#", 4)
            # převod Null na integer 0
            raster = arcpy.sa.Con(arcpy.sa.IsNull("temp_" + rasterName), 0, "temp_" + rasterName)
            raster.save(str(rasterName))
            arcpy.Delete_management("temp_" + rasterName)
            arcpy.Delete_management("temp_smbGeom")
        rasterNames.append(rasterName)
        expression += rasterName
        dictNum += 1

    expression = "int("+expression+")"
    outRaster = arcpy.sa.RasterCalculator(rasterNames,rasterNames,expression)

    # pojmenování rastru s výsledným porovnáním (LZE VYNECHAT A PŘEPISOVAT JEDEN)
    outputName = ""
    for name in rasterNames:
        outputName += name
    outputName2 = outputName+"2"
    outRaster.save(outputName)
    outRaster.save(outputName2)

    # získání celkového součtu hodnot větších než 1
    arcpy.sa.ZonalStatisticsAsTable(outputName, "Value", outputName2, "tab_"+outputName, "NODATA", "SUM")
    arcpy.Delete_management(outputName2)
    tableSeaCur = arcpy.da.SearchCursor("tab_"+outputName, ["Value", "COUNT", "SUM"])
    tableSum = 0
    for row in tableSeaCur:
        if row[0] > 1:
            tableSum += row[2]
    print("tableSum: "+str(tableSum))
    return tableSum

def clusterSolve(inputFeature, inputBuffer, cluster,distance,outputFeature,sr, withoutRaster):
    """
    Vrátí nejlepší řešení konfliktu mezi znaky v jednom shluku podle zadaných parametrů.

    :param inputFeature: cesta k souboru, ze kterého je brána geometrie
    :param cluster: cluster, pro který je problém řešený
    # DALŠÍ PARAMETRY MOHOU BÝT KLÍČOVÉ PŘI UPRAVÁCH ALGORITMU !!!
    :param distance: Rozestupy mezi pozicemi v síti
    :param outputFeature: cesta k souboru, do kterého jsou ukládány polygony znaků v nejlepší konfiguraci
    :param withoutRaster: boolean, pokud je True, nevytváří se rastry k porovnání
    :return: xxx vytvoří soubor s posunutými polygonovými znaky
    """
    # začátek měření času průběhu funkce
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

    # definování rozsahu znaků (včetně možných posunů) pro tvorby rastru
    # clustBuffer = arcpy.SelectLayerByAttribute_management(inputBuffer, "NEW_SELECTION", "CLUSTER = " + str(cluster))
    arcpy.analysis.Buffer(clust, "temp_clustBuffer", "SHIFT")
    arcpy.env.extent = arcpy.Describe("temp_clustBuffer").extent
    print(arcpy.Describe("temp_clustBuffer").extent)

    winner = []
    winnerWeight = 999999999999999
    solution = withoutRaster # Existuje konfigurace bez konfliktu?

    # nalezení největší váhy pro vážení v případech, že nelze nalézt konfiguraci bez konfliktu
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
    def next(cfg, i, winnerWeight, winner,dict,solution):
        """

        :param cfg: aktuální konfigurace
        :param i: pozice v konfiguraci
        :param winnerWeight: aktuální váha nejlepší konfigurace
        :param winner: aktuálně nejlepší konfigurace
        :param dict: slovník s geometriemi celého clusteru
        :param solution: boolean zda existuje řešení bez konfliktu
        :return: winnerWeight, winner, solution
        """
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

            if detect == 0:
                solution = True

            if detect != 0:
                # vážení konfliktu podle průniku v rasteru (pouze v případě, že není řešení bez konfliktu)
                if not solution:
                    print("Tvoří se rastr")
                    # váha rastru = počet pixelů v překryvu * množstí znaků v překryvu
                    rasterWeight = rasterComparsion(cfg, dict)
                actualWeight += rasterWeight * maxWeight


            if actualWeight < winnerWeight:
                winner = list(cfg)
                winnerWeight = actualWeight
                # print("Tato konfigurace je aktuálně nejlepší s váhou: {}".format(winnerWeight))


            # konec testování a tvorby výstupu

            cfg[i] += 1

            j = i
            while j != 0:
                j -= 1
                winnerWeight, winner, solution = next(cfg, j, winnerWeight, winner,dict, solution)

        cfg[i] = 0
        return winnerWeight, winner, solution

    # procházení pozic v konfiguraci a volání funkce

    for x in range(len(cfg)):
        # print("další forcyklus")
        winnerWeight, winner, solution = next(cfg, x, winnerWeight, winner,dict, solution)

    if winner == []:
        print("Při současném nastacení pro shluk neexistuje žádné lepší řešení než výchozí")
        # arcpy.CopyFeatures_management(geometries, "best164")
        winner += cfg

    seconds2 = time.time()
    print("Cluster {}, který obsahuje {} znaků, je vyřešen za {} sekund.".format(cluster,len(dict),(seconds2-seconds1)))

    # vložení vítězných geometrií do výstupu
    insCur = arcpy.da.InsertCursor(outputFeature, ["SHAPE@","X1","Y1","FID_ZBG","CLASS"])
    for pos in range(len(dict)):
        insCur.insertRow((dict[pos]["geom"][winner[pos]],dict[pos]["x"],dict[pos]["y"],dict[pos]["id"],dict[pos]["class"]))
    del insCur

# základní parametry pro funkci
mainFeature = "FeatureTest2"
mainBuffer = mainFeature + "_Buffer"
mainOutput = "bestOutput9"
mainSR = 5514

# definování polygonové vrstvy z datasetu
# shapePlace("znacky.json","JTSK_1","T2feature","T2buffer",mainSR,10000)

# roztřídění polygonů do clusterů
# clusterDefinition(mainFeature,mainBuffer)

# vytvoření seznamu všech clusterů
seaCur_clust = arcpy.da.SearchCursor(mainFeature, ["CLUSTER"])
clusters = []
clusterGeometries = []

for row in seaCur_clust:
    if row[0] not in clusters:
        clusters.append(row[0])

# vytvoření souboru pro výstup
arcpy.CreateFeatureclass_management(arcpy.env.workspace, mainOutput, "POLYGON", "#", "#", "#", mainSR)

# přidání odpovídajících polí atributové tabulky do výstupu
arcpy.AddField_management(mainOutput, "X1", "DOUBLE")
arcpy.AddField_management(mainOutput, "Y1", "DOUBLE")
arcpy.AddField_management(mainOutput, "CLASS", "TEXT")
arcpy.AddField_management(mainOutput, "FID_ZBG", "TEXT")


# clusters = [118, 88, 94, 117, 110] # clustery seřazené podle počtu prvků pro featureTest3
clusters = [29]

for cluster in clusters:
    clusterSolve(mainFeature,mainBuffer, cluster,5,mainOutput,mainSR,False)


