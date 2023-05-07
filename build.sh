
cd ~/Github/
git clone https://github.com/smr02/ifcStructuralAnalysis.git

cd ~/Github/ifcStructuralAnalysis/ifcStructural_server/
docker build -t ifcstructural_server . 

# clone and build code_aster from aethereng/docker-codeaster
cd ~/Github/
git clone https://github.com/aethereng/docker-codeaster.git
cd docker-codeaster/
# make seq VERSION_ASTER=15.5.2
make seq 

# build code_aster container 
cd ~/Github/ifcStructuralAnalysis/ifcStructural_analysis/
docker build -t codeaster-seq . 
cd ..

# docker run --rm -it codeaster-seq

