import arcpy


inputDatabase = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"

# definovani pracovního prostoru
arcpy.env.workspace = inputDatabase
arcpy.env.overwriteOutput = 1


def netMake (layersNumber,distance):
    """

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

#print(netMake(1,5))

def detectConflicts(clusterGeom):
    # detekce konfliktů
    confall = True

    for g1 in range(len(clusterGeom)):
        for g2 in range(len(clusterGeom)):
            if g1 != g2 and g1 < g2:
                conf = clusterGeom[g1].disjoint(clusterGeom[g2])
                if not conf:
                    confall = conf

                print(str(g1) + " x " + str(g2) + " = " + str(conf))

    # je cluster bez konfliktu?
    ## print(confall)

def clusterSolve(inputFeature,cluster,distance):
    # výběr prvků ve shluku
    clust = arcpy.SelectLayerByAttribute_management(inputFeature, "NEW_SELECTION",
                                            "CLUSTER = "+str(cluster))


    positions = {} # slovník, který obsahuje odkaz na geometrii, síť jako seznam a nějakou identifikaci znaku
    seaCur = arcpy.da.SearchCursor(clust, ["OBJECTID", "CLASS","SHIFT","X1","Y1"])

    cfg = [] # konfigurace pozicí znaků
    for row in seaCur:
        positions[row[0]]= {"net":netMake(int(int(row[2])/distance),distance),"class":row[1],"shift":row[2],"x":row[3],"y":row[4]}
        cfg.append(0)

    nets = {0:[[-10, -10], [0, -10], [10, -10]],1:[[0, 0], [10, 0], [-10, 10]],2:[[0, 10], [10, 10]],3:[[0, 0], [10, 0], [-10, 10]]}

    cfg = [0,0,0,0]

    def next(cfg,i):
        while cfg[i] < len(nets[i])-1:
            cfg[i]+=1
            print(cfg)

            j=i
            while j != 0:
                j-=1
                next(cfg,j)

        cfg[i]=0
        return

    def configuration(cfg):
        print(cfg)
        for x in range(len(cfg)):
            print("další forcyklus")
            next(cfg, x)


    configuration(cfg)


    ## print(positions)



    # funkce, která postupně bere pozice v slovníku


        # porovnání konfliktu mezi geometriemi na určité pozici

    # reprezentace prvků ve shluku jako geometrií
    ## geometries = arcpy.CopyFeatures_management(clust, arcpy.Geometry())
    ## print(geometries)

    ## detectConflicts(geometries)



clusterSolve("T3comb",212,10)
