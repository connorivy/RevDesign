# import pytest
# from .examples import ex1
# from model.sfepy_pb_description.connectToSpeckle import get_client

# class Example:
#     def __init__(self, **kwargs) -> None:
#         for key,value in kwargs.items():
#             setattr(self,key,value)

# @pytest.fixture(scope='class', params=[ex1.define()])
# def example_obj(request):
#     print('REQUEST.param', len(request.param))
#     example_obj = Example(**request.param)
#     return example_obj

# @pytest.mark.usefixtures("example_obj")
# class TestExample:
#     @pytest.fixture(scope="session")
#     def client(self, example_obj):
#         return get_client(example_obj.HOST, example_obj.STREAM_ID)

    

#     def test_is_valid_example(self, example_obj):
#         assert hasattr(example_obj, 'HOST')
#         assert hasattr(example_obj, 'STREAM_ID')
#         assert hasattr(example_obj, 'OBJECT_ID')
#         assert hasattr(example_obj, 'outline')
#         assert isinstance(example_obj.outline.segments, list)
#         assert hasattr(example_obj, 'coords_before_adding_shearwalls')
#         assert hasattr(example_obj, 'coords_after_adding_shearwalls')
#         assert hasattr(example_obj, 'coord_dict_walls')

