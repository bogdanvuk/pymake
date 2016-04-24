import os
from collections import OrderedDict
import pickle
import shutil

def resolve_path(path):
    return os.path.realpath(os.path.normpath(os.path.expanduser(os.path.expandvars(path))))

class File:
    def __init__(self, name):
        self.name = resolve_path(name) 
    
    @property
    def timestamp(self):
        if self.exists:
            return os.path.getmtime(self.name)
        else:
            return float('-inf')
    
    @property
    def exists(self):
        return os.path.exists(self.name)
    
    @property
    def dirname(self):
        return os.path.dirname(self.name)
    
    @property
    def basename(self):
        return os.path.basename(self.name)
    
    def load(self):
        with open(self.name, 'rb') as f:
            return pickle.load(f)
    
    def dump(self, obj):
        with open(self.name, 'wb') as f:
            return pickle.dump(obj, f)
    
#     def json_load(self):
#         with open(self.name) as f:    
#             return json.load(f)
#         
#     def json_dump(self, obj):
#         with open(self.name, 'w') as f:    
#             json.dump(obj, f)
            
    def default(self):
        return str(self)
    
    def clean(self):
        if self.exists:
            if os.path.isfile(self.name):
                os.remove(self.name)
            else:
                shutil.rmtree(self.name)
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __str__(self):
        return self.name
    
    __repr__ = __str__
    
    def __hash__(self):
        return hash(self.name)

class Filedict(OrderedDict):
    def __init__(self, files = []):
        super().__init__()
        for key, f in files:
            if isinstance(f, str):
                f = File(f)
            self[key] = f

class Fileset(list):
    def __init__(self, files = [], list_timestamp=float('-inf')):
        super().__init__([File(f) for f in files])
        self.list_timestamp = list_timestamp

    @property
    def timestamp(self):
        tsm = [float('+inf'), float('-inf')]
        for f in self:
            t = f.timestamp
           
            if t < tsm[0]: tsm[0] = t
            if t > tsm[1]: tsm[1] = t
            
        return tuple(tsm)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        
        return set(self) == set(other)
    
    def __ne__(self, other):
        return not (self == other)
