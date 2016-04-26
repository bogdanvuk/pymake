from pymake.builds.fileset import Fileset, FilesetBuild, FileBuild
from subprocess import call
import subprocess
from pymake.utils import resolve_path
from pymake.builds.interact import Interact
from pymake.builds.vivado_hls import VivadoHlsInteract
import os
import re


def check_fileset(fs, match):
    ret = subprocess.check_output(['find', '-name', match], universal_newlines=True)
    find_files_rel = ret.split('\n')[:-1]
    find_files = [resolve_path(f) for f in find_files_rel]
    assert set(fs) == set(find_files)

def test_fileset():
    try:
        os.remove('dummy.py')
    except FileNotFoundError:
        pass
    
    f = FilesetBuild(match = ['*.py'])
    f.clean('fileset_test')
    fileset_files = f.build('fileset_test')
    assert f.rebuilt
    check_fileset(fileset_files, '*.py')
    
    fileset_files = f.build('fileset_test')
    assert f.rebuilt == False
    
    with open('dummy.py', 'w'):
        pass
    
    fileset_files = f.build('fileset_test')
    assert f.rebuilt
    check_fileset(fileset_files, '*.py')

def test_fileset2():
    f = FilesetBuild(match=['./src/*.cpp', './src/*.hpp'], ignore=['*/tb*.cpp'], root=FileBuild('$BUILDDIR/test_vivado_hls'))
    f.clean('fileset_test2')
    fileset_files = f.build('fileset_test2')
    pass
    

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
    
# test_fileset2()
# test_interact()
