import time
start_time = time.time()

import os
import subprocess
import requests


# path: 
path = '~/Github/ifcStructuralAnalysis/'
#path = os.path.expanduser('~/Github/ifcStructuralAnalysis/')

# conda env with gmsh installed: 
conda_gmsh_env = "gmsh"

# conda env with gmsh installed: 
conda_gmsh_env = "gmsh"

# path to GMSH with .med support:
gmsh_path = "/bin/gmsh-4.11.1-Linux64/bin/gmsh"
# gmsh_path = "/Applications/Gmsh.app/Contents/MacOS/gmsh"

# IFC files: 
ifcFiles = [
    "beam_01.ifc",
    "portal_01.ifc",
    "structure_01.ifc",
    # "grid_of_beams.ifc",
    # "building_01.ifc",
    # "building_02.ifc",
]

#

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# start ifc_flask container
# --------------------------------------------------------------------------------------
containerName = 'ifcstructural_server'

if not subprocess.check_output(f'docker ps -q -f "name={containerName}"', shell=True):
    # print(f"The {containerName} container is being started.")
    subprocess.run(f"docker run -d --rm -v ~/Github/ifcStructuralAnalysis/ifcStructural_server:/app -v ~/Github/ifcStructuralAnalysis/ifc:/ifc -p 8080:8080 --name {containerName} smr02/{containerName}", shell = True)
    time.sleep(5)
    
else: 
    # print(f"The {containerName} container is already running.")
    pass


analysis_successful = []
for ifcFile in ifcFiles: 
    ifcFileName = os.path.splitext(ifcFile)[0]

    # create result folder
    if os.path.exists(f"result/{ifcFileName}"):
        os.system(f"rm -rf result/{ifcFileName}")
    os.mkdir(f"result/{ifcFileName}") 

    
    requests.post('http://localhost:8080/load_IFC', data=ifcFile.encode('utf-8'))
    #print(response.text)
    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    # Create mesh (gmsh)
    # --------------------------------------------------------------------------------------

    subprocess.run(
        f"conda run -n {conda_gmsh_env} python ifcStructural_mesh/ifc_to_mesh.py {ifcFileName}",
        shell=True
    )

    subprocess.run(f"""
    {gmsh_path} result/{ifcFileName}/{ifcFileName}.msh \\
        -format med \\
        -save result/{ifcFileName}/{ifcFileName}
    """,
        shell=True)

    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    # Run code_aster
    # --------------------------------------------------------------------------------------

    subprocess.run(f"""

    docker run --rm -it\
        --add-host=host.docker.internal:host-gateway \\
        -v {path}:/work/aster smr02/codeaster-seq \\
        sh -c "sh /work/aster/ifcStructural_analysis/run_aster.sh {ifcFileName}"
        
    """,
        shell=True
    )


    
    if os.path.isfile(f"result/{ifcFileName}/{ifcFileName}.rmed"):
        analysis_successful.append("\033[32m" + "✓" * 5 + "  Analysis successful!  " + "✓" * 5 + "\033[0m" + " " +ifcFile) 
    else:
        analysis_successful.append("\033[31m" + "✗" * 5 + "  Analysis FAILED!   " + "✗" * 5 + "\033[0m" + "    " +ifcFile) 


print()
for i in analysis_successful: 
    print(i)
print()


end_time = time.time()
execution_time = end_time - start_time

print(f"Execution time: {execution_time} seconds")