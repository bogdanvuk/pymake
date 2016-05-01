from pymake.builds.interact import InteractInst
from pymake.utils import File, Filedict
import os
from collections import OrderedDict
from pymake.build import Build, SrcConf

class VivError(Exception):
    pass

class VivadoInteractInst(InteractInst):
#     def __init__(self):
#         super().__init__(runcmd='vivado -mode tcl', prompt='Vivado% ')
    
    @classmethod
    def open(cls):
        return super(VivadoInteractInst, cls).open(runcmd='vivado -mode tcl', prompt='Vivado% ')
    
    def clean(self):
        while(1):
            try:
                self.cmd('close_project')
            except VivError:
                return
    
    def send_quit(self):
        self.p.sendline("exit")
    
    def cmd(self, text, timeout=5, strip_warn=False, except_err=True):
        resp = super().cmd(text, timeout)
        print(resp)
        self.warnings = []
        ret = []
        lines_raw = resp.split('\n')     
        for line in lines_raw:
            if line.startswith('ERROR:') and except_err:
                raise VivError(lines_raw)
            
            if line.startswith('WARNING:'):
                self.warnings.append(line)
                if not strip_warn:
                    ret.append(line)
                
#         return self.p.before.decode()
#        print('\n'.join(ret))
        return '\n'.join(ret)
    
    def cmd_live(self, cmd, timeout=30, strip_warn=False, except_err=True):
        self.p.sendline(cmd)
        resp = []
        res = 0
        while res == 0:
            res = self.p.expect(['\r\n', 'Vivado%'], timeout)
            if res == 0:
                resp.append(self.p.before)
                yield self.p.before
            
        for ln in resp:
            if except_err and ln.startswith('ERROR:'):
                raise VivError('\n'.join(resp))
  
    
class VivadoProject:
    
    def __init__(self, name, prjdir, sources = OrderedDict(), config = OrderedDict()):
        self.name = name
        self.config = config
        self.sources = sources
        self.p = None
        self.prjdir = prjdir
        self.prjfile = File(os.path.join(str(self.prjdir), name + '.xpr'))
        self.files = Filedict([('prjfile', self.prjfile),
                               ])
# 
#         self.solutions = solutions
#         for s in solutions:
#             self.files[s.name + '_cfg'] = os.path.join(basedir, prj, s.name, s.name + '.aps')
#             self.files[s.name + '_directive'] = os.path.join(basedir, prj, s.name, s.name + '.directive')
            
        self._solution = None
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['p']
        return OrderedDict(sorted(state.items()))
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.p = None

    def synth_status(self):
        self.open()    
        dirty = False

        try:
            status = self.p.cmd('get_property', 'STATUS', '[get_runs synth_1]')[0]
            if status == 'Not started':
                dirty = True
        except VivError:
            self.cmd('create_run', '-flow', '{Vivado Synthesis 2015}', 'synth_1')
            dirty = True
        
        runs = self.cmd_list('get_runs')[0]
        needs_refresh = self.cmd_list('get_property', 'NEEDS_REFRESH', '[get_runs]')[0]
        
        for r, d in zip(runs, needs_refresh):
            if d == '1':
                self.cmd('reset_run', r)    
                dirty = True
        
        self.close()        
        return dirty
    
    def run_synth(self):
        self.open()                
        self.p.cmd('launch_runs synth_1 -jobs 3')
         
#         p = Process(target=tail, args=('/data/projects/so_ip_eth/so_ip_eth_1G_mac/result/master_build/master_build.runs/synth_1/runme.log',))
#         p.start()
         
        for ln in self.p.cmd_live('wait_on_run synth_1', timeout=3600):
            print(ln)
         
        self.close()
    
    @property
    def exists(self):
        return self.files['prjfile'].exists
    
    def clean(self):
        self.prjdir.clean()
    
    def open(self):
        self.p = VivadoInteractInst.open()
#        ret = self.p.cmd('cd {}'.format(self.basedir))
        try:
            self.p.cmd('open_project {}'.format(self.prjfile))
        except VivError:
            self.p.cmd('create_project {} {}'.format(self.name, self.basedir))
        pass
        
    def configure(self):
#        self.clean()
        self.open()

        for k,v in self.config.items():
            self.conf(k,v)
            
        for n,f in self.sources.items():
            self.add_fileset(n,f)
            self.p.cmd('update_compile_order')
        
#         for f in self.sources:
#             self.add_file(f)
                
        self.close()
    
    def add_fileset(self, name, fileset):
        if name:
            self.p.cmd('create_fileset -quiet {}'.format(name))

        self.add_files(fileset, name)
        
        cmd = ['get_files']
        if name:
            cmd += ['-of', '[get_filesets {' + name + '}]']
        
        prjfiles = self.p.cmd(' '.join(cmd)).split('\n')[0]
        removal = []
        for f in prjfiles:
            if (f not in fileset) and (os.path.splitext(f)[1] != ".xci"):
                removal.append(f)
        
        if removal:
            cmd = ['remove_files']
            cmd += ['-fileset', '[get_filesets {' + name + '}]']
            cmd += ['{' + ' '.join(removal) + '}']
            self.p.cmd(' '.join(cmd))
    
    def add_files(self, fileset, fileset_name=None):
        cmd = ['add_files', '-norecurse', '-quiet']
        
        if fileset_name:
            cmd += ['-fileset', fileset_name]
        
#         pref = os.path.commonprefix([self.srcdir, self.prjdir])
        
#         relf = [os.path.relpath(str(f), str(self.prjdir)) 
#                     for f in files]
        
        cmd += ['{' + ' '.join(list(map(str, fileset))) + '}']
        
        return self.p.cmd(' '.join(cmd))

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
    
class VivadoIpProject(VivadoProject):

    def __init__(self, name, prjdir, ipdir, sources = OrderedDict(), config = OrderedDict()):
        self.ipdir = ipdir
        super().__init__(name=name, prjdir=prjdir, sources=sources, config=config)

    def ipx_cmd(self, cmd, timeout=2):
        return self.p.cmd('ipx::{} [ipx::current_core]'.format(cmd), timeout=timeout)
    
    def configure(self):
        super().configure()
        
        self.p.cmd('ipx::package_project -root_dir {}'.format(self.ipdir))
        self.ipx_cmd('save_core')

class VivadoProjectBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                     ('name',      SrcConf()),
                     ('prjdir',    SrcConf()),
                     ('sources',   SrcConf('dict')),
                     ('config',    SrcConf('dict'))
                     ])
    
    def __init__(self, name, prjdir, sources={}, config={}, **kwargs):
        super().__init__(name=name, prjdir=prjdir, sources=sources, config=config, **kwargs)

    def set_targets(self):
        return [self.res_file]

    def outdated(self):
        try:
            if (self.res is None) or (not self.res.exists) or (super().outdated()) or (not self.res_file.exists):
                return True
        except Exception as e:
            print("PYMAKE: Rebuilding because exception was raised: " + str(e))
            return True
        
        return False

    def rebuild(self):
        res = VivadoProject(name        = self.srcres['name'], 
                            prjdir      = self.srcres['prjdir'],
                            sources     = self.srcres['sources'], 
                            config      = self.srcres['config']
                           )
#        res.clean()
        res.configure()
#         open(str(self.res_file), 'w')
        return res

class VivadoIpProjectBuild(VivadoProjectBuild):
    srcs_setup = VivadoProjectBuild.srcs_setup.copy()
    srcs_setup.update([('ipdir',   SrcConf()),
                       ])

    def __init__(self, name, prjdir, ipdir, sources={}, config={}, **kwargs):
        super().__init__(name=name, prjdir=prjdir, ipdir=ipdir, sources=sources, config=config, **kwargs)

    def rebuild(self):
        res = VivadoIpProject(name        = self.srcres['name'], 
                            prjdir      = self.srcres['prjdir'],
                            ipdir       = self.srcres['ipdir'],
                            sources     = self.srcres['sources'], 
                            config      = self.srcres['config']
                           )
#        res.clean()
        res.configure()
#         open(str(self.res_file), 'w')
        return res
