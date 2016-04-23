from pymake.utils import Fileset, File
from pymake.builds.fileset import FilesetBuild, FileBuild
from pymake.builds.vivado_hls import VivadoHlsProjectBuild, VivadoHlsSolution,\
    VivadoHlsSynthBuild
import pickle

def test_vivado_hls():
    hlsprj = VivadoHlsProjectBuild(prj          = FileBuild('$BUILDDIR/axi_lite'),
                                   config       = {'top': 'axi_lite'},  
                                   fileset      = FilesetBuild(match=['./src/*.cpp', './src/*.hpp'], ignore=['*/tb*.cpp'], root=FileBuild('$BUILDDIR')),
                                   tb_fileset   = FilesetBuild(match=['./src/tb*.cpp']),
                                   solutions    = [VivadoHlsSolution(config={'rtl': '-reset all -reset_level high'})]
                  )
    
#     b = VivadoHlsSynthBuild(hlsprj)
#     inst = b.build('vivado_hls')
    hlsprj.build('vivado_hls_prj')

# obj = pickle.load(open('/home/bogdan/projects/pymake/tests/test_vivado_hls/vivado_hls_prj.pickle', 'rb'))
# pass
test_vivado_hls()
