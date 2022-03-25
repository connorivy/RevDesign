import pytest
from .examples import ex1
from model.requests_get_mesh import *
from model.sfepy_pb_description.connectToSpeckle import get_client

class Example:
    def __init__(self, **kwargs) -> None:
        for key,value in kwargs.items():
            setattr(self,key,value)

@pytest.fixture(scope='class', params=[ex1.define()])
def example_obj(request):
    example_obj = Example(**request.param)
    return example_obj

@pytest.mark.usefixtures("example_obj")
class TestGetMesh:
    @pytest.fixture(scope="class")
    def client(self, example_obj):
        return get_client(example_obj.HOST)

    def test_is_valid_example(self, example_obj):
        assert hasattr(example_obj, 'HOST')
        assert hasattr(example_obj, 'STREAM_ID')
        assert hasattr(example_obj, 'OBJECT_ID')
        assert hasattr(example_obj, 'outline')
        assert isinstance(example_obj.outline.segments, list)
        assert hasattr(example_obj, 'coords_before_adding_shearwalls')
        assert hasattr(example_obj, 'coords_after_adding_shearwalls')
        assert hasattr(example_obj, 'coord_dict_walls')

    def test_get_coords_list(self, example_obj):
        assert get_coords_list(example_obj) == \
                example_obj.coords_before_adding_shearwalls

    def test_add_coords_for_shear_walls(self, example_obj):
        assert add_coords_for_shear_walls(coord_dict_walls=example_obj.coord_dict_walls, coord_list_floor=example_obj.coords_before_adding_shearwalls) == \
                example_obj.coords_after_adding_shearwalls

    def test_query_shearwalls(self, client, example_obj):
        assert query_shearwalls(client=client, STREAM_ID=example_obj.STREAM_ID, OBJECT_ID=example_obj.OBJECT_ID) == \
                example_obj.coord_dict_walls

