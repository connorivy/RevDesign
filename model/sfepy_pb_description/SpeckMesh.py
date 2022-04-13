from specklepy.objects import Base
from specklepy.objects.geometry import Point, Mesh

import collections
import numpy as np

from collections import deque
import itertools

topological_dimension = {
    "line": 1,
    "polygon": 2,
    "triangle": 2,
    "quad": 2,
    "tetra": 3,
    "hexahedron": 3,
    "wedge": 3,
    "pyramid": 3,
    "line3": 1,
    "triangle6": 2,
    "quad9": 2,
    "tetra10": 3,
    "hexahedron27": 3,
    "wedge18": 3,
    "pyramid14": 3,
    "vertex": 0,
    "quad8": 2,
    "hexahedron20": 3,
    "triangle10": 2,
    "triangle15": 2,
    "triangle21": 2,
    "line4": 1,
    "line5": 1,
    "line6": 1,
    "tetra20": 3,
    "tetra35": 3,
    "tetra56": 3,
    "quad16": 2,
    "quad25": 2,
    "quad36": 2,
    "triangle28": 2,
    "triangle36": 2,
    "triangle45": 2,
    "triangle55": 2,
    "triangle66": 2,
    "quad49": 2,
    "quad64": 2,
    "quad81": 2,
    "quad100": 2,
    "quad121": 2,
    "line7": 1,
    "line8": 1,
    "line9": 1,
    "line10": 1,
    "line11": 1,
    "tetra84": 3,
    "tetra120": 3,
    "tetra165": 3,
    "tetra220": 3,
    "tetra286": 3,
    "wedge40": 3,
    "wedge75": 3,
    "hexahedron64": 3,
    "hexahedron125": 3,
    "hexahedron216": 3,
    "hexahedron343": 3,
    "hexahedron512": 3,
    "hexahedron729": 3,
    "hexahedron1000": 3,
    "wedge126": 3,
    "wedge196": 3,
    "wedge288": 3,
    "wedge405": 3,
    "wedge550": 3,
    "VTK_LAGRANGE_CURVE": 1,
    "VTK_LAGRANGE_TRIANGLE": 2,
    "VTK_LAGRANGE_QUADRILATERAL": 2,
    "VTK_LAGRANGE_TETRAHEDRON": 3,
    "VTK_LAGRANGE_HEXAHEDRON": 3,
    "VTK_LAGRANGE_WEDGE": 3,
    "VTK_LAGRANGE_PYRAMID": 3,
    None : None,
}
class CellBlock(Base):
    def __init__(
        self,
        cell_type = None,
        data = None,
        # tags: list[str] | None = None,
    ):
        self.type = cell_type
        self.data = data

        # if cell_type.startswith("polyhedron"):
        #     self.dim = 3
        # else:
        self.data = self.data
        self.dim = topological_dimension[cell_type]

        # self.tags = [] if tags is None else tags

    def __repr__(self):
        items = [
            "meshio CellBlock",
            f"type: {self.type}",
            f"num cells: {len(self.data)}",
            f"tags: {self.tags}",
        ]
        return "<" + ", ".join(items) + ">"

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
        units=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.units = units # default value for units is 'ft'
        self.points = points
        if cells:
            self.cells = [
                CellBlock(cells[index].type, cells[index].data.tolist()) for index in range(len(cells))
            ]
            self.create_display_value()
        else:
            self.cells = cells

        if cell_sets:
            for key in cell_sets:
                new_list = []
                # remove None values
                cell_sets[key] = [i for i in cell_sets[key] if i is not None]
                for index in range(len(cell_sets[key])):
                    if isinstance(cell_sets[key][index], np.ndarray):
                        new_list.extend(cell_sets[key][index].tolist())
                cell_sets[key] = new_list
            self.cell_sets = cell_sets
        else:
            self.cell_sets = {}
        self.point_data = {} if point_data is None else point_data
        self.cell_data = {} if cell_data is None else cell_data
        self.field_data = {} if field_data is None else field_data
        self.point_sets = {} if point_sets is None else point_sets
        self.gmsh_periodic = gmsh_periodic
        self.info = info
        self.units = units # default value for units is 'ft'
        for key, value in kwargs.items():
            self[key] = value

    def create_display_value(self):
        faces = []
        for cell in self.cells:
            if cell.type == 'triangle':
                for tri in cell.data:
                    faces.extend([0, tri[0], tri[1], tri[2]])

        # print(faces)
        # print(colors)
        self.displayValue = [Mesh.create(list(itertools.chain.from_iterable(self.points)), faces)]
        self.displayValue[0].units = self.units
        print('display mesh units', type(self.displayValue[0]), self.units, self.displayValue[0].units)

    def get_polyline(self):
        lines = set()
        for cell in self.cells:
            if cell.type == 'triangle':
                for tri in cell.data:
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

