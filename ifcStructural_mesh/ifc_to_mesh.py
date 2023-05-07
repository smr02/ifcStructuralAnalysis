import sys
import os
import gmsh
import requests

import numpy as np


# ifcFileName = os.path.splitext(sys.argv[1])[0]
ifcFileName = sys.argv[1]

ifcProject_json = requests.get('http://localhost:8080/')
ifcProject = ifcProject_json.json()

lengthUnit = ifcProject['units']['LENGTHUNIT']
if lengthUnit == 'MilliMetre':
    cl1 = 200
elif lengthUnit == 'Metre':
    cl1 = 0.2

    
meshing = True

gmsh.initialize()

# load Vertex points
ifcVertexPoints_json = requests.get('http://localhost:8080/ifcVertexPoints')
ifcVertexPoints = ifcVertexPoints_json.json()

# # Define points

for vert in ifcVertexPoints:
    gmsh.model.geo.addPoint(
        ifcVertexPoints[vert]['X'], 
        ifcVertexPoints[vert]['Y'], 
        ifcVertexPoints[vert]['Z'], 
        cl1,
        tag = int(vert)
    )
    
# load ifcEdges
ifcEdges_json = requests.get('http://localhost:8080/ifcEdges')
ifcEdges = ifcEdges_json.json()

for edge in ifcEdges: 
    gmsh.model.geo.addLine(
        ifcEdges[edge][0], 
        ifcEdges[edge][1], 
        tag = int(edge)
    )


# load ifcStructuralItmes
ifcStructuralItems_json = requests.get('http://localhost:8080/ifcStructuralItems')
ifcStructuralItems = ifcStructuralItems_json.json()

ifcVertices = {}
ifcLines = {}
ifcSurfaces = {}

gmsh.model.geo.synchronize()

for key, value in ifcStructuralItems.items():
    # for vert in value['geomList']:
    #     geomList.append( points[str(vert)] )
    
    if value['type'] == 'Vertex':
        gmsh.model.geo.synchronize()
        gmsh.model.addPhysicalGroup(0, value['geomList'], name=key)
        ifcVertices[key] = value['geomList']



    elif value['type'] == 'Edge':
        gmsh.model.addPhysicalGroup(1, value['geomList'], name=key)
        ifcLines[key] = value['geomList']
        

    elif value['type'] == 'Face': 
        
        curveLoop = gmsh.model.geo.addCurveLoop(value['geomList'])
        _surface = gmsh.model.geo.addPlaneSurface([curveLoop])

        gmsh.model.geo.synchronize()
        gmsh.model.addPhysicalGroup(2, [_surface], name=key)

        for connection in value['RelatedStructuralConnection']:
            if connection['is_a'] == 'IfcStructuralPointConnection':
                gmsh.model.mesh.embed(0, [connection['id']], 2, _surface)



# load ifcRelConnects
ifcRelConnects_json = requests.get('http://localhost:8080/ifcRelConnects')
ifcRelConnects = ifcRelConnects_json.json()

for key, value in ifcRelConnects.items():
    try: 
        start_point = ifcEdges[str(ifcLines[value['RelatingStructuralMember_globalID']][0])][0]
        end_point = ifcEdges[str(ifcLines[value['RelatingStructuralMember_globalID']][0])][1]

        start_point_coord = np.array([
            ifcVertexPoints[str(start_point)]['X'],
            ifcVertexPoints[str(start_point)]['Y'],
            ifcVertexPoints[str(start_point)]['Z'],
        ])

        end_point_coord = np.array([
            ifcVertexPoints[str(end_point)]['X'],
            ifcVertexPoints[str(end_point)]['Y'],
            ifcVertexPoints[str(end_point)]['Z'],
        ])

        axis_vector = (end_point_coord - start_point_coord) / np.sqrt(np.sum(np.square(end_point_coord - start_point_coord)))
        vector =  axis_vector * value['coordinates'][0] #/1.1

        # print(value['Id'])
        if np.array_equal(vector, np.array([0, 0, 0])):
            point = start_point
            # print('point == start_point')
        elif np.array_equal(vector, (end_point_coord - start_point_coord)):
            point = end_point

            # print('point == end_point')
        else: 
            point = gmsh.model.geo.copy([(0, start_point)]) 
            gmsh.model.geo.translate(
                point,
                vector[0],
                vector[1],
                vector[2],
            )
            point = point[0][1]
            print(f"point == {start_point + vector}")

            gmsh.model.geo.synchronize()
            gmsh.model.mesh.embed(0, [point], 1, value['Curve_ID'])


        gmsh.model.geo.addLine(
            point, 
            ifcVertices[value['RelatedStructuralConnection']][0], 
            tag = value['Id']
        )
        gmsh.model.geo.synchronize()

        gmsh.model.geo.synchronize()
        gmsh.model.addPhysicalGroup(1, [value['Id']], name=key)
    except: 
        # meshing = False
        pass



gmsh.model.geo.synchronize()

gmsh.model.geo.removeAllDuplicates()

gmsh.model.geo.synchronize()


if meshing:
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)


if '-popup' in sys.argv:
    gmsh.fltk.run()


gmsh.write(f"result/{ifcFileName}/{ifcFileName}.msh")

gmsh.finalize()

