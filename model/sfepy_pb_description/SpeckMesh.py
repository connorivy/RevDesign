from specklepy.objects import Base
from specklepy.objects.geometry import Point

import collections
import numpy as np

class CellBlock(collections.namedtuple("CellBlock", ["type", "data"])):
    # def __repr__(self):
    #     return f"<meshio CellBlock, type: {self.type}, num cells: {len(self.data)}>"

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
