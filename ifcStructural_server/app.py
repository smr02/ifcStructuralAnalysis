
from flask import Flask, jsonify, request
import ifcopenshell
import os 
import sys
import numpy as np

app = Flask(__name__)

# Open the IFC file
# ifc_path = '/ifc/beam_01.ifc'
# ifc_path = '/ifc/portal_01.ifc'
# ifc_path = '/ifc/structure_01.ifc'
# ifc_path = '/ifc/grid_of_beams.ifc'
# ifc_path = '/ifc/building_01.ifc'
# ifc_path = '/ifc/building_02.ifc'


app = Flask(__name__)

@app.route('/load_IFC', methods=['POST'])
def load_IFC():
    data = request.data.decode('utf-8') 
    global ifc_path
    ifc_path = '/ifc/' + data
    
    global ifc_file
    try: ifc_file = ifcopenshell.open(ifc_path)
    except: ifc_file = []
    
    for i in ifc_file:
        try: 
            if '$' in i.GlobalId:
                new_id = '$'
                while '$' in new_id:
                    new_id = ifcopenshell.guid.new()
                i.GlobalId = new_id
        except:
            pass

    
    return ifc_path


@app.route('/')
def start():
    output = {}
    output['file_name'] = ifc_file.by_type('IFCPROJECT')[0].Name
    output['project_name'] = ifc_file.by_type('IFCPROJECT')[0].Name

    output['units'] = {}
    for unit in ifc_file.by_type('ifcsiUnit'):
        # print(unit.get_info())
        #print(unit.UnitType, unit.Name)
        if unit.Prefix: 
            output['units'][unit.UnitType] = str.title(unit.Prefix) + str.title(unit.Name)
        else:  
            output['units'][unit.UnitType] = str.title(unit.Name)


    return jsonify(output)




@app.route('/ifcVertexPoints')
def get_ifcVertexPoints():
    ifcVertexPoints={}
    for element in ifc_file.by_type("IfcVertexPoint"):
        coord = element[0]
        ifcVertexPoints[element.VertexGeometry.id()] = {
            'X': coord.Coordinates[0],
            'Y': coord.Coordinates[1],
            'Z': coord.Coordinates[2],
        }
    return jsonify(ifcVertexPoints)


def get_ifcVertexPoints_2():
    ifcVertexPoints={}
    for element in ifc_file.by_type("IfcVertexPoint"):
        coord = element[0]
        ifcVertexPoints[element.VertexGeometry.id()] = {
            'X': coord.Coordinates[0],
            'Y': coord.Coordinates[1],
            'Z': coord.Coordinates[2],
        }
    return ifcVertexPoints


@app.route('/ifcEdges')
def get_ifcEdges():
    ifcEdges = {}
    for element in ifc_file.by_type("IfcEdge"):
        ifcEdges[element.id()] = [
            element.EdgeStart.VertexGeometry.id(),
            element.EdgeEnd.VertexGeometry.id()
        ]
        pass

    return jsonify(ifcEdges)



@app.route('/ifcStructuralItems')
def get_ifcStructuralItems():
    ifcStructuralItems = {}
    for item in ifc_file.by_type('IfcStructuralItem'):

        if item.Representation.Representations[0].RepresentationType == 'Vertex':
            geomList = [item.Representation.Representations[0].Items[0].VertexGeometry.id()]

        elif  item.Representation.Representations[0].RepresentationType == 'Edge':
            geomList = [
                item.Representation.Representations[0].Items[0].id(),
            ]
        elif item.Representation.Representations[0].RepresentationType == 'Face':
            geomList = []
            surface_edge = (item.Representation.Representations[0].Items[0].Bounds[0].Bound)
            for edge in surface_edge.EdgeList:
                geomList.append(edge.id())

        RelatedStructuralConnection = []
        if hasattr(item, 'ConnectedBy'): 
            for connection in item.ConnectedBy:
                if connection.RelatedStructuralConnection.Representation.Representations[0].Items[0].is_a() == 'IfcVertexPoint':
                    RelatedStructuralConnection.append({
                        'id': connection.RelatedStructuralConnection.Representation.Representations[0].Items[0].VertexGeometry.id(),
                        'is_a': connection.RelatedStructuralConnection.is_a()
                    })

        ifcStructuralItems[item.GlobalId] = {
            'geomList': geomList, 
            'type': item.Representation.Representations[0].RepresentationType,
            'ifcItem': item.is_a(),
            'RelatedStructuralConnection': RelatedStructuralConnection
        }

    return jsonify(ifcStructuralItems)
    
@app.route('/ifcRelConnects')
def get_ifcRelConnects():
    text = "hello_world"
    ifcRelConnects = {}
    for item in ifc_file.by_type('IfcRelConnectsWithEccentricity'):
        vertList = []
        ifcRelConnects[item.GlobalId] = {
            'coordinates': item.ConnectionConstraint.PointOnRelatingElement.Coordinates,
            'axis': item.RelatingStructuralMember.Axis.DirectionRatios,
            'RelatingStructuralMember_globalID': item.RelatingStructuralMember.GlobalId,
            'RelatingStructuralMember_ID': item.RelatingStructuralMember.id(),
            'Curve_ID': item.RelatingStructuralMember.Representation.Representations[0].Items[0].id(),
            'RelatedStructuralConnection': item.RelatedStructuralConnection.GlobalId,
            'Id': item.id(),
        }
        
    return jsonify(ifcRelConnects)


@app.route('/ifcMaterials')
def get_ifcMaterials():
    ifcMaterials = {}
    for material in ifc_file.by_type('IfcMaterial'):
        values = {}
        for material_prop in material.HasProperties:
            for propertie in material_prop.Properties:
                values[propertie.Name] = propertie.NominalValue.wrappedValue
        ifcMaterials[material.Name] = values | {'Category' : material.Category}
        ifcMaterials[material.Name]['Members'] = []

    for member in ifc_file.by_type('IfcRelAssociatesMaterial'):
        relatedObjects = []
        for relatetObject in member.RelatedObjects:
            relatedObjects.append(relatetObject.GlobalId)
        if hasattr(member.RelatingMaterial, 'MaterialProfiles'): 
            ifcMaterials[member.RelatingMaterial.MaterialProfiles[0].Material.Name]['Members'].extend(relatedObjects)
        elif hasattr(member.RelatingMaterial, 'Name'): 
            ifcMaterials[member.RelatingMaterial.Name]['Members'].extend(relatedObjects)
        elif hasattr(member.RelatingMaterial.ForProfileSet.MaterialProfiles[0].Material, 'Name'): 
            ifcMaterials[member.RelatingMaterial.ForProfileSet.MaterialProfiles[0].Material.Name]['Members'].extend(relatedObjects)
    return jsonify(ifcMaterials)


@app.route('/ifcBC')
def get_ifcBC():
    ifcBC = {}
    for element in ifc_file.by_type('IfcStructuralConnection'):
        if element.AppliedCondition:
            if element.is_a() == 'IfcStructuralPointConnection':
                ifcBC[element.GlobalId] = {
                    "type": element.is_a(),
                    "DRX": element.AppliedCondition.RotationalStiffnessX.wrappedValue, 
                    "DRY": element.AppliedCondition.RotationalStiffnessY.wrappedValue, 
                    "DRZ": element.AppliedCondition.RotationalStiffnessZ.wrappedValue,
                    "DX": element.AppliedCondition.TranslationalStiffnessX.wrappedValue, 
                    "DY": element.AppliedCondition.TranslationalStiffnessY.wrappedValue, 
                    "DZ": element.AppliedCondition.TranslationalStiffnessZ.wrappedValue,
                    "id": element.Representation.Representations[0].Items[0].VertexGeometry.id(),
                    "globalID": element.GlobalId
                }
                
            elif element.is_a() == 'IfcStructuralCurveConnection':
                
                ifcBC[element.GlobalId] = {
                    "type": element.is_a(),
                    "DRX": element.AppliedCondition.RotationalStiffnessByLengthX.wrappedValue, 
                    "DRY": element.AppliedCondition.RotationalStiffnessByLengthY.wrappedValue, 
                    "DRZ": element.AppliedCondition.RotationalStiffnessByLengthZ.wrappedValue,
                    "DX": element.AppliedCondition.TranslationalStiffnessByLengthX.wrappedValue, 
                    "DY": element.AppliedCondition.TranslationalStiffnessByLengthY.wrappedValue, 
                    "DZ": element.AppliedCondition.TranslationalStiffnessByLengthZ.wrappedValue,
                    "globalID": element.GlobalId
                }
                
    return jsonify(ifcBC)



@app.route('/analysis/ifcStructuralItems')
def get_ifcStructuralItems_analysis():
    ifcStructuralItems = {}
    for item in ifc_file.by_type('IfcStructuralItem'):

        ifcStructuralItems[item.GlobalId] = {
            'ifcItem': item.is_a(),
        }

        if item.is_a() == 'IfcStructuralSurfaceMember': 
            ifcStructuralItems[item.GlobalId]['Thickness'] = item.Thickness

    for item in ifc_file.by_type('IfcRelConnectsWithEccentricity'):

        ifcStructuralItems[item.GlobalId] = {
            'ifcItem': item.is_a(),
        }


    return jsonify(ifcStructuralItems)



@app.route('/analysis/ifcProfiles')
def get_ifcProfiles():
    
    ifcProfiles = {}

    for member in ifc_file.by_type('IfcRelAssociatesMaterial'):
        is_profile = False

        if member.RelatingMaterial.is_a() == 'IfcMaterialProfileSet':
            profileName = member.RelatingMaterial.MaterialProfiles[0].Profile.ProfileName
            profiles = member.RelatingMaterial.MaterialProfiles[0].Profile.get_info()
            is_profile = True

        elif member.RelatingMaterial.is_a() == 'IfcMaterialProfileSetUsage':
            profileName = member.RelatingMaterial.ForProfileSet.MaterialProfiles[0].Profile.ProfileName
            profiles = member.RelatingMaterial.ForProfileSet.MaterialProfiles[0].Profile.get_info()
            is_profile = True

        if is_profile: 
            keys_to_remove = []
            for key, value in profiles.items(): 
                if not isinstance(value, (int, str, float)):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del profiles[key]

            ifcProfiles[profileName] = profiles
            ifcProfiles[profileName]['Members'] = [i.GlobalId for i in member.RelatedObjects]
    return jsonify(ifcProfiles)



if __name__ == '__main__':
    app.run()


