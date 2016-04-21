from pymake.build import Build, SrcConf
import fnmatch
import os
from pymake.utils import resolve_path

def str_check_filt(path, filter_in=[], filter_out=[]):
    for filt in filter_out:
        if fnmatch.fnmatch(path, filt):
            return False
    
    if filter_in:
        for filt in filter_in:
            if fnmatch.fnmatch(path, filt):
                return True
    else:
        return True

def get_all_files_rec(folder, file_filt_in=[], file_filt_out=[]):  
    try:
        for f in os.listdir(folder):
            path = resolve_path(os.path.join(folder,f))
             
            if os.path.isfile(path):
                if str_check_filt(path, file_filt_in, file_filt_out):
                    yield resolve_path(os.path.expandvars(path))
            else:
                yield from get_all_files_rec(path, file_filt_in, file_filt_out)
    except FileNotFoundError:
        pass

def verbatim_path_part(path):
    verbatim = ''
    for c in path:
        if not c in ['*', '?']:
            verbatim += c
        else:
            return verbatim

def get_all_files(root, file_filt_in=[], file_filt_out=[]):
    folders = []
    relative_paths = False
    for f in file_filt_in:
        verbatim_path = verbatim_path_part(f)
        if verbatim_path:
            folders += [verbatim_path]
        else:
            relative_paths = True
            
    if relative_paths:
        folders += [root]
    
    for folder in folders:
        for r,d,f in os.walk(folder):
            for file in f:
                path = os.path.join(r,file)
                if str_check_filt(path, file_filt_in, file_filt_out):
                    yield resolve_path(path)
    #     try

def filt_entry_resolve(entry):
    entry = os.path.expanduser(os.path.expandvars(entry))
    if not entry[0] in ['*', '?']:
        entry = os.path.realpath(entry)
        
    return entry


class File(Build):
    def __init__(self, name):
        super().__init__(name=name)
        
    def outdated(self):
        return True
    
    def rebuild(self):
        return resolve_path(self.srcs['name'])

class Fileset(Build):
    
    srcs_setup = {'files': SrcConf('list'),
                  'match': SrcConf('list'),
                  'ignore': SrcConf('list')
                  }
    
    def __init__(self, files=[], match=[], ignore=[], root='.'):
        super().__init__(files=files, match=match, ignore=ignore, root=root)
    
    def outdated(self):
        return True
    
    def rebuild(self):
        match = [filt_entry_resolve(m)
                    for m in self.srcs['match']]
        ignore = [filt_entry_resolve(i)
                    for i in self.srcs['ignore']]
        
        res = []
        if isinstance(self.srcs['files'], str):
            if str_check_filt(self.srcs['files'], match, ignore):
                res.append(resolve_path(self.srcs['files']))
        else:
            for f in self.srcs['files']:
                if str_check_filt(f, match, ignore):
                    res.append(resolve_path(f))
        
        if match:
            for f in get_all_files(resolve_path(self.srcs['root']), match, ignore):
                res.append(f)
        
        return res
        