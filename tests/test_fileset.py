from pymake.builds.fileset import Fileset
from subprocess import call
import subprocess

def test_fileset():
    f = Fileset(match = ['*.py'])
    fileset_files = f.build()
     
    find_files = subprocess.check_output(['find', '-name', '*.py'])
    assert set(fileset_files) == set(find_files) 
    
test_fileset()