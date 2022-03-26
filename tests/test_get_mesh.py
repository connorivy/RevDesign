from dotmap import DotMap
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

    @pytest.mark.skip(reason="I don't want to query the server too many times")
    def test_query_shearwalls(self, client, example_obj):
        assert query_shearwalls(client=client, STREAM_ID=example_obj.STREAM_ID, OBJECT_ID=example_obj.OBJECT_ID) == \
                example_obj.coord_dict_walls

    def test_get_wind_load_point_ids(self, example_obj):
        wlpi = get_wind_load_point_ids(example_obj.coords_after_adding_shearwalls, example_obj.surface)
        assert wlpi['minus_x_wind_load_point_ids'] == example_obj.minus_x_wind_load_point_ids
        assert wlpi['plus_x_wind_load_point_ids'] == example_obj.plus_x_wind_load_point_ids
        assert wlpi['minus_y_wind_load_point_ids'] == example_obj.minus_y_wind_load_point_ids
        assert wlpi['plus_y_wind_load_point_ids'] == example_obj.plus_y_wind_load_point_ids

def test_adjust_wind_line():
    '''
    case 1:
                    4  --------------   7             curve
            0   -----------------------------  10     segment
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[4,0]},{'x':[7,0]}]}), 0) == [[0,4],[7,10]] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,4]},{'x':[0,7]}]}), 1) == [[0,4],[7,10]] # y dir

    '''
    case 2:
            -5 -------------- 4                         curve
                   0 ----------------------------- 10   segment
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[-5,0]},{'x':[4,0]}]}), 0) == [[4,10]] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,-5]},{'x':[0,4]}]}), 1) == [[4,10]] # y dir

    '''
    case 3:
                                7   --------------  14  curve
            0 -----------------------------  10         segment
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[7,0]},{'x':[14,0]}]}), 0) == [[0,7]] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,7]},{'x':[0,14]}]}), 1) == [[0,7]] # y dir

    '''
    case 4:
        -5 ---------------------------------------  14  curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[-5,0]},{'x':[14,0]}]}), 0) == [] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,-5]},{'x':[0,14]}]}), 1) == [] # y dir

    '''
    case 5:
            0 -----------------------------  10         curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[10,0]}]}), 0) == [] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[0,10]}]}), 1) == [] # y dir

    '''
    case 6:
            0 ------------------  7                     curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[7,0]}]}), 0) == [[7,10]] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[0,7]}]}), 1) == [[7,10]] # y dir

    '''
    case 7:
                  4 -----------------------  10         curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[4,0]},{'x':[10,0]}]}), 0) == [[0,4]] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,4]},{'x':[0,10]}]}), 1) == [[0,4]] # y dir
    '''
    case 8:
            0 --------------------------------  12      curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[12,0]}]}), 0) == [] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,0]},{'x':[0,12]}]}), 1) == [] # y dir

    '''
    case 9:
         -4 -------------------------------  10         curve
            0 -----------------------------  10         segment 
    '''
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[-4,0]},{'x':[10,0]}]}), 0) == [] # x dir
    assert adjust_wind_line([[0, 10]], [0,10], DotMap({'points': [{'x':[0,-4]},{'x':[0,10]}]}), 1) == [] # y dir


def test_lines_overlap():
    '''
    case 1:
         -4 -- 0                                        curve
            0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[-4,0]},{'x':[0,0]}]}), 0) == False # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,-4]},{'x':[0,0]}]}), 1) == False # y dir

    '''
    case 2:
             -4 ----- -1                                             curve
                         0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[-4,0]},{'x':[-1,0]}]}), 0) == False # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,-4]},{'x':[0,-1]}]}), 1) == False # y dir
    '''
    case 3:
                                                14 -- 20  curve
            0 -----------------------------  10           segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[14,0]},{'x':[20,0]}]}), 0) == False # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,14]},{'x':[0,20]}]}), 1) == False # y dir

    '''
    case 4:
                                                     10 ----- 14     curve
                         0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[10,0]},{'x':[14,0]}]}), 0) == False # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,10]},{'x':[0,14]}]}), 1) == False # y dir

    '''
    case 5:
         -4 ---- 1                                      curve
            0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[-4,0]},{'x':[1,0]}]}), 0) == True # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,-4]},{'x':[0,1]}]}), 1) == True # y dir

    '''
    case 6:
                                8 ------------- 11      curve
            0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[8,0]},{'x':[11,0]}]}), 0) == True # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,8]},{'x':[0,11]}]}), 1) == True # y dir

    '''
    case 7:
                    4 ------------- 7      curve
            0 -----------------------------  10         segment 
    '''
    assert lines_overlap([0,10], DotMap({'points': [{'x':[4,0]},{'x':[7,0]}]}), 0) == True # x dir
    assert lines_overlap([0,10], DotMap({'points': [{'x':[0,4]},{'x':[0,7]}]}), 1) == True # y dir




