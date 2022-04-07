from specklepy.objects import Base
from specklepy.objects.geometry import Point, Mesh

import collections
import numpy as np

from collections import deque
import itertools

class CellBlock(collections.namedtuple("CellBlock", ["type", "data"])):
    def __repr__(self):
        return f"<meshio CellBlock, type: {self.type}, num cells: {len(self.data)}>"

    def __len__(self):
        return len(self.data)

class SpeckMesh(Base):
    def __init__(
        self,
        points=None,
        cells=None,
        point_data=None,
        cell_data=None,
        field_data=None,
        point_sets=None,
        cell_sets=None,
        gmsh_periodic=None,
        info=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.points = points
        if cells:
            self.cells = [
                CellBlock(cell_type, data.tolist()) for cell_type, data in cells
            ]
            self.create_display_value()
        else:
            self.cells = cells
        self.point_data = {} if point_data is None else point_data
        self.cell_data = {} if cell_data is None else cell_data
        self.field_data = {} if field_data is None else field_data
        self.point_sets = {} if point_sets is None else point_sets
        self.cell_sets = {} if cell_sets is None else cell_sets
        self.gmsh_periodic = gmsh_periodic
        self.info = info
        for key, value in kwargs.items():
            self[key] = value

    def create_display_value(self):
        faces = []
        colors = []
        i=0
        for cell in self.cells:
            if cell[0] == 'triangle':
                for tri in cell[1]:
                    faces.extend([0, tri[0], tri[1], tri[2]])
                    colors.extend([111*i/10, 111*i/10, 111*i/10, 111*i/10])
                    i += 1

        # print(faces)
        # print(colors)
        self.displayValue = [Mesh.create(list(itertools.chain.from_iterable(self.points)), faces, colors)]

    def get_polyline(self):
        lines = set()
        for cell in self.cells:
            if cell[0] == 'triangle':
                for tri in cell[1]:
                    l1, l2, l3 = self.get_lines_from_triangle(tri)
                    lines.add(l1)
                    lines.add(l2)
                    lines.add(l3)

        lines = list(lines)
        lines.sort()
        polyline = deque([lines.pop(0)])

        print('lines', lines, len(lines))
        while lines != []:
            len_polyline = len(polyline)
            for index in range(len(lines)):
                # CASE 1
                # line[index] - (5,6) polyline (3,4)(4,5)
                if lines[index][0] == polyline[-1][-1]:
                    polyline.append(lines.pop(index))
                    break
                # CASE 2
                # line[index] - (1,5) polyline (3,4)(4,5)
                elif lines[index][1] == polyline[-1][-1]:
                    new_segment = lines.pop(index)
                    polyline.append((new_segment[1],new_segment[0]))
                    break
                # CASE 3
                # line[index] - (2,3) polyline (3,4)(4,5)
                elif lines[index][1] == polyline[0][0]:
                    polyline.appendleft(lines.pop(index))
                    break
                # CASE 4
                # line[index] - (3,9) polyline (3,4)(4,5)
                elif lines[index][0] == polyline[0][0]:
                    new_segment = lines.pop(index)
                    polyline.appendleft((new_segment[1],new_segment[0]))
                    break
            if len(polyline) == len_polyline:
                print('POLYLINE FORMATION DIDNT WORK', lines, polyline)
                break
        print('POLYLINE FORMATION WORKED', lines, polyline)
            
        self.polyline = list(polyline)


    def get_lines_from_triangle(self, tri):
        l1 = (min(tri[0], tri[1]), max(tri[0], tri[1]))
        l2 = (min(tri[1], tri[2]), max(tri[1], tri[2]))
        l3 = (min(tri[0], tri[2]), max(tri[0], tri[2]))

        return l1,l2,l3

