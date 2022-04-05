from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from graphql import value_from_ast
import pygmsh
import numpy as np
import json
import math

from .shear_walls.shear_wall_classes import ShearWall, StackedShearWall, Project

from .requests_get_mesh import point_in_poly, query_shearwalls, lines_overlap
from .sfepy_pb_description.SpeckMesh import SpeckMesh
from .sfepy_pb_description.connectToSpeckle import edit_data_in_obj, get_client, get_globals_obj, get_latest_commit, get_transport, get_object, send_to_speckle

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base
from gql.gql import gql


@csrf_exempt
def build_shearwalls(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        OBJECT_ID = request.POST.get('OBJECT_ID')
        # change to get from server
        # floors = json.loads(request.POST.get('floors'))

        client = get_client(HOST)
        project_info = Project()
        shear_wall_objects = query_shearwall_objects(client, STREAM_ID, OBJECT_ID, project_info, 1)
        coord_dict_floor = query_floors(client, STREAM_ID, OBJECT_ID, 1)

        # stacked_walls = []
        data_to_change = update_shearwall_data(shear_wall_objects = shear_wall_objects, coord_dict_floor=coord_dict_floor)

        transport = get_transport(client, STREAM_ID)
        globals = get_globals_obj(client, transport, STREAM_ID)
        edit_data_in_obj(globals, data_to_change)
        send_to_speckle(client, transport, STREAM_ID, globals, 'globals')

        # stacked_walls = get_stacked_walls(shear_wall_objects)
        # print(coord_dict_walls)

        return JsonResponse({'data_to_change': data_to_change}, status = 200)
    return JsonResponse({}, status = 400)

def query_shearwall_objects(client, STREAM_ID, OBJECT_ID, project_info, num_decimals):
    query = gql(
        """
            query($myQuery:[JSONObject!], $stream_id: String!, $object_id: String!){
                stream(id:$stream_id){
                    object(id:$object_id){
                        children(query: 
                            $myQuery select:["length","studHeight","start.x","start.y","start.z","end.x","end.y","end.z","level.elevation","topLevel.elevation", 
                            "baseOffset","topOffset","viewRange.topElevation","viewRange.bottomElevation","loadInfo.totalShear",
                            "loadInfo.floorTrib","loadInfo.floorLoadType"]
                        ){
                            objects{
                                id
                                data
                            }
                        }
                    }
                }
            }
        """)

    params = {
        "myQuery": [
            {
                "field":"lineType",
                "value":"shearWall",
                "operator":"="
            }
        ],
        "stream_id": STREAM_ID, 
        "object_id": OBJECT_ID
    }

    dict_from_server = client.httpclient.execute(query, variable_values=params)
    # print(dict_from_server)
    shear_walls = []
    for wall in dict_from_server['stream']['object']['children']['objects']:
        shear_walls.append(ShearWall(
            projectInfo = project_info,
            id = wall['id'],
            length = round(wall['data']['length'], num_decimals),
            studHeight = try_except_from_server(wall,num_decimals,'data','studHeight'),
            start = (round(wall['data']['start']['x'], num_decimals),round(wall['data']['start']['y'], num_decimals)),
            end = (round(wall['data']['end']['x'], num_decimals),round(wall['data']['end']['y'], num_decimals)),
            baseLevelElevation = round(wall['data']['level']['elevation'], num_decimals),
            topLevelElevation = try_except_from_server(wall,num_decimals,'data','topLevel','elevation'),
            baseOffset = try_except_from_server(wall,num_decimals,'data','baseOffset'),
            topOffset = try_except_from_server(wall,num_decimals,'data','topOffset'),
            topViewElevation = round(wall['data']['viewRange']['topElevation'], num_decimals), 
            bottomViewElevation = round(wall['data']['viewRange']['bottomElevation'], num_decimals),
            totalShear = try_except_from_server(wall,num_decimals,'data','loadInfo','totalShear'),
            floorTrib = try_except_from_server(wall,num_decimals,'data','loadInfo','floorTrib'),
            floorLoadType = try_except_from_server(wall,num_decimals,'data','loadInfo','floorLoadType'),
        ))

    return shear_walls

def try_except_from_server(wall, num_decimals, path1, path2, path3=None):
    try:
        if not path3:
            x = round(wall[path1][path2],num_decimals)
        else:
            x = round(wall[path1][path2][path3], num_decimals)
        return x
    except:
        return -1

def query_floors(client, STREAM_ID, OBJECT_ID, num_decimals):
    query = gql(
        """
            query($myQuery:[JSONObject!], $stream_id: String!, $object_id: String!){
                stream(id:$stream_id){
                    object(id:$object_id){
                        children(query: $myQuery select:["outline.segments", "parameters.STRUCTURAL_ELEVATION_AT_TOP.value", "level"]){
                            objects{
                                id
                                data
                            }
                        }
                    }
                }
            }
        """)

    # eventually maybe pass in list of floor_ids in view
    # see operatorsWhitelist - https://github.com/specklesystems/speckle-server/blob/e2c43d225d8282646e5e06acac77dcc2d21b7910/packages/server/modules/core/services/objects.js
    params = {
        "myQuery": [
            {
                "field":"speckle_type",
                "value":"Objects.BuiltElements.Floor:Objects.BuiltElements.Revit.RevitFloor",
                "operator":"="
            }
        ],
        "stream_id": STREAM_ID, 
        "object_id": OBJECT_ID
    }

    dict_from_server = client.httpclient.execute(query, variable_values=params)
    # print(dict_from_server)
    floor_dict = {}
    for floor in dict_from_server['stream']['object']['children']['objects']:
        coords = []
        seen_coords = set()
        for segment in floor['data']['outline']['segments']:
                x0 = round(segment['start']['x'], num_decimals)
                y0 = round(segment['start']['y'], num_decimals)
                x1 = round(segment['end']['x'], num_decimals)
                y1 = round(segment['end']['y'], num_decimals)
                if (x0, y0) not in seen_coords:
                    seen_coords.add((x0, y0))
                    coords.append((x0, y0))
                if (x1, y1) not in seen_coords:
                    seen_coords.add((x1, y1))
                    coords.append((x1, y1))
        floor_dict[floor['id']] = {
            'polygon' : coords,
            'elevation_at_top': floor['data']['parameters']['STRUCTURAL_ELEVATION_AT_TOP']['value'],
            'level': floor['data']['level']
        }

        if len(coords) != len(floor['data']['outline']['segments']):
            print('WARNING: # of coords != # 0f segments')

        floor_dict[floor['id']]['polygon'].append(floor_dict[floor['id']]['polygon'][0])

    floor_dict_sorted = {}
    for id in sorted(floor_dict, key=lambda x: floor_dict[x]['elevation_at_top']):
        floor_dict_sorted[id] = floor_dict[id]
    
    print('coord_dict_floor', floor_dict_sorted)
    return floor_dict_sorted

def update_shearwall_data(shear_wall_objects, coord_dict_floor):
    data_to_change = {}
    for sw_obj in shear_wall_objects:
        floors_in_view = []
        for floor_id in coord_dict_floor:
            if sw_obj.bottom_view_elevation > coord_dict_floor[floor_id]['elevation_at_top']:
                continue
            if sw_obj.top_view_elevation < coord_dict_floor[floor_id]['elevation_at_top']:
                break
            floors_in_view.append(coord_dict_floor[floor_id])

        bot_data = assign_bottom_floor(sw_obj, sw_obj.start, sw_obj.end, sw_obj.base_level_elevation, floors_in_view)
        top_data = assign_top_floor(sw_obj, sw_obj.start, sw_obj.end, sw_obj.base_elevation, coord_dict_floor)

        data_to_change[sw_obj.id] = Merge(top_data, bot_data)

    return data_to_change


def assign_bottom_floor(sw_obj, sw_start, sw_end, lvl_base_elevation, floors_in_view):
    data_to_change = None
    if len(floors_in_view) == 0:
        print('Could not find base floor, No floors present in shearwall view')
    elif len(floors_in_view) == 1:
        sw_obj.base_offset = floors_in_view[0]['elevation_at_top'] - lvl_base_elevation
        sw_obj.get_base_elevation()
        data_to_change = {
            'baseOffset' : floors_in_view[0]['elevation_at_top'] - lvl_base_elevation
        }
    else:
        floors_containing_sw = []
        for floor in floors_in_view:
            p0_in_poly = point_in_poly(sw_start, (floor['polygon'],), 1)
            p1_in_poly = point_in_poly(sw_end, (floor['polygon'],), 1)
            if p0_in_poly[0] != 0 and p1_in_poly[0] != 0:
                floors_containing_sw.append(floor)
        if len(floors_containing_sw) == 0:
            print(f'Shear wall is not inside floor, {sw_obj.id}')
        elif len(floors_containing_sw) == 1:
            sw_obj.base_offset = floors_containing_sw[0]['elevation_at_top'] - lvl_base_elevation
            sw_obj.get_base_elevation()
            data_to_change = {
                'baseOffset' : floors_containing_sw[0]['elevation_at_top'] - lvl_base_elevation
            }
        else:
            print('Shearwall line is contained within multiple floors in the same view')
    return data_to_change

def assign_top_floor(sw_obj, sw_start, sw_end, sw_base_elevation, floors):
    data_to_change = {
        'topLevel' : None,
        'topOffset' : None,
        'topFloorId' : None,
    }
    for floor_id in floors:
        if floors[floor_id]['elevation_at_top'] <= sw_base_elevation:
            continue
        p0_in_poly = point_in_poly(sw_start, (floors[floor_id]['polygon'],), 1)
        p1_in_poly = point_in_poly(sw_end, (floors[floor_id]['polygon'],), 1)
        if p0_in_poly[0] != 0 and p1_in_poly[0] != 0:
            sw_obj.top_level_elevation = floors[floor_id]['level']['elevation']
            sw_obj.top_offset = floors[floor_id]['elevation_at_top'] - floors[floor_id]['level']['elevation']
            sw_obj.get_top_elevation()
            data_to_change = {
                'topLevel' : floors[floor_id]['level'],
                'topOffset' : floors[floor_id]['elevation_at_top'] - floors[floor_id]['level']['elevation'],
                'topFloorId' : floor_id,
            }
            break

    return data_to_change

def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def get_stacked_walls(shear_wall_objects):
    sw_objects_at_level = {}
    stacked_walls = {}

    shear_wall_objects.sort(key=lambda x: x.base_elevation)

    for sw_obj in shear_wall_objects:
        if not sw_obj.base_elevation in sw_objects_at_level.keys():
            sw_objects_at_level[sw_obj.base_elevation] = {}
        sw_objects_at_level[sw_obj.base_elevation] = Merge(sw_objects_at_level[sw_obj.base_elevation], {sw_obj.id : sw_obj})

    # print('\n\n\nKEYS\n\n\n', sw_objects_at_level.keys(), sw_objects_at_level)

    for sw_obj in shear_wall_objects:
        # sws with no floor above will be skipped for now
        if not hasattr(sw_obj, 'top_elevation'):
            continue

        # no shear walls above this wall
        if not sw_obj.top_elevation in sw_objects_at_level.keys():
            break
        for upper_sw_obj_id, upper_sw_obj in sw_objects_at_level[sw_obj.top_elevation].items():

            if walls_stack(sw_obj.start, sw_obj.end, upper_sw_obj.start, upper_sw_obj.end):
                # assign wall stack id to upper wall
                if hasattr(sw_obj, 'wall_stack_id'):
                    wall_stack_id = sw_obj['wall_stack_id']
                else:
                    wall_stack_id = f'SSW{sw_obj.id}'
                    stacked_walls[wall_stack_id] = StackedShearWall(wall_stack_id)
                    stacked_walls[wall_stack_id].add_shear_wall(sw_obj)
                upper_sw_obj.wall_stack_id = wall_stack_id
                stacked_walls[wall_stack_id].add_shear_wall(upper_sw_obj)

                # remove sw from sw_at_level bc it has already been assigned
                del sw_objects_at_level[sw_obj.top_elevation][upper_sw_obj_id]
                break

    print('STACKED WALLS', stacked_walls)
    print('sw_at_level', sw_objects_at_level)
    return stacked_walls

def walls_stack(w1start, w1end, w2start, w2end):
    # only supports vertical or horizontal walls
    if abs(w1start[0] - w1end[0]) < 1e-1:
        w1_is_vert = True
    elif abs(w1start[1] - w1end[1]) < 1e-1:
        w1_is_vert = False
    else:
        print('diagonal walls are not yet implemented')
        return False

    if abs(w2start[0] - w2end[0]) < 1e-1:
        w2_is_vert = True
    elif abs(w2start[1] - w2end[1]) < 1e-1:
        w2_is_vert = False
    else:
        print('diagonal walls are not yet implemented')
        return False

    if w1_is_vert != w2_is_vert:
        return False
    elif w1_is_vert:
        if not abs(w1start[0] - w2start[0]) < 1e-1:
            return False
        return lines_overlap([w1start[1],w1end[1]],[w2start[1],w2end[1]])
    elif not w1_is_vert:
        if not abs(w1start[1] - w2start[1]) < 1e-1:
            return False
        return lines_overlap([w1start[0],w1end[0]],[w2start[0],w2end[0]])