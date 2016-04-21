from pymake.builds.fileset import Fileset
from subprocess import call
import subprocess
from pymake.utils import resolve_path
from pymake.builds.interact import Interact
from pymake.builds.vivado_hls import VivadoHlsInteract

def test_fileset():
    f = Fileset(match = ['*.py'])
    fileset_files = f.build()
     
    ret = subprocess.check_output(['find', '-name', '*.py'], universal_newlines=True)
    find_files_rel = ret.split('\n')[:-1]
    find_files = [resolve_path(f) for f in find_files_rel]
    assert set(fileset_files) == set(find_files) 

def test_interact():
    b = VivadoHlsInteract()
    inst = b.build()
    with inst:
        vivado_hls_files_rel = inst.cmd('ls')
        
    ret = subprocess.check_output(['find', '-maxdepth', '1'], universal_newlines=True)
    find_files_rel = ret.split('\n')[1:-1] #Remove current dir from list since 'ls' does not return it
    find_files = [resolve_path(f) for f in find_files_rel]
    vivado_hls_files = [resolve_path(f) for f in vivado_hls_files_rel]
    assert set(vivado_hls_files) == set(find_files) 
    
# test_fileset()
test_interact()