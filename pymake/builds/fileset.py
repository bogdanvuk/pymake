from pymake.build import Build

class Fileset(Build):
    def __init__(self, 
                 files : list = [],
                 match : list = [],
                 ignore : list = []
                 ):
        super().__init__(self.__init__.__annotations__, files=files, match=match, ignore=ignore)
    