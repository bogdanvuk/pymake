from pymake.build import Build, SrcConf
from pymake.builds.interact import InteractInst, Interact
import os
from collections import namedtuple

class VivadoHlsInteractInst(InteractInst):
    def __init__(self):
        super().__init__(runcmd='vivado_hls -i', prompt='vivado_hls> ')
    
    def cmd(self, text):
        super().cmd(text)
        ret = super().cmd('')
        lines = ret.split('\n')[1:-1]
        ret = [l.replace("\r", "") for l in lines]
        return ret

class VivadoHlsInteract(Build):
    def outdated(self):
        return self.res is None
    
    def rebuild(self):
        return VivadoHlsInteractInst()

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
        return namedtuple('Solution', ['name', 'config'])(
                                                          self.srcres['name'],
                                                          conf)

class VivadoHlsProject:
    def __init__(self, prj, basedir):
        self.prj = prj
        self.basedir = basedir
        self.p = VivadoHlsInteractInst()
        self._solution = None
        
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
    
    def conf(self, name, value):
        if name == 'clock':
            cmd = 'create_clock {}'
        elif (name in ['top', 'part', 'clock_uncertainty']) or (name.startswith('directive')):
            cmd = 'set_{}'.format(name) + ' {}'
        else:
            cmd = 'config_{}'.format(name) + ' {}'
            
        self.p.cmd(cmd.format(value))
    
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

    def outdated(self):
        return self.res is None

    def rebuild(self):
        folder = os.path.dirname(self.srcres['prj'])
        prj_name = os.path.basename(self.srcres['prj'])
        prj = VivadoHlsProject(prj_name, folder)
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
        pass