import time
import os
from collections import OrderedDict
import pickle
import zlib
from pymake.utils import File, resolve_path
import re
import argparse
import sys

class SrcConf:
    def __init__(self, collection='', childdir='', target='all'):
        self.collection = collection
        self.childdir = childdir
        self.target = target

class Build:
    
    srcs_setup = OrderedDict([
                              ('env',       SrcConf('dict')),
                              ('args',      SrcConf('tuple'))
                              ])
    # OrderedDict([('BUILDDIR','$BUILDDIR'), ('SRCDIR', '$SRCDIR'), ('BUILDNAME', '$BUILDNAME')])
    def __init__(self, *args, 
                 env={}, 
                 **kwargs):
        # Napravi da mogu da se kopiraju pickle fajlovi iz buildova istih klasa, ako su ulazni parametri isti. 
        
        srcs = kwargs.copy()
        srcs['env'] = env
        
        self.srcs = OrderedDict()
        for s in self.srcs_setup:
            if s not in ['args', 'kwargs']:
                self.srcs[s] = srcs[s]
                del srcs[s]
        
        self.srcs_setup = self.srcs_setup.copy()
        
        for k,v in srcs.items():
            self.srcs[k] = v
                
        if args:
            self.srcs['args'] = args

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

    def cli_add_arg_item(self, parser, name, src, key=[]):
        name = ':'.join([name] + list(map(str, key)))
        if hasattr(src, 'build'):
            src.cli_add_build_args(parser, name)
        else:
            parser.add_argument('--' + name, dest=name, metavar='VAL', help=str(src))

    def cli_add_arg(self, parser, name, src, collection, key=[]):
        cur_collection, _, collection = collection.partition(':')
        if cur_collection in ['list', 'tuple']:
            for s in src:
                if hasattr(s, 'build'):
                    break
            else:
                self.cli_add_arg_item(parser, name, src, key)
                return

            for subkey in range(len(src)):
                self.cli_add_arg(parser, name, src[subkey], collection=collection, key=key + [subkey])
        elif cur_collection == 'dict':
            # If none of subkeys are Builds, offer whole dict as one argument
            for s in src:
                if hasattr(src[s], 'build'):
                    break
            else:
                self.cli_add_arg_item(parser, name, src, key)
                return
                
            for subkey in sorted(src):
                self.cli_add_arg(parser, name, src[subkey], collection=collection, key=key + [subkey])
        else:
            self.cli_add_arg_item(parser, str(name), src, key=key)
    
    def cli_add_build_args(self, parser, name):
        for srcname, src in self.srcs.items():
            self.cli_add_arg(parser, '.'.join([name, srcname]), src, collection=self.srcs_setup.get(srcname, SrcConf()).collection)
    
    def cli_build(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('targets', nargs='*', default=['all'])
        for name, src in self.srcs.items():
            self.cli_add_arg(parser, name, src, collection=self.srcs_setup.get(name, SrcConf()).collection)
        
        args = parser.parse_args()
        for t in args.targets:
            self.build(target=t)

    def build(self, target='all', **kwargs):
        self.start_time = time.time()
        self.build_src_env('env', self.srcs['env'])

        if target != 'all':
            src_defs = target.partition('.')[0]
            keys_src = src_defs.split(':')
            src_name = keys_src[0]
            child = self.srcs[src_name]
            collection = self.srcs_setup.get(src_name, SrcConf()).collection
            keys = []
            for k in keys_src[1:]:
                collection = collection.partition(':')[2]
                if k.isalpha():
                    k = int(k)
                
                keys.append[k]
                child = child[k]
            
            return self.build_src(src_name, child, collection, keys)
            

#         self.builddir = self.set_environ_var('BUILDDIR', builddir, os.getcwd())
#         os.makedirs(resolve_path(self.builddir), exist_ok=True)
#         self.srcdir = self.set_environ_var('SRCDIR', srcdir, os.getcwd())
#         
#         self.name = name
        
        self.build_srcs()
         
        self.srchash, self.res = self.load()
        
        self.targets = self.set_targets()
        
        if self.outdated():
            self.rebuilt = True
            self.res = self.rebuild()
            self.dump()
        else:
            self.rebuilt = False

        print('PYMAKE: {}: {} done in {:.2f}s.'.format(time.strftime("%H:%M:%S", time.localtime(time.time())), os.environ['BUILDNAME'], time.time() - self.start_time))        
        return self.res

    def def_build_src_item(self, name, src, key=[]):
        if hasattr(src, 'build'):
            target = self.srcs_setup.get(name, SrcConf()).target
            if (target != 'all'):
                pass
            name = '.'.join([os.environ['BUILDNAME'], name])
            name = '_'.join([name] + list(map(str, key)))
            os.environ['BUILDNAME'] = name
            
            res = src.build(target=target)
        else:
            res = src
        
        return res

    def def_build_src(self, name, src, collection='', key=[]):
        cur_collection, _, collection = collection.partition(':')
        if cur_collection in ['list', 'tuple']:
            res = []
            for subkey in range(len(src)):
                res.append(self.build_src(name, src[subkey], collection=collection, key=key + [subkey]))
        elif cur_collection == 'dict':
            res = OrderedDict()
            for subkey in sorted(src):
                res[subkey] = self.build_src(name, src[subkey], collection=collection, key=key + [subkey])
        else:
            res = self.def_build_src_item(str(name), src, key=key)
            
        return res

    def build_src(self, name, src, collection='', key=[]):
        if hasattr(self, "build_src_" + str(name)):
            res = getattr(self, "build_src_" + str(name))(name=name, src=src, collection=collection, key=key)
        else:
            res = self.def_build_src(name=name, src=src, collection=collection, key=key)
        
        if hasattr(self, "build_postproc_" + str(name)):
            res = getattr(self, "build_postproc_" + str(name))(name=name, res=res, collection=collection, key=key)
        
        self.reset_env()
            
        return res

    def build_src_env(self, name, src, collection='', key=[]):
        res = OrderedDict()
        for k,v in src.items():
            if k in ['BUILDDIR', 'SRCDIR', 'PICKLEDIR']:
                v = resolve_path(v)
            res[k] = v #resolve_path(v)
            os.environ[k] = res[k]
            
        self.environ_cpy = os.environ.copy()
        
        if 'BUILDNAME' not in os.environ:
            os.environ['BUILDNAME'] = os.path.basename(sys.argv[0]) + '_all'

        if 'SRCDIR' not in os.environ:
            os.environ['BUILDDIR'] = os.getcwd()
        
        if 'BUILDDIR' not in os.environ:
            os.environ['BUILDDIR'] = os.environ['SRCDIR']

        if 'PICKLEDIR' not in os.environ:
            os.environ['PICKLEDIR'] = os.path.join(os.environ['BUILDDIR'], '.pickle')
            
        print('PYMAKE: {}: Building {} in {} ...'.format(time.strftime("%H:%M:%S", time.localtime(self.start_time)), os.environ['BUILDNAME'], os.environ['BUILDDIR']))
        return res
        
    def reset_env(self):
#         if 'env' in self.srcres:
#             for k,v in self.srcres['env']:
#                 os.environ[k] = v
        os.environ.update(self.environ_cpy)

    def get_hash(self, obj):
        return zlib.crc32(pickle.dumps(obj))

    def calc_src_cash(self):
        return zlib.crc32(pickle.dumps(self.srcres.items()))
    
    def get_pickle(self):
        return File('$PICKLEDIR/{}.pickle'.format(os.environ['BUILDNAME']))

    def setup_builddir_for_src(self, name):
        if name in self.srcs_setup:
            childdir = self.srcs_setup[name].childdir
        else:
            childdir = ''
        os.environ['BUILDDIR'] = os.path.join(os.environ['BUILDDIR'], childdir.format(name=name))

    def build_srcs(self):
        self.srcres = OrderedDict()
        for name, src in self.srcs.items():
            if name != 'env':
                self.srcres[name] = self.build_src(name, src, collection=self.srcs_setup.get(name, SrcConf()).collection)
               
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
