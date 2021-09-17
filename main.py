import arcpy

#definovani umisteni, ve kterém pracuji
arcpy.env.workspace = "C:\\Users\\danie\\OneDrive\\Dokumenty\\ArcGIS\\Projects\\Diplomka\\Diplomka.gdb"

# soubor ke zpracovani
fc = "kriz_null_DetectGraphicConfl1"

# v jakem sloupci je geometrie?
desc = arcpy.Describe(fc)
shapefieldname = desc.ShapeFieldName

print(shapefieldname)

# vytvorime kurzor
cursor = arcpy.da.SearchCursor(fc, ["OBJECTID", "SHAPE@"])

# pro kazdy zaznam v souboru ke zpracovani
for row in cursor:
    # zkusime precist atribut
    id = row[0]
    print(id)

    # ... a geometrii (ktera je singlepart)
    geom = row[1]

    part = geom.getPart(0)
    pnt = part.next()

    while pnt:
        # tento cyklus probehne pro kazdy bod dane casti
        # vypis souradnice bodu
        print(pnt.X, pnt.Y)

        # a ber dalsi
        pnt = part.next()

        # pokud je nyni hodnota pnt rovna None, bud jsme precetli posledni bod dane casti a nebo je tam mezera
        # oddelujici diru
        if not pnt:
            # zkusime si rici o dalsi bod
            pnt = part.next()

            # pokud jsme uspeli, jde o diru
            if pnt:
                print("Dira v polygonu:")

    # print(pnt)
    # partcount = geom.partCount
    # print("Pocet casti: " + str(partcount))
    #print(pnt.X, pnt.Y)

# smazeme kurzor (uvolnime zamek)
del cursor
