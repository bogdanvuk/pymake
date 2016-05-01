from pymake.build import Build
import pexpect
import sys
import atexit

class InteractInst:
    instances = {}

    def __init__(self, runcmd, prompt):
        self.prompt = prompt
        self.runcmd = runcmd
        self.p = pexpect.spawnu(self.runcmd, echo=False)
#         self.p.logfile = sys.stdout
        self.p.expect(self.prompt)
        self.hdr = self.p.before

        self.mutex = False
    
    @classmethod
    def closeall(cls):
        for k,v in cls.instances.items():
            for i in v:
                i.close(delete=True)
    
    @classmethod
    def find_available_inst(cls, runcmd):
        if runcmd in cls.instances:
            for inst in cls.instances[runcmd]:
                if not inst.mutex:
                    return inst
            else:
                return None
        else:
            return None
        
    @classmethod
    def open(cls, runcmd, prompt):
        inst = cls.find_available_inst(runcmd)
        if inst is None:
            inst = cls(runcmd, prompt)
            if runcmd not in cls.instances:
                cls.instances[runcmd] = []
            
            cls.instances[runcmd].append(inst)
        else:
            if hasattr(inst, 'clean'):
                inst.clean()
            
        inst.mutex = True
        
        return inst
    
    def close(self, delete=False):
        if delete:
            if self.p and self.p.isalive():
                if (hasattr(self, 'send_quit')):
                    self.send_quit()
                self.p.terminate(True)
        else:
            self.mutex = False
    
    def cmd(self, text, timeout=-1):
        if text:
            self.p.sendline(text)
        self.p.expect(self.prompt, timeout=timeout)
        self.p.flush()
        return self.p.before
    
    def __del__(self):
        self.close(delete=True)

atexit.register(InteractInst.closeall)
      
class Interact(Build):
    def __init__(self, 
                 cmd,
                 prompt,
                 ):
        super().__init__(self.__init__.__annotations__, cmd=cmd, prompt=prompt)
        
    def outdated(self):
        return self.res is None
    
    def rebuild(self):
        return InteractInst(self.srcs['cmd'], self.srcs['prompt'])
