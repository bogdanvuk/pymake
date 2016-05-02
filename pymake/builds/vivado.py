from pymake.builds.interact import InteractInst
from pymake.utils import File, Filedict
import os
from collections import OrderedDict
from pymake.build import Build, SrcConf
from pymake.builds.fileset import FileBuild
import string

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
        lines_raw = resp.strip().split('\n')     
        for line in lines_raw:
            if line.startswith('ERROR:') and except_err:
                raise VivError(lines_raw)
            
            if strip_warn and line.startswith('WARNING:'):
                self.warnings.append(line)
            else:
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

class IpInst:
    def __init__(self, name, vlnv, ipdir=None, config={}):
        self.name = name
        self.vlnv = vlnv
        self.config = config
        self.ipdir = ipdir
        
class IpInstBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                     ('name',      SrcConf()),
                     ('vlnv',      SrcConf()),
                     ('ipdir',     SrcConf()),
                     ('config',    SrcConf('dict'))
                     ])
    def __init__(self, name, vlnv, ipdir=None, config={}, **kwargs):
        super().__init__(name=name, vlnv=vlnv, ipdir=ipdir, config=config, **kwargs)
        
    def rebuild(self):
        return IpInst(name        = self.srcres['name'], 
                      vlnv        = self.srcres['vlnv'],
                      ipdir       = self.srcres['ipdir'], 
                      config      = self.srcres['config']
                    )
    
class VivadoProject:
    
    def __init__(self, name, prjdir, sources = OrderedDict(), ips=[], config = OrderedDict()):
        self.name = name
        self.config = config
        self.sources = sources
        self.p = None
        self.prjdir = prjdir
        self.ips = ips
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
            self.p.cmd('create_project {} {}'.format(self.name, self.prjdir))
        pass
        
    def configure(self):
#        self.clean()
        self.open()

        for k,v in self.config.items():
            self.conf(k,v)
            
        for n,f in self.sources.items():
            self.add_fileset(n,f)
            self.p.cmd('update_compile_order')
        
        if self.ips:
            self.add_all_ips()
#         for f in self.sources:
#             self.add_file(f)
                
        self.close()
    
    def add_ip(self, ip):
        ret = self.p.cmd('get_ips ' + ip.name)

        rebuild = False

        if ret.strip() == ip.name:
            ip_dir = self.p.cmd('get_property IP_DIR [get_ips ' + ip.name + ']')[0]
#             js_params = os.path.join(ip_dir, 'params.js')
#         
#             if os.path.isfile(js_params):
#                 with open(js_params) as f:
#                     params = json.load(f)
#                 
#                 if params != ip.prop:
#                     rebuild = True
#             else:
#                 rebuild = True
    
#             if rebuild:
# #                 self.p.cmd('remove_files', '[get_files ' + ip.module + '.xci]')
#                 self.p.cmd('reset_target', 'all', '[get_ips ' + ip.module + ']')
        else:
            self.p.cmd('create_ip -vlnv {vlnv} -module_name {module_name}'.format(vlnv=ip.vlnv, 
                                                                              module_name=ip.name))
            
#             ip_dir = self.p.cmd('get_property IP_DIR [get_ips ' + ip.module + ']')[0]
#             js_params = os.path.join(ip_dir, 'params.js')
            
            rebuild = True

        if rebuild:
#             with open(js_params, 'w') as f:
#                 json.dump(ip.prop, f) 
            
            if ip.config:
                prop_list = ' '.join(['CONFIG.' + k + ' {' + v + '}' for k,v in ip.prop.items()])
                self.p.cmd('set_property -dict [list ' + prop_list + '] [get_ips ' + ip.module + ']')
            
#         self.p.cmd('validate_ip', '-verbose', '-save_ip', '[get_ips ' + ip.module + ']')
    
    def add_all_ips(self):
        ip_repo_paths = set()
        for i in self.ips:
            if i.ipdir:
                ip_repo_paths.add(str(i.ipdir.dirname))
        
        if ip_repo_paths:
            self.p.cmd('set_property ip_repo_paths {{{}}} [current_project]'.format(' '.join(ip_repo_paths)))
            self.p.cmd('update_ip_catalog')
        
        for i in self.ips:
            self.add_ip(i)
            
        prjips = self.p.cmd('get_ips', strip_warn=True).split('\n')[0]
        removal = []
        ipmodules = [ip.name for ip in self.ips]
        for i in prjips:
            if (i not in ipmodules):
                removal.append(i + '.xci')
        
        if removal:
            cmd = ['remove_files']
            cmd += ['{' + ' '.join(removal) + '}']
            self.p.cmd(' '.join(cmd))
    
    def add_fileset(self, name, fileset):
        if name:
            self.p.cmd('create_fileset -quiet {}'.format(name))

        self.add_files(fileset, name)
        
        cmd = ['get_files']
        if name:
            cmd += ['-of', '[get_filesets {' + name + '}]']
        
        prjfiles = self.p.cmd(' '.join(cmd)).split(' ')
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

    def __init__(self, name, prjdir, ipdir, sources = {}, ipconfig = {}, config = {}):
        self.ipdir = ipdir
        self.ipconfig = ipconfig
        super().__init__(name=name, prjdir=prjdir, sources=sources, config=config)

    def ipx_set_prop(self, name, val):
        return self.p.cmd("set_property {name} {val} [ipx::current_core]".format(name=name, val=val))
        
    def ipx_cmd(self, cmd, timeout=2):
        return self.p.cmd('ipx::{} [ipx::current_core]'.format(cmd), timeout=timeout)
    
    def configure(self):
        super().configure()

        self.p.cmd('ipx::package_project -root_dir {}'.format(self.ipdir))

        for k,v in self.ipconfig.items():
            self.ipx_set_prop(k,v)

        self.ipx_cmd('save_core')

class VivadoProjectBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([
                     ('name',      SrcConf()),
                     ('prjdir',    SrcConf()),
                     ('sources',   SrcConf('dict')),
                     ('ips',       SrcConf('list')), 
                     ('config',    SrcConf('dict'))
                     ])
    
    def __init__(self, name, prjdir=None, sources={}, ips=[], config={}, **kwargs):
        if prjdir is None:
            prjdir = FileBuild(os.path.join('$BUILDDIR', name))
            
        super().__init__(name=name, prjdir=prjdir, sources=sources, ips=ips, config=config, **kwargs)

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
                            ips         = self.srcres['ips'],
                            config      = self.srcres['config']
                           )
#        res.clean()
        res.configure()
#         open(str(self.res_file), 'w')
        return res

class VivadoIpProjectBuild(VivadoProjectBuild):
    srcs_setup = VivadoProjectBuild.srcs_setup.copy()
    srcs_setup.update([
                       ('ipdir',    SrcConf()),
                       ('ipconfig', SrcConf('dict'))
                       ])

    def __init__(self, name, ipdir, prjdir=None, sources={}, ipconfig = {}, config={}, **kwargs):
        super().__init__(name=name, prjdir=prjdir, ipdir=ipdir, sources=sources, ipconfig=ipconfig, config=config, **kwargs)

    def rebuild(self):
        res = VivadoIpProject(name        = self.srcres['name'], 
                            prjdir      = self.srcres['prjdir'],
                            ipdir       = self.srcres['ipdir'],
                            sources     = self.srcres['sources'],
                            ipconfig    = self.srcres['ipconfig'], 
                            config      = self.srcres['config']
                           )
#        res.clean()
        res.configure()
#         open(str(self.res_file), 'w')
        return res
    
class VivadoIpBuild(Build):
    srcs_setup = Build.srcs_setup.copy()
    srcs_setup.update([('ipprj',   SrcConf()),
                       ])
    
    def __init__(self, ipprj, **kwargs):
        super().__init__(ipprj=ipprj, **kwargs)
        
    def rebuild(self):
        return self.srcres['ipprj'].ipdir
