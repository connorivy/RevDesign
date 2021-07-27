# these are helper functions for my django classes

class LocalMembers:
    def __init__(self, line):
        line = line.strip()
        bad_chars = [',', ')', '(']
        for i in bad_chars:
            line = line.replace(i, '')
        string_list = line.split(' ')
        
        self.node1x = float(string_list[0])
        self.node1y = float(string_list[1])
        self.node1z = float(string_list[2])
        self.node2x = float(string_list[3])
        self.node2y = float(string_list[4])
        self.node2z = float(string_list[5])

    def __str__(self):
        return f'{self.node1x}'

def define_local_members():
    path = './zz_helper_files/revit_output_tca.txt'
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

