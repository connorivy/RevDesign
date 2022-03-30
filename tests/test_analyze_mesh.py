from math import floor
from dotmap import DotMap
import pytest

from model.sfepy_pb_description.linear_elastic import *
from .examples import ex1
from model.requests_get_mesh import *
from model.sfepy_pb_description.connectToSpeckle import get_client, get_globals_obj, get_transport

class Example:
    def __init__(self, **kwargs) -> None:
        for key,value in kwargs.items():
            setattr(self,key,value)

@pytest.fixture(scope='class', params=[ex1.define()])
def example_obj(request):
    example_obj = Example(**request.param)
    return example_obj

@pytest.mark.usefixtures("example_obj")
class TestAnalyzeMesh:
    @pytest.fixture(scope="class")
    def client(self, example_obj):
        return get_client(example_obj.HOST)

    @pytest.fixture(scope="class")
    def transport(self, example_obj, client):
        return get_transport(client, example_obj.STREAM_ID)

    def test_floor_obj(self, example_obj, client, transport):
        globals_obj = get_globals_obj(client, transport, example_obj.STREAM_ID)
        floor_obj = DotMap(globals_obj[example_obj.FLOOR_ID])

        assert floor_obj.speckMesh.points == example_obj.mesh.points
        assert floor_obj.speckMesh.minus_x_wind_load_point_ids == example_obj.minus_x_wind_load_point_ids
        assert floor_obj.speckMesh.plus_x_wind_load_point_ids == example_obj.plus_x_wind_load_point_ids
        assert floor_obj.speckMesh.minus_y_wind_load_point_ids == example_obj.minus_y_wind_load_point_ids
        assert floor_obj.speckMesh.plus_y_wind_load_point_ids == example_obj.plus_y_wind_load_point_ids
        assert floor_obj.speckMesh.vert_shear_walls == example_obj.vert_shear_walls
        assert floor_obj.speckMesh.horiz_shear_walls == example_obj.horiz_shear_walls

    # def test_get_reactions_in_region(self, example_obj):
    #     get_reactions_in_region(pb, state, regions, fixed_nodes)

    def test_reactions(self, example_obj):
        options = {
            'mesh_points' : example_obj.mesh.points,
            'minus_x_wind_load_point_ids' : example_obj.minus_x_wind_load_point_ids,
            'plus_x_wind_load_point_ids': example_obj.plus_x_wind_load_point_ids,
            'minus_y_wind_load_point_ids' : example_obj.minus_y_wind_load_point_ids,
            'plus_y_wind_load_point_ids' : example_obj.plus_y_wind_load_point_ids,
            'vert_shear_walls' : example_obj.vert_shear_walls.copy(),
            'horiz_shear_walls' : example_obj.horiz_shear_walls.copy(),
            'fixed_nodes' : example_obj.fixed_nodes,
            'wind_dir' : example_obj.wind_dir
        }
        f = create_mesh_applied_loads(**options)

        print(f, f.shape)
        assert f.shape == ( 2 * len(example_obj.mesh.points),) # if this doesn't pass then there are likely multiple nodes in almost an identical location
        f= f.reshape((-1, 2))
        assert f[example_obj.dofs].tolist() == example_obj.reactions

