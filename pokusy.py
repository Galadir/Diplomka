def scitani(x,y):
    z=x+y
    print(z)
    return z

#z= scitani(5,6)
import json
with open ('znacky.json',encoding='UTF-8') as f:
    znacky = json.load(f)

znacky2 = znacky['symbols']

for z in znacky2:
    print(z["name"])

