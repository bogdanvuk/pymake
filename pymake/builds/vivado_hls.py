from pymake.build import Build, SrcConf
from pymake.builds.interact import InteractInst, Interact
import os
from collections import namedtuple
from pymake.builds.fileset import File
import zlib
import collections
import pickle

class VivadoHlsInteractInst(InteractInst):
    def __init__(self):
        super().__init__(runcmd='vivado_hls -i', prompt='vivado_hls> ')
    
    def cmd(self, text, resp=False, timeout=5):
        super().cmd(text, timeout)

#         resp_received = False
        
#         while (not resp_received):
        ret = super().cmd('', timeout)
        lines_raw = ret.split('\n')[1:-1]
#         for l in lines_raw:
# #             if l[0] == '@':
#                 lines.append(l)
#                 resp_received = True
                    
#             if not resp:
#                 resp_received = True 
        lines = []
        err = 0
        for l in lines_raw:
            line = l.replace("\r", "")
            lines.append(line)
            if line.startswith('@E'):
                err = 1            
        
        self.resp = lines
        return err

class VivadoHlsInteract(Build):
    def outdated(self):
        return self.res is None
    
    def rebuild(self):
        return VivadoHlsInteractInst()

Solution = namedtuple('Solution', ['name', 'config'])

class VivadoHlsSolution(Build):
    srcs_setup = {'config': SrcConf('dict'),
                  }
        
    def __init__(self, name='solution1', part='xc7k325tffg900-2', clock='-period 10 -name default', config={}):
        super().__init__(name=name, part=part, clock=clock, config=config)

    def outdated(self):
        return self.res is None
            
    def rebuild(self):
        conf = {'part': self.srcres['part'], 'clock': self.srcres['clock']}
        conf.update(self.srcres['config'])
        return Solution(
                      self.srcres['name'],
                      collections.OrderedDict(sorted(conf.items())))

class VivadoHlsProject:
    def __init__(self, prj, basedir):
        self.prj = prj
        self.basedir = basedir
        self.p = VivadoHlsInteractInst()
        self.prj_dir = File(os.path.join(basedir, prj))
        self.prj_file = File(os.path.join(basedir, prj, 'vivado_hls.app'))
        self._solution = None
    
    @property
    def exists(self):
        return self.prj_file.exists
    
    def open(self):
        self.p.close()
        self.p.open()
        ret = self.p.cmd('cd {}'.format(self.basedir))
        ret = self.p.cmd('open_project {}'.format(self.prj))
    
    def add_file(self, fn, tb=False):
        ret = self.p.cmd('add_files {} {}'.format('-tb' if tb else '', fn))
    
    @property
    def solution(self):
        return self._solution
        
    @solution.setter
    def solution(self, name):
        self.p.cmd('open_solution {}'.format(name))
        self._solution = name
    
    def synth(self, solution=None):
        if solution:
            self.solution = solution
            
        return self.p.cmd('csynth_design', timeout=-1)
    
    def conf(self, name, value):
        if name == 'clock':
            cmd = 'create_clock {}'
            resp = False
        elif (name in ['top', 'part', 'clock_uncertainty']) or (name.startswith('directive')):
            cmd = 'set_{}'.format(name) + ' {}'
            resp = True
        else:
            cmd = 'config_{}'.format(name) + ' {}'
            resp = True
            
        self.p.cmd(cmd.format(value), resp=False)
    
    def close(self):
        self.p.close()
        
    def __del__(self):
        self.close()
        

class VivadoHlsProjectBuild(Build):
    srcs_setup = {'solutions': SrcConf('list'),
                  'config' : SrcConf('dict')
                  }
    
    def __init__(self, prj, fileset, config={}, solutions=[VivadoHlsSolution()], tb_fileset = None):
        super().__init__(prj=prj, fileset=fileset, tb_fileset=tb_fileset, config=config, solutions=solutions)

    def load(self):
        
        res = None
        name = zlib.crc32(pickle.dumps(collections.OrderedDict(sorted(self.srcres.items()))))
#         name = 0xffffffff
# 
#         name = zlib.crc32(str(self.srcs['prj']).encode(), name)
#         for src_name in ['fileset', 'tb_fileset']:
#             for f in self.srcs[src_name]:
#                 name = zlib.crc32(str(f).encode(), name)
#                 
#         for key in sorted(self.srcs['config']):
#             name = zlib.crc32(str(key + self.srcs['config'][key]).encode(), name)
#             
#         for s in self.srcs['solutions']:
#             name = zlib.crc32(str(s.name).encode(), name)
#             for key in sorted(s.config):
#                 name = zlib.crc32(str(key + s.config[key]).encode(), name)

        self.res_file = File('$BUILDDIR/vivado_hls_prj_{}.json'.format(hex(name)[2:]))
        
        folder = os.path.dirname(self.srcres['prj'])
        prj_name = os.path.basename(self.srcres['prj'])
        res = VivadoHlsProject(prj_name, folder)
        
        return res
    
    def set_targets(self):
        pass

    def outdated(self):
        if self.res is None:
            return True
        elif super().outdated():
            return True
        elif res != self.res:
            return True
        else:
            return False

    def rebuild(self):
        prj.open()

        for f in self.srcres['fileset']:
            prj.add_file(f)
            
        for f in self.srcres['tb_fileset']:
            prj.add_file(f, tb=True)
        
        for k,v in self.srcres['config'].items():
            prj.conf(k,v)
            
        for s in self.srcres['solutions']:
            prj.solution = s.name
            for k,v in s.config.items():
                prj.conf(k,v)
        
        return prj
                
class VivadoHlsSynthBuild(Build):
    def __init__(self, hlsprj):
        super().__init__(hlsprj=hlsprj)
        
    def outdated(self):
        return self.res is None
    
    def rebuild(self):
        self.srcres['hlsprj'].synth()
