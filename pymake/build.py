import time
import os
from collections import OrderedDict
import pickle
import zlib
from pymake.utils import File

class SrcConf:
    def __init__(self, collection=None, childdir=''):
        self.collection = collection
        self.childdir = childdir

class Build:
    
    srcs_setup = OrderedDict()
    
    def __init__(self, *args, **kwargs):
        self.srcs = OrderedDict()
        for s in self.srcs_setup:
            self.srcs[s] = kwargs[s]

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

    def build(self, name, builddir=None):
        start = time.time()
        if builddir is None:
            if 'BUILDDIR' not in os.environ:
                os.environ['BUILDDIR'] = os.getcwd()
                
            builddir = os.environ['BUILDDIR']

        self.builddir = builddir
        self.name = name
        
        print('PYMAKE: {}: Building {} in {} ...'.format(time.strftime("%H:%M:%S", time.localtime(start)), self.name, self.builddir))

        self.srcres = self.build_srcs()
         
        self.srchash, self.res = self.load()
        
        self.targets = self.set_targets()
        
        if self.outdated():
            self.rebuilt = True
            self.res = self.rebuild()
        else:
            self.rebuilt = False
        
        self.dump()

        print('PYMAKE: {}: {} done in {:.2f}s.'.format(time.strftime("%H:%M:%S", time.localtime(time.time())), self.name, time.time() - start))        
        return self.res

    def build_src_def(self, name, src):
        if hasattr(src, 'build'):
            res = src.build('.'.join([self.name, name]))
        else:
            res = src
        
        return res

    def build_src_collection(self, name, src, key):
        setup_fname = "setup_src_{0}_item".format(str(name))
        build_fname = "build_src_{0}_item".format(str(name))
        
        if hasattr(self, setup_fname):
            src[key] = getattr(self, setup_fname)(src, key) 
            
        if hasattr(self, build_fname):
            res = getattr(self, build_fname)(src, key)
        else:
            res = self.build_src_def(str(name), src[key])
                
        return res

    def build_src(self, name, src, key=None):

#         self.setup_builddir_for_src(name)

        if hasattr(self, "setup_src_" + str(name)):
            src = getattr(self, "setup_src_" + str(name))(src)
                        
        if hasattr(self, "build_src_" + str(name)):
            res = getattr(self, "build_src_" + str(name))(src)
        else:
            if self.srcs_setup[name].collection == 'list':
                res = []
                for key in range(len(src)):
                    res.append(self.build_src_collection(name, src, key))
            elif self.srcs_setup[name].collection == 'dict':
                res = OrderedDict()
                for key in sorted(src):
                    res[key] = self.build_src_collection(name, src, key)
            else:
                res = self.build_src_def(str(name), src)
        
#         os.environ['BUILDDIR'] = self.builddir
        
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
        srcres = OrderedDict()
        if self.srcs:
            for name, src in self.srcs.items():
                srcres[name] = self.build_src(name, src)
                
        return srcres

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
        
        if self.res:
            timestamp = self.timestamp
            
            try:
                oldest_t = timestamp[0]
            except TypeError:
                oldest_t = timestamp
            
            if oldest_t == float("-inf"):
                return True
            
            for name, res in self.srcres.items():
                if name in self.srcs_setup:
                    if self.srcs_setup[name].collection == 'list':
                        for key in range(len(res)):
                            if self.is_src_outdated(name, oldest_t, key):
                                return True
                    elif self.srcs_setup[name].collection == 'dict':
                        for key in res:
                            if self.is_src_outdated(name, oldest_t, key):
                                return True
                else:
                    if self.is_src_outdated(name, oldest_t):
                        return True

        return False

