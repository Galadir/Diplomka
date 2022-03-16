import arcpy

# definovani pracovního prostoru
inputDatabase = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"
arcpy.env.workspace = inputDatabase
arcpy.env.overwriteOutput = 1

def netMake1 (layersNumber, distance):
    """
    Vytvoří pravidelnou čtvercovou síť bodů na základě zadané vzdálenosti mezi body.

    :param layersNumber: počet vrstev v pravidelné síti 1 vrstva = síť 3x3, 2 vrstvy = síť 5x5
    :param distance: vzdálenost mezi jednotlivými body
    :return:
    """
    list = []
    size = layersNumber * 2 + 1
    for i in range(-layersNumber,layersNumber+1):
        y = i*distance
        for j in range(-layersNumber, layersNumber+1):
            x = j*distance
            list.append([x,y])
    return list

def detectConflicts(clusterGeom):
    """
    Určí, zda mezi vstupními geometriemi dochází k průniku.

    :param clusterGeom: seznam acrpy geometrií, mezi kterými je třeba určit
    :return: Boolean – pokud True, je bez konfliktu
    """
    # výsledná boolean hodnota
    confall = True

    # procházení konfliktních situací
    for g1 in range(len(clusterGeom)):
        for g2 in range(len(clusterGeom)):
            if g1 != g2 and g1 < g2:
                conf = clusterGeom[g1].disjoint(clusterGeom[g2])
                if not conf:
                    confall = conf

                # print(str(g1) + " x " + str(g2) + " = " + str(conf))

    print(confall)
    return confall

def clusterSolve(inputFeature,cluster,distance):
    """
    Vrátí nejlepší řešení konfliktu mezi znaky v jednom shluku podle zadaných parametrů.

    :param inputFeature: cesta k souboru, ze kterého je brána geometrie
    :param cluster: cluster, pro který je problém řešený
    # DALŠÍ PARAMETRY MOHOU BÝT KLÍČOVÉ PŘI UPRAVÁCH ALGORITMU !!!
    :param distance: Rozestupy mezi
    :return:
    """
    dict = {} # slovník, který obsahuje identifikaci znaku a seznam geometrií na možných pozicích po provedení posunu


    # výběr znaků ve shluku z celkové množiny znaků
    clust = arcpy.SelectLayerByAttribute_management(inputFeature, "NEW_SELECTION","CLUSTER = "+str(cluster))

    # ověření, jestli opravdu existuje konflikt, v případě, že jsme bez konfliktu, je nejvhodnějším výstupem výchozí rozložení
    geometries = arcpy.CopyFeatures_management(clust, arcpy.Geometry())
    if detectConflicts(geometries):
        return

    # vybrané atributy !!! MŮŽE BÝT KLÍČOVÉ PRO ZADÁNÍ PARAMETRŮ PŘI UPRAVÁCH ALGORITMU !!!
    seaCur = arcpy.da.SearchCursor(clust, ["SHAPE@","OBJECTID", "CLASS","SHIFT","X1","Y1"])

    symbolNum = 0 # identifikační číslo znaku v slovníku – spojité od 0 do n
    for row in seaCur:
        # definování sítě pro jednotlivé znaky !!! KLÍČOVÉ PRO ZADÁNÍ PARAMETRŮ PŘI UPRAVÁCH ALGORITMU !!!
        net = netMake1(int(int(row[3]) / distance), distance)

        geomAll = [] # seznam geometrií pro body v síti jednoho znaku
        geom = row[0] # jedna geometrie v seznamu

        # vytvoření geometrie na místa v síti
        for netPoint in net: #procházím body v síti
            part = arcpy.Array() # pole do kterého nahraji tvar
            for point in geom: # procházím body z polygonu znaku
                for nod in point: # procházím souřadnice v bodě
                    pnt = arcpy.Point(nod.X+netPoint[0], nod.Y+netPoint[1])
                    part.add(pnt)
            # vytvoření polygonu z pole
            polygon = arcpy.Polygon(part)
            geomAll.append(polygon)
            # vyčištění pole
            part.removeAll()

        dict[symbolNum] = {"class":row[2],"geom":geomAll} #class by mělo být nahrazeno nějakým unikátním id
        # arcpy.CopyFeatures_management(geomAll, "tvar"+str(symbolNum))

        symbolNum += 1


    print(dict)

    def configuration(dict):
        """

        :param cfg:
        :param dict:
        :return:
        """
        cfg = []  # konfigurace pozicí znaků

        # nastavení nul jakožto výchozích pozic v konfiguraci
        for num in range(len(dict)):
            cfg.append(0)

        # rekurzivní procházení konfigurací vázaných na její určitou pozici
        def next(cfg, i):
            while cfg[i] < len(dict[i]["geom"]) - 1:
                print(cfg)

                # otestování konfliktu
                clusterGeom =[] # všechny geometrie aktuální konfigurace
                for g in range(len(dict)):
                    clusterGeom.append(dict[g]["geom"][cfg[g]])

                # tvorba výstupu
                if detectConflicts(clusterGeom):
                    name = "cfg" # název souboru výstupu
                    for n in cfg:
                        name = name + str(n)

                    print(name)
                    arcpy.CopyFeatures_management(clusterGeom, name)
                # konec testování a tvorby výstupu

                cfg[i] += 1

                j = i
                while j != 0:
                    j -= 1
                    next(cfg, j)

            cfg[i] = 0
            return

        # procházení pozic v konfiguraci a volání funkce
        for x in range(len(cfg)):
            # print("další forcyklus")
            next(cfg, x)

    configuration(dict)


clusterSolve("T3comb",212,10)
