from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
import pygmsh
import numpy as np
import json
import math

from sympy import re

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
        
        coord_dict_walls = query_shearwalls(client, STREAM_ID, OBJECT_ID, 1)
        coord_dict_floor = query_floors(client, STREAM_ID, OBJECT_ID, 1)

        # floors_sorted = sorted(coord_dict_floor.items(), key=lambda x: coord_dict_floor[x]['elevation_at_top'])

        # floors_sorted = {}
        # for id in sorted(coord_dict_floor, key=lambda x: coord_dict_floor[x]['elevation_at_top']):
        #     floors_sorted[id] = coord_dict_floor[id]

        # print(floors_sorted)

        stacked_walls = []
        data_to_change = update_shearwall_data(coord_dict_walls=coord_dict_walls, coord_dict_floor=coord_dict_floor)
        
        stacked_walls = get_stacked_walls()

        return JsonResponse({'data_to_change': data_to_change}, status = 200)
    return JsonResponse({}, status = 400)

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

def update_shearwall_data(coord_dict_walls, coord_dict_floor):
    data_to_change = {}
    for sw_id in coord_dict_walls:
        floors_in_view = []
        for floor_id in coord_dict_floor:
            if coord_dict_walls[sw_id][6] > coord_dict_floor[floor_id]['elevation_at_top']:
                continue
            if coord_dict_walls[sw_id][5] < coord_dict_floor[floor_id]['elevation_at_top']:
                break
            floors_in_view.append(coord_dict_floor[floor_id])

        bot_data = assign_bottom_floor(sw_id, (coord_dict_walls[sw_id][0], coord_dict_walls[sw_id][1]), \
            (coord_dict_walls[sw_id][2], coord_dict_walls[sw_id][3]), coord_dict_walls[sw_id][4], floors_in_view)

        top_data = assign_top_floor(sw_id,(coord_dict_walls[sw_id][0], coord_dict_walls[sw_id][1]), \
            (coord_dict_walls[sw_id][2], coord_dict_walls[sw_id][3]), coord_dict_walls[sw_id][4]+bot_data['baseOffset'], coord_dict_floor)

        data_to_change[sw_id] = Merge(top_data, bot_data)
    return data_to_change


def assign_bottom_floor(sw_id, sw_start, sw_end, lvl_base_elevation, floors_in_view):
    data_to_change = None
    if len(floors_in_view) == 0:
        print('Could not find base floor, No floors present in shearwall view')
    elif len(floors_in_view) == 1:
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
            print(f'Shear wall is not inside floor, {sw_id}')
        elif len(floors_containing_sw) == 1:
            data_to_change = {
                'baseOffset' : floors_containing_sw[0]['elevation_at_top'] - lvl_base_elevation
            }
        else:
            print('Shearwall line is contained within multiple floors in the same view')
    return data_to_change

def assign_top_floor(sw_id, sw_start, sw_end, sw_base_elevation, floors):
    data_to_change = {
        'topLevel' : None,
        'topOffset' : None,
    }
    for floor_id in floors:
        if floors[floor_id]['elevation_at_top'] <= sw_base_elevation:
            continue
        p0_in_poly = point_in_poly(sw_start, (floors[floor_id]['polygon'],), 1)
        p1_in_poly = point_in_poly(sw_end, (floors[floor_id]['polygon'],), 1)
        if p0_in_poly[0] != 0 and p1_in_poly[0] != 0:
            data_to_change = {
                'topLevel' : floors[floor_id]['level'],
                'topOffset' : floors[floor_id]['elevation_at_top'] - floors[floor_id]['level']['elevation'],
            }
            break

    return data_to_change

def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def walls_stack(w1x1, w1y1, w1x2, w1y2, w2x1, w2y1, w2x2, w2y2):
    # only supports vertical or horizontal walls
    if abs(w1x1 - w1x2) < 1e-1:
        w1_is_vert = True
    elif abs(w1y1 - w1y2) < 1e-1:
        w1_is_vert = False
    else:
        print('diagonal walls are not yet implemented')
        return False

    if abs(w2x1 - w2x2) < 1e-1:
        w2_is_vert = True
    elif abs(w2y1 - w2y2) < 1e-1:
        w2_is_vert = False
    else:
        print('diagonal walls are not yet implemented')
        return False

    if w1_is_vert != w2_is_vert:
        return False
    elif w1_is_vert:
        return lines_overlap([w1y1,w1y2],[w2y1,w2y2])
    elif not w1_is_vert:
        return lines_overlap([w1x1,w1x2],[w2x1,w2x2])