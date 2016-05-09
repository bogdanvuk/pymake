from pymake.build import Build, SrcConf
from pymake.builds.interact import InteractInst, Interact
import os
from collections import namedtuple, OrderedDict
from pymake.utils import File, Filedict
import zlib
import collections
import pickle
from pymake.builds.fileset import FilesetBuild

class VivadoHlsInteractInst(InteractInst):
    @classmethod
    def open(cls):
        return super(VivadoHlsInteractInst, cls).open(runcmd='vivado_hls -i', prompt='vivado_hls> ')
    
    def clean(self):
        self.cmd('close_project')
    
    def send_quit(self):
        self.p.sendeof()
    
    def cmd(self, text, timeout=5):
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
        print('\n'.join(lines))
        return err

class VivadoHlsInteract(Build):
    def outdated(self):
        return self.res is None
    
    def rebuild(self):
        return VivadoHlsInteractInst()

Solution = namedtuple('Solution', ['name', 'config'])

class VivadoHlsSolution(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                      ('name',      SrcConf()),
                      ('part',      SrcConf()),
                      ('clock',     SrcConf()),
                      ('config',    SrcConf('dict'))
                      ])
    
    def __init__(self, name='solution1', part='xc7k325tffg900-2', clock='-period 10 -name default', config={}, **kwargs):
        super().__init__(name=name, part=part, clock=clock, config=config, **kwargs)

#     def outdated(self):
#         return self.res is None
            
    def rebuild(self):
        conf = {'part': self.srcres['part'], 'clock': self.srcres['clock']}
        conf.update(self.srcres['config'])
        return Solution(
                      self.srcres['name'],
                      collections.OrderedDict(sorted(conf.items())))

class VivadoHlsProject:
    
    def __init__(self, prj, basedir, sources, include, cflags, tb_sources, solutions, config):
        self.prj = prj
        self.basedir = basedir
        self.config = config
        self.sources = sources
        self.include = include
        self.cflags = cflags
        self.tb_sources = tb_sources
        self.p = None
        self.prj_dir = File(os.path.join(basedir, prj))
        self.files = Filedict([('prj_file', os.path.join(basedir, prj, 'vivado_hls.app')),
                               ])
# 
        self.solutions = solutions
        for s in solutions:
            self.files[s.name + '_cfg'] = os.path.join(basedir, prj, s.name, s.name + '.aps')
            self.files[s.name + '_directive'] = os.path.join(basedir, prj, s.name, s.name + '.directive')
            
        self._solution = None
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['p']
        return OrderedDict(sorted(state.items()))
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.p = None
    
    @property
    def exists(self):
        return self.files['prj_file'].exists
    
    def clean(self):
        self.prj_dir.clean()
    
    def open(self):
        self.p = VivadoHlsInteractInst.open()
#        self.p.close()
#         self.p.open()
        ret = self.p.cmd('cd {}'.format(self.basedir))
        ret = self.p.cmd('open_project {}'.format(self.prj))
        
    def configure(self):
        self.clean()
        self.open()
        
        cflags = self.cflags
        if self.include:
            cflags = ' '.join([cflags] + ['-I {}'.format(i) for i in self.include])
        
        for f in self.sources:
            self.add_file(f, cflags=cflags)
            
        for f in self.tb_sources:
            self.add_file(f, tb=True, cflags=cflags)
        
        for k,v in self.config.items():
            self.conf(k,v)
            
        for s in self.solutions:
            self.solution = s.name
            for k,v in s.config.items():
                self.conf(k,v)
                
        self.close()
    
    def add_file(self, fn, tb=False, cflags=''):
        if cflags:
            cflags = ' -cflags "{}"'.format(cflags)
        ret = self.p.cmd('add_files {}{} {}'.format('-tb' if tb else '', cflags, fn))
    
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
            
        return self.p.cmd('csynth_design', timeout=120)
    
    def conf(self, name, value):
        if name == 'clock':
            cmd = 'create_clock {}'
        elif (name in ['top', 'part', 'clock_uncertainty']) or (name.startswith('directive')):
            cmd = 'set_{}'.format(name) + ' {}'
        else:
            cmd = 'config_{}'.format(name) + ' {}'
            
        self.p.cmd(cmd.format(value))
    
    def close(self):
        if self.p:
            self.p.close()
        
    def __del__(self):
#         self.close()
        pass
        

class VivadoHlsProjectBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                     ('prj',       SrcConf()),
                     ('include',   SrcConf()),
                     ('cflags',    SrcConf()),
                     ('fileset',   SrcConf()),
                     ('tb_fileset',SrcConf()),
                     ('solutions', SrcConf('list')), 
                     ('config',    SrcConf('dict'))
                     ])
    
    def __init__(self, prj, fileset, cflags='', include=None, config={}, solutions=[VivadoHlsSolution()], tb_fileset = [], **kwargs):
        super().__init__(prj=prj, fileset=fileset, cflags=cflags, include=include, tb_fileset=tb_fileset, config=config, solutions=solutions, **kwargs)

#     def load(self):
#         res = None
#         self.res_file = File('$BUILDDIR/vivado_hls_prj_{}.pickle'.format(hex(self.calc_src_cash())[2:]))
#         res = VivadoHlsProject(self.srcres['prj'].basename, self.srcres['prj'].dirname)
#         
#         return res
    
    def set_targets(self):
        return [self.res_file]

    def outdated(self):
        if (self.res is None) or (not self.res.exists) or (super().outdated()) or (not self.res_file.exists):
            return True
        else:
            
            return False

    def rebuild(self):
        res = VivadoHlsProject(prj          = self.srcres['prj'].basename, 
                               basedir      = self.srcres['prj'].dirname,
                               include      = self.srcres['include'],
                               cflags       = self.srcres['cflags'],
                               sources      = self.srcres['fileset'], 
                               tb_sources   = self.srcres['tb_fileset'], 
                               solutions    = self.srcres['solutions'], 
                               config       = self.srcres['config']
                               )
        res.clean()
        res.configure()
#         open(str(self.res_file), 'w')
        return res
                
class VivadoHlsVhdlSynthBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                              ('hlsprj', SrcConf()),
                              ('synths', SrcConf()),
                              ('solution', SrcConf())
                              ])
    
    def __init__(self, hlsprj, synths=FilesetBuild(match=['./solution1/syn/vhdl/*.vhd']), solution='solution1', **kwargs):
        super().__init__(hlsprj=hlsprj, synths=synths, solution=solution, **kwargs)
    
    def build_src_synths(self, name, src, collection='', key = []):
        src.srcs['root'] = self.srcres['hlsprj'].prj_dir
        return super().def_build_src('synths', src, collection, key)
    
#     def set_targets(self):
#         return [self.srcres['vhdl']]
    
    def outdated(self):
        if not self.srcres['synths']:
            return True
        elif self.srcres['synths'].timestamp[0] < self.srcres['hlsprj'].sources.timestamp[1]:
            return True
        else:
            return False
#        return self.res is None
    
    def rebuild(self):
        prj = self.srcres['hlsprj']
        prj.open()
        prj.solution = self.srcres['solution']
        prj.synth()
#         prj.vhdl = self.build_src_synths(self.srcs['synths'])
        
        return self.build_src_synths('synths', self.srcs['synths'])
