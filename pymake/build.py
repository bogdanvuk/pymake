import time
import os
from collections import OrderedDict
import pickle
import zlib
from pymake.utils import File, resolve_path
import re

class SrcConf:
    def __init__(self, collection='', childdir='', postproc=None):
        self.collection = collection
        self.childdir = childdir
        self.postproc = postproc

class Build:
    
    srcs_setup = OrderedDict()
    
    def __init__(self, *args, **kwargs):
        # Napravi da mogu da se kopiraju pickle fajlovi iz buildova istih klasa, ako su ulazni parametri isti. 
        
        srcs = kwargs.copy()
        
        self.srcs = OrderedDict()
        for s in self.srcs_setup:
            if s not in ['args', 'kwargs']:
                self.srcs[s] = srcs[s]
                del srcs[s]
        
        self.srcs_setup = self.srcs_setup.copy()
        
        if srcs:
            self.srcs['kwargs'] = srcs
            if 'kwargs' not in self.srcs_setup:
                self.srcs_setup['kwargs'] = SrcConf('dict')
                
        if args:
            self.srcs['args'] = args
            if 'args' not in self.srcs_setup:
                self.srcs_setup['args'] = SrcConf('list')

        self.res = None
        self.srcres = None
        self.builddir = None

    def clean(self, name, builddir=None):
        if builddir is None:
            if 'BUILDDIR' not in os.environ:
                os.environ['BUILDDIR'] = os.getcwd()
                
            builddir = os.environ['BUILDDIR']
        
        self.name = name
        self.builddir = builddir
        self.srcres = self.build_srcs()
        self.res = self.load()
        self.targets = self.set_targets()
        self.clean_targets()

    def clean_targets(self):
        for t in self.targets:
            if hasattr(t, 'clean'):
                t.clean()

    def load(self):
        res = None
        srchash = None
        self.res_file = self.get_pickle()
        
        if self.res_file.exists:
            try:
                (srchash, res) = self.res_file.load()
            except Exception as e:
#                 print(e.msg)
                pass
            
        return srchash, res
    
    def dump(self):
        self.res_file.dump((self.get_hash(self.srcres), self.res))
    
    def set_targets(self):
        pass

    def set_environ_var(self, name, val, default):
        if val is None:
            if name not in os.environ:
                os.environ[name] = default
                
            val = os.environ[name]
        else:
            os.environ[name] = val
            
        return val

    def build(self, name, builddir=None, srcdir=None):
        start = time.time()

        self.builddir = self.set_environ_var('BUILDDIR', builddir, os.getcwd())
        os.makedirs(resolve_path(self.builddir), exist_ok=True)
        self.srcdir = self.set_environ_var('SRCDIR', srcdir, os.getcwd())
        
        self.name = name
        
        print('PYMAKE: {}: Building {} in {} ...'.format(time.strftime("%H:%M:%S", time.localtime(start)), self.name, self.builddir))

        self.build_srcs()
         
        self.srchash, self.res = self.load()
        
        self.targets = self.set_targets()
        
        if self.outdated():
            self.rebuilt = True
            self.res = self.rebuild()
            self.dump()
        else:
            self.rebuilt = False

        print('PYMAKE: {}: {} done in {:.2f}s.'.format(time.strftime("%H:%M:%S", time.localtime(time.time())), self.name, time.time() - start))        
        return self.res

    def src_build_item(self, name, src, key=[], builddir='$BUILDDIR', srcdir='$SRCDIR'):
        os.environ['BUILDDIR'] = resolve_path(builddir)
        os.environ['SRCDIR'] = resolve_path(srcdir)
        if hasattr(src, 'build'):
            name = '.'.join([self.name, name])
            name = '_'.join([name] + list(map(str, key)))
            res = src.build(name)
        else:
            res = src
        
        os.environ['BUILDDIR'] = self.builddir
        os.environ['SRCDIR'] = self.srcdir
        
        return res

    def build_src(self, name, src, collection='', key=[]):
        cur_collection, _, collection = collection.partition(':')
        if cur_collection in ['list', 'tuple']:
            res = []
            for subkey in range(len(src)):
                if self.name == 'hlsmac':
                    pass
                res.append(self.build_src(name, src[subkey], collection=collection, key=key + [subkey]))
                if self.name == 'hlsmac':
                    pass
        elif cur_collection == 'dict':
            res = OrderedDict()
            for subkey in sorted(src):
                res[subkey] = self.build_src(name, src[subkey], collection=collection, key=key + [subkey])
        else:
            res = self.src_build_item(str(name), src, key=key)
        
        if self.srcs_setup[name].postproc:
            res = self.srcs_setup[name].postproc(name, res, key)
        
        return res

    def get_hash(self, obj):
        return zlib.crc32(pickle.dumps(obj))

    def calc_src_cash(self):
        return zlib.crc32(pickle.dumps(self.srcres.items()))
    
    def get_pickle(self):
        return File('$BUILDDIR/{}.pickle'.format(self.name))

    def setup_builddir_for_src(self, name):
        if name in self.srcs_setup:
            childdir = self.srcs_setup[name].childdir
        else:
            childdir = ''
        os.environ['BUILDDIR'] = os.path.join(os.environ['BUILDDIR'], childdir.format(name=name))

    def build_srcs(self):
        self.srcres = OrderedDict()
        if self.srcs:
            for name, src in self.srcs.items():
                build_func = getattr(self, "build_src_" + str(name), self.build_src)
                res = build_func(name, src, collection=self.srcs_setup[name].collection)
                    
                self.srcres[name] = res
                
    @property
    def timestamp(self):
        oldest_t_time = None
        newest_t_time = None
        for t in self.targets:
            timestamp = None
            
            if hasattr(t, 'timestamp'):
                timestamp = t.timestamp
#             else:
#                 if os.path.exists(t):
#                     timestamp = os.path.getmtime(t)
#                 else:
#                     return float('-inf')
            
            try:
                oldest = timestamp[0]
                newest =  timestamp[1]
            except TypeError:
                oldest = newest = timestamp

            if (oldest is not None) and ((oldest_t_time is None) or (oldest_t_time > oldest)):
                oldest_t_time = oldest
            
            if (newest is not None) and ((newest_t_time is None) or (newest_t_time < newest)):
                newest_t_time = newest
                
        return oldest_t_time, newest_t_time

    def is_src_outdated(self, name, oldest_t, key = None):
        if key:
            src = self.srcs[name][key]
            srcres = self.srcres[name][key]
        else:
            src = self.srcs[name]
            srcres = self.srcres[name]
        
        if hasattr(src, 'rebuilt'):
            if src.rebuilt:
                return True
        
        if oldest_t:
            timestamp = None
            if hasattr(srcres, 'timestamp'):
                timestamp = srcres.timestamp
                                
            try:
                newest =  timestamp[1]
            except TypeError:
                newest = timestamp
            
            if (newest is not None) and (newest > oldest_t):
                return True

    def outdated(self):
        if self.get_hash(self.srcres) != self.srchash:
            return True
        
#         if self.res:
#             timestamp = self.timestamp
#             
#             try:
#                 oldest_t = timestamp[0]
#             except TypeError:
#                 oldest_t = timestamp
#             
#             if oldest_t == float("-inf"):
#                 return True
#             
#             for name, res in self.srcres.items():
#                 if name in self.srcs_setup:
#                     if self.srcs_setup[name].collection == 'list':
#                         for key in range(len(res)):
#                             if self.is_src_outdated(name, oldest_t, key):
#                                 return True
#                     elif self.srcs_setup[name].collection == 'dict':
#                         for key in res:
#                             if self.is_src_outdated(name, oldest_t, key):
#                                 return True
#                 else:
#                     if self.is_src_outdated(name, oldest_t):
#                         return True

        return False

    def rebuild(self):
        if len(self.srcres) == 1:
            if 'args' in self.srcres:
                return self.srcres['args']
            elif 'kwargs' in self.srcres:
                return self.srcres['kwargs']
            
        return self.srcres
