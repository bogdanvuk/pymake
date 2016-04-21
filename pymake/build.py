import time
import os

class SrcConf:
    def __init__(self, collection=None, childdir=''):
        self.collection = collection
        self.childdir = childdir

class Build:
    
    srcs_setup = {}
    
    def __init__(self, *args, **kwargs):
        self.srcs = kwargs
        self.res = None
        self.srcres = None
        self.builddir = None

    def build(self, builddir=None):
        start = time.time()
        if builddir is None:
            if 'BUILDDIR' not in os.environ:
                os.environ['BUILDDIR'] = os.getcwd()
                
            builddir = os.environ['BUILDDIR']
            
        self.builddir = builddir
        
        self.srcres = self.build_srcs()
         
        if self.outdated():
            self.res = self.rebuild()
        
        return self.res

    def build_src_def(self, name, src):
        if hasattr(src, 'build'):
            res = src.build()
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

        self.setup_builddir_for_src(name)

        if hasattr(self, "setup_src_" + str(name)):
            src = getattr(self, "setup_src_" + str(name))(src)
                        
        if hasattr(self, "build_src_" + str(name)):
            res = getattr(self, "build_src_" + str(name))(src)
        else:
            if name in self.srcs_setup:
                if self.srcs_setup[name].collection == 'list':
                    res = []
                    for key in range(len(src)):
                        res.append(self.build_src_collection(name, src, key))
                elif self.srcs_setup[name].collection == 'dict':
                    res = {}
                    for key in src:
                        res[key] = self.build_src_collection(name, src, key)
            else:
                res = self.build_src_def(str(name), src)
        
        os.environ['BUILDDIR'] = self.builddir
        
        return res

    def setup_builddir_for_src(self, name):
        if name in self.srcs_setup:
            childdir = self.srcs_setup[name].childdir
        else:
            childdir = ''
        os.environ['BUILDDIR'] = os.path.join(os.environ['BUILDDIR'], childdir.format(name=name))

    def build_srcs(self):
        srcres = {}
        if self.srcs:
            for name, src in self.srcs.items():
                srcres[name] = self.build_src(name, src)
                
        return srcres

    def get_timestamp(self):
        oldest_t_time = None
        newest_t_time = None
        for t in self.targets:
            timestamp = None
            
            if hasattr(t, 'get_timestamp'):
                timestamp = t.get_timestamp()
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

    def outdated(self):
        if self.res:
            timestamp = self.get_timestamp()
            
            try:
                oldest_t = timestamp[0]
            except TypeError:
                oldest_t = timestamp
            
            if oldest_t == float("-inf"):
                return True
            
            for name, res in self.res.items():
                try:
                    collection_type = self.src_properties[name]['collection']
                except KeyError:
                    collection_type = None
                    
                if collection_type:
                    if collection_type  == 'list':
                        for key in range(len(res)):
                            if self.is_src_outdated(res[key], oldest_t):
                                return True
                    elif collection_type == 'dict':
                        for key in res:
                            if self.is_src_outdated(res[key], oldest_t):
                                return True
                else:
                    if self.is_src_outdated(res, oldest_t):
                        return True

        return False

