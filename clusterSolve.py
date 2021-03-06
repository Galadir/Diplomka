import arcpy
import math

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

        dict[symbolNum] = {"class":row[2],"geom":geomAll,"weight":weightAll} #class by mělo být nahrazeno nějakým unikátním id
        # arcpy.CopyFeatures_management(geomAll, "tvar"+str(symbolNum))

        symbolNum += 1


    print(dict)

    def configuration(dict):
        """

        :param cfg:
        :param dict:
        :return:
        """
        winner = ""
        winnerWeight = 999999999999999

        cfg = []  # konfigurace pozicí znaků

        # nastavení nul jakožto výchozích pozic v konfiguraci
        for num in range(len(dict)):
            cfg.append(0)

        # rekurzivní procházení konfigurací vázaných na její určitou pozici
        def next(cfg, i, winnerWeight, winner,dict):
            while cfg[i] < len(dict[i]["geom"]) - 1:
                print(cfg)

                # otestování konfliktu
                clusterGeom =[] # všechny geometrie aktuální konfigurace
                actualWeight = 0
                for g in range(len(dict)):
                    clusterGeom.append(dict[g]["geom"][cfg[g]])
                    actualWeight += dict[g]["weight"][cfg[g]]


                # tvorba výstupu
                if detectConflicts(clusterGeom):
                    if actualWeight < winnerWeight:
                        winner = clusterGeom
                        winnerWeight = actualWeight
                    name = "cfg" # název souboru výstupu
                    for n in cfg:
                        name = name + str(n)

                    #print(name)
                    #arcpy.CopyFeatures_management(clusterGeom, name)
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
        arcpy.CopyFeatures_management(winner, "best")

    configuration(dict)


clusterSolve("T3comb",212,10)

print(netMake1(1,5))
