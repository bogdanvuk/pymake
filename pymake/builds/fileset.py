from pymake.build import Build, SrcConf
import fnmatch
import os
from pymake.utils import resolve_path, Fileset, File
import zlib
import json
import pickle
import collections
from collections import OrderedDict

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

def get_all_files(root, file_filt_in=[], file_filt_out=[], maxdepth=20):
    folders = set()
    relative_paths = False
    for f in file_filt_in:
        verbatim_path = verbatim_path_part(f)
        if verbatim_path:
            folders.add(verbatim_path)
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

class FileBuild(Build):
    srcs_setup = OrderedDict([
                          ('fn', SrcConf())
                          ])
    def __init__(self, fn):
        super().__init__(fn=fn)
    
    def load(self):
        return None, None
    
    def dump(self):
        pass
    
    def outdated(self):
        return True
    
    def rebuild(self):
        return File(resolve_path(self.srcres['fn']))

class FilesetBuild(Build):
    
    srcs_setup = OrderedDict([
                          ('files', SrcConf('list')), 
                          ('match', SrcConf('list')),
                          ('ignore', SrcConf('list')),
                          ('root', SrcConf()),
                          ('maxdepth', SrcConf())
                          ])
    
    def __init__(self, files=[], match=[], ignore=[], root='.', maxdepth=10):
        super().__init__(files=files, match=match, ignore=ignore, root=root, maxdepth=maxdepth)
    
#     def load(self):
#         res = None
#         self.res_file = File('$BUILDDIR/fileset_{}.pickle'.format(hex(self.calc_src_cash())[2:]))
#         
#         if self.res_file.exists:
# #             try
#             res = self.res_file.load()
# #             except:
# #                 pass
#             
#         return res
    
    def set_targets(self):
        return [self.res_file]
    
    def outdated(self):
        
        curdir = os.getcwd();
        
        os.chdir(str(self.srcres['root']))
        
        match = [filt_entry_resolve(m)
                    for m in self.srcs['match']]
        ignore = [filt_entry_resolve(i)
                    for i in self.srcs['ignore']]
        
        res = []
        if isinstance(self.srcres['files'], str):
            if str_check_filt(self.srcres['files'], match, ignore):
                res.append(resolve_path(self.srcres['files']))
        else:
            for f in self.srcres['files']:
                if str_check_filt(f, match, ignore):
                    res.append(resolve_path(f))
        
        if match:
            for f in get_all_files(resolve_path(str(self.srcres['root'])), match, ignore, self.srcres['maxdepth']):
                res.append(f)
            
        self.newres = Fileset(res, self.res_file.timestamp)
        os.chdir(curdir)
        if self.res is None:
            return True
        elif super().outdated():
            return True
        elif res != self.res:
            return True
        else:
            return False
    
    def rebuild(self):
#        self.res_file.dump(self.newres)
        return self.newres
        