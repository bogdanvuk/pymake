import os

def resolve_path(path):
    return os.path.realpath(os.path.normpath(os.path.expanduser(os.path.expandvars(path))))
