from pymake.build import Build
import pexpect

class InteractInst:
    def __init__(self, runcmd, prompt):
        self.prompt = prompt
        self.runcmd = runcmd
        self.p = None
    
    def open(self):
        self.p = pexpect.spawn(self.runcmd)
        self.p.expect(self.prompt)
        self.hdr = self.p.before.decode()
    
    def close(self):
        if self.p and self.p.isalive():
            self.p.sendeof()
            self.p.terminate(True)
    
    def cmd(self, text):
        self.p.sendline(text)
        self.p.expect(self.prompt)
        self.p.flush()
        return self.p.before.decode()
    
    def __del__(self):
        self.close()
        
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
