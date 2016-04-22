from pymake.builds.fileset import Fileset, File, FilesetBuild
from pymake.builds.vivado_hls import VivadoHlsProjectBuild, VivadoHlsSolution,\
    VivadoHlsSynthBuild

def test_vivado_hls():
    hlsprj = VivadoHlsProjectBuild(prj=File('$BUILDDIR/axi_lite'), 
                  fileset=FilesetBuild(match=['*.cpp', '*.hpp'], ignore=['*/tb*.cpp']),
                  tb_fileset=FilesetBuild(match=['*/tb*.cpp']),
                  solutions=[VivadoHlsSolution(config={'rtl': '-reset all -reset_level high'})]
                  )
    
    b = VivadoHlsSynthBuild(hlsprj)
    inst = b.build()
    pass

test_vivado_hls()
