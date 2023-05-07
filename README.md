
#### **Work in progress! Please do NOT use for any real structures!**

# ifcStructuralAnalysis

Load cases are not implemented yet. Only self weight. 

`IfcRelConnectsWithEccentricity` works only on some models. 


#### run.py:
edit the following in `run.py´: 
``` python
# conda env with gmsh installed: 
conda_gmsh_env = "gmsh"

# conda env with gmsh installed: 
conda_gmsh_env = "gmsh"

# path to GMSH with .med support:
gmsh_path = "/bin/gmsh-4.11.1-Linux64/bin/gmsh"

# IFC files: 
ifcFiles = [
```

then run 
```
python run.py
```
<img src="result/Screenshot%20from%202023-05-06%2019-10-13.png" alt="image" height="300"/>

### ifcStructural_server
docker container with flask that provides data from the IFC for meshing and analysis to http://localhost:8080/

### ifcStructural_mesh
Creates a mesh from the IFC using GMSH

### ifcStructural_analysis
FEM analysis using code-aster
based on the docker container from [aethereng/docker-codeaster](https://github.com/aethereng/docker-codeaster)


#### Build docker containers: 
`build.sh`

### IFC files

- [x] beam_01.ifc
- [x] portal_01.ifc
- [x] grid_of_beams.ifc
- [ ] structure_01.ifc
    - no mesh generated for `IfcRelConnectsWithEccentricity`
- [ ] building_01.ifc
    - no mesh generated for `IfcRelConnectsWithEccentricity`
- [ ] building_02.ifc
    - no mesh generated for `IfcRelConnectsWithEccentricity`


## ToDo
- [ ] add support for load cases
- [ ] Docker image for GMSH
- [ ] fix meshing for `IfcRelConnectsWithEccentricity`

<!-- 
### Run CA in singularity container
``` shell
apptainer run ../salome_meca-lgpl-2022.1.0-1-20221225-scibian-9.sif shell

source /opt/salome_meca/V2022.1.0_scibian_univ/tools/Code_aster_stable-1560/share/aster/profile.sh

```

### Run CA in docker container
``` shell
docker run --rm -v .:/work/aster codeaster-seq sh -c "sh /work/aster/ifcStructural_analysis/run_aster.sh"


``` -->

