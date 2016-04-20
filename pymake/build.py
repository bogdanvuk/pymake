import time
class Build(object):
    
    def __init__(self, srcattrs, *args, **kwargs):
        self.src_attrs = srcattrs
        self.srcs = kwargs

    def build(self):
        start = time.time()
        pass

    def build_src_def(self, name, src):
        if hasattr(src, 'build'):
            res = src.build()
        else:
            res = src
        
        return res


    def build_src_collection(self, name, src, key, collection_type):
        setup_fname = "setup_src_{0}_{1}".format(str(name), collection_type)
        build_fname = "build_src_{0}_{1}".format(str(name), collection_type)
        
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
            if name in self.src_attrs:
                if self.src_attrs[name] is list:
                    res = []
                    for key in range(len(src)):
                        res.append(self.build_src_collection(name, src, key, collection_type))
                elif self.src_attrs[name] is dict:
                    res = {}
                    for key in src:
                        res[key] = self.build_src_collection(name, src, key, collection_type)
            else:
                res = self.build_src_def(str(name), src)
        
        self.reset_env()
        
        return res

    def build_srcs(self):
        if self.srcs:
            for name, src in self.srcs.items():
                self.res[name] = self.build_src(name, src)
