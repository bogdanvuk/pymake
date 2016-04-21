from pymake.builds.fileset import Fileset, File
from pymake.builds.vivado_hls import VivadoHlsProjectBuild, VivadoHlsSolution

def test_vivado_hls():
    b = VivadoHlsProjectBuild(prj=File('$BUILDDIR/axi_lite'), 
                  fileset=Fileset(match=['*.cpp', '*.hpp'], ignore=['*/tb*.cpp']),
                  tb_fileset=Fileset(match=['*/tb*.cpp']),
                  solutions=[VivadoHlsSolution(config={'rtl': '-reset all -reset_level high'})]
                  )
    inst = b.build()
    pass

test_vivado_hls()
