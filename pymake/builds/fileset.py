from pymake.build import Build, SrcConf
import fnmatch
import os
from pymake.utils import resolve_path
import zlib
import json
import pickle
import collections

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

from json import JSONEncoder

def _default(self, obj):
    return repr(obj)

JSONEncoder.default = _default  # Replace with the above.

class File:
    def __init__(self, name):
        self.name = resolve_path(name) 
    
    @property
    def timestamp(self):
        return os.path.getmtime(self.name)
    
    @property
    def exists(self):
        return os.path.exists(self.name)
    
    def load(self):
        with open(self.name, 'rb') as f:
            return pickle.load(f)
    
    def dump(self, obj):
        with open(self.name, 'wb') as f:
            return pickle.dump(obj, f)
    
    def json_load(self):
        with open(self.name) as f:    
            return json.load(f)
        
    def json_dump(self, obj):
        with open(self.name, 'w') as f:    
            json.dump(obj, f)
            
    def default(self):
        return str(self)
    
    def clean(self):
        if self.exists:
            os.remove(self.name)
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __str__(self):
        return self.name
    
    __repr__ = __str__
    
    def __hash__(self):
        return hash(self.name)

class Fileset(list):
    def __init__(self, files):
        super().__init__([File(f) for f in files])
        
    def __eq__(self, other):
        if len(self) != len(other):
            return False
        
        return set(self) == set(other)
    
    def __ne__(self, other):
        return not (self == other)

class FilesetBuild(Build):
    
    srcs_setup = {'files': SrcConf('list'),
                  'match': SrcConf('list'),
                  'ignore': SrcConf('list')
                  }
    
    def __init__(self, files=[], match=[], ignore=[], root='.'):
        super().__init__(files=files, match=match, ignore=ignore, root=root)
    
    def load(self):
        res = None
#         name = 0xffffffff

#         name = zlib.crc32(pickle.dumps(self.srcres))
        name = zlib.crc32(pickle.dumps(collections.OrderedDict(sorted(self.srcres.items()))))

#         for src_name in ['files', 'match', 'ignore']:
#             for f in self.srcs[src_name]:
#                 name = zlib.crc32(str(f).encode(), name)

        self.res_file = File('$BUILDDIR/fileset_{}.pickle'.format(hex(name)[2:]))
        
        if self.res_file.exists:
#             try
            res = self.res_file.load()
#             except:
#                 pass
            
        return res
    
    def set_targets(self):
        return [self.res_file]
#         targets = []
#         self.targets = [self.res_file]
        
#         return res 
    
    def outdated(self):
        
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
            
        self.newres = Fileset(res)
        
        if self.res is None:
            return True
        elif super().outdated():
            return True
        elif res != self.res:
            return True
        else:
            return False
    
    def rebuild(self):
        self.res_file.dump(self.newres)
        return self.newres
        