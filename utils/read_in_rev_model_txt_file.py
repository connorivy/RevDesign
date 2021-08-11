# these are helper functions for my django classes

class LocalMembers:
    def __init__(self, line):
        line = line.split(',')
        
        self.node1x = float(line[0])
        self.node1y = float(line[1])
        self.node1z = float(line[2])
        self.node2x = float(line[3])
        self.node2y = float(line[4])
        self.node2z = float(line[5])

    def __str__(self):
        return f'{self.node1x}'

def define_local_members():
    path = './zz_helper_files/revit_output.txt'
    revit_output = open(path, 'r')
    lines = revit_output.readlines()
    revit_output.close()

    local_members = {}

    for line in range(len(lines)):
        key = str(line)
        value = LocalMembers(lines[line])

        local_members[key] = value

    return local_members

# mems = define_local_members()
# for key,mem in mems.items():
#     print(mem.node1x)

