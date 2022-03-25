import pytest
from .helpers import *
from model.requests_get_mesh import add_coords_for_shear_walls
# from ..model.requests_analyze_mesh import *

def test_add_coords_for_shear_walls():
    for example in test_examples:
        assert add_coords_for_shear_walls(coord_dict_walls=example.coord_dict_walls, coord_list_floor=example.coords_before_adding_shearwalls) == example.coords_after_adding_shearwalls