import arcpy

#definovani umisteni, ve kterém pracuji
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"

# soubor ke zpracovani
tvarFeatureClass = "Tkriz_null_DetectGraphicConfl"

# vytvorime kurzor
seaCur = arcpy.da.SearchCursor(tvarFeatureClass, ["OBJECTID", "SHAPE@"])

# pro kazdy zaznam v souboru ke zpracovani
for row in seaCur:
    # ... a geometrii (ktera je singlepart)
    geom = row[1]
    part = geom.getPart(0)
    pnt = part.next()

    tvar = []
    while pnt:
        # tento cyklus probehne pro kazdy bod dane casti
        # vypis souradnice bodu
        print(pnt.X, pnt.Y)
        tvar.append([pnt.X/10,pnt.Y/10])

        # a ber dalsi
        pnt = part.next()

        # ošetření polygonu s dírou
        if not pnt:
            pnt = part.next()
            if pnt:
                print("Dira v polygonu:")

    # print(pnt)
    # partcount = geom.partCount
    # print("Pocet casti: " + str(partcount))
    #print(pnt.X, pnt.Y)

# smazeme kurzor (uvolnime zamek)
print(tvar)
del seaCur