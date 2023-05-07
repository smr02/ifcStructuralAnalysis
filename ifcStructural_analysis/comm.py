
import os
import code_aster as ca
from code_aster.Commands import *
import sys

import requests
ifcFileName = sys.argv[1]

ca.init(LANG='EN')

# # # -----------------------------------------------------------------------------
# # # -----------------------------------------------------------------------------
# # # MESH
# # # -----------------------------------------------------------------------------

def load_mesh():
   mesh = ca.Mesh()
   mesh.readMedFile(f"{ifcFileName}.med")
   # mesh.debugPrint()
     
   return mesh

mesh = load_mesh()

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Model Definition
# -----------------------------------------------------------------------------


ifcStructuralItems_json = requests.get('http://host.docker.internal:8080/analysis/ifcStructuralItems')
ifcStructuralItems = ifcStructuralItems_json.json()
elementList = []

# Assign finite elements
for item in ifcStructuralItems:
   if ifcStructuralItems[item]['ifcItem'] =='IfcStructuralCurveMember':
      elementList.append(
        _F(
            GROUP_MA=(item),
            MODELISATION='POU_D_T',
            PHENOMENE='MECANIQUE'
        )
      )
   elif ifcStructuralItems[item]['ifcItem'] =='IfcStructuralSurfaceMember':
    elementList.append(
        _F(
            GROUP_MA=(item),
            MODELISATION='DKT',
            PHENOMENE='MECANIQUE'
        )
    )
   elif ifcStructuralItems[item]['ifcItem'] =='IfcRelConnectsWithEccentricity':
    elementList.append(
        _F(
            GROUP_MA=(item),
            MODELISATION='DIS_TR',
            PHENOMENE='MECANIQUE'
        )
    )


model0 = AFFE_MODELE(
    AFFE = elementList,
   MAILLAGE=mesh
)

ifcProfiles_json = requests.get('http://host.docker.internal:8080//analysis/ifcProfiles')
ifcProfiles = ifcProfiles_json.json()
bcList = []
poutre = []

for profile in ifcProfiles:
   if ifcProfiles[profile]['type'] == 'IfcRectangleProfileDef':
      poutre.append(
         _F(
            CARA=('HY', 'HZ'),
            GROUP_MA=(ifcProfiles[profile]['Members']),
            SECTION='RECTANGLE',
            VALE=(
               ifcProfiles[profile]['XDim'], 
               ifcProfiles[profile]['YDim']
            )
         )
      )


coque = []
discret = [ ]

for item in ifcStructuralItems:
    if ifcStructuralItems[item]['ifcItem'] =='IfcStructuralSurfaceMember':
        coque.append(
            _F(
                EPAIS=ifcStructuralItems[item]['Thickness'],
                GROUP_MA=(item),
                VECTEUR=(0.0, 1.0, 0.0)
            ),
        )
    elif ifcStructuralItems[item]['ifcItem'] =='IfcRelConnectsWithEccentricity':
        discret.append(
            _F(
               CARA='K_TR_D_L',
               GROUP_MA=(item),
               REPERE='GLOBAL',
               VALE=(10e9, 10e9, 10e9, 10e9, 10e9, 10e9)
            ),
        )


elemprop = AFFE_CARA_ELEM(
   MODELE = model0,
   POUTRE = poutre,
   COQUE = coque,
   DISCRET = discret
)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Material
# -----------------------------------------------------------------------------

ifcMaterials_json = requests.get('http://host.docker.internal:8080/ifcMaterials')
ifcMaterials = ifcMaterials_json.json()

materials = {}
materialMemberList = []


for material in ifcMaterials: 
   materialProperties = {}
   materialProperties['E'] = ifcMaterials[material]['YoungModulus']
   try: 
      materialProperties['NU'] = ifcMaterials[material]['PoissonRatio']
   except: 
      materialProperties['NU'] = 0.3
   materialProperties['RHO'] = ifcMaterials[material]['MassDensity']

   materials[material] = DEFI_MATERIAU(
      ELAS=_F(materialProperties)
   )

   materialMemberList.append(
      _F(
         GROUP_MA= ifcMaterials[material]['Members'],
         MATER=( materials[material] )
      )
   )


material = AFFE_MATERIAU(
   AFFE = materialMemberList,
   MODELE = model0,
)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Functions and Lists
# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# BC and Loads
# -----------------------------------------------------------------------------

# BCs
ifcBC_json = requests.get('http://host.docker.internal:8080/ifcBC')
ifcBC = ifcBC_json.json()
bcList = []
for name in ifcBC:  
    for key, value in list(ifcBC[name].items()):
        if key == 'globalID':
            ifcBC[name]['GROUP_MA'] = str(value)
            del ifcBC[name][key]
        elif key == 'id':
            del ifcBC[name][key]
        elif value == True:
            ifcBC[name][key] = 0.0
        elif isinstance(value, bool):
            del ifcBC[name][key]
        elif isinstance(value, (int, float)):
            pass
        else: 
            del ifcBC[name][key]
    bcList.append(_F(ifcBC[name]))


BC = AFFE_CHAR_MECA(
   DDL_IMPO = bcList,
   MODELE=model0
)


# Load, selfweight
selfw = AFFE_CHAR_MECA(
   MODELE=model0,
   PESANTEUR=_F(
      DIRECTION=(0.0, 0.0, -1.0),
      GRAVITE=10.0,
      GROUP_MA = [
         key for key, value in ifcStructuralItems.items() 
         if value['ifcItem'] == 'IfcStructuralCurveMember'
         or
         value['ifcItem'] == 'IfcStructuralSurfaceMember'
         ],
   )
)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Analysis
# -----------------------------------------------------------------------------

reslin = MECA_STATIQUE(
   CARA_ELEM=elemprop,
   CHAM_MATER=material,
   EXCIT=(
      _F(CHARGE=BC),
      _F(CHARGE=selfw)
   ),
   MODELE=model0
)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Post Processing
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------


IMPR_RESU(
   RESU=_F(
      # GROUP_MA = [
      #    key for key, value in ifcStructuralItems.items() 
      #    if value['ifcItem'] == 'IfcStructuralCurveMember'
      #    or
      #    value['ifcItem'] == 'IfcStructuralSurfaceMember'
      #    ],
      NOM_CHAM=('DEPL', ),
      RESULTAT=reslin
   ),
   UNITE=80
)

os.rename('fort.80', f"{ifcFileName}.rmed")

# FIN()

