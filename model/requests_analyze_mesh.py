from asyncio import transports
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .sfepy_pb_description.linear_elastic import *
from .sfepy_pb_description.connectToSpeckle import get_object, get_client, get_transport

@csrf_exempt
def analyze_mesh(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        FLOOR_ID = request.POST.get('FLOOR_ID')
        
        client = get_client(HOST=HOST, STREAM_ID=STREAM_ID)
        transport = get_transport(client, STREAM_ID)
        floor_obj = get_object(transport, FLOOR_ID)

        options = {
                'mesh_points' : floor_obj.speckMesh.points,
                'minus_x_wind_load_point_ids' : floor_obj.speckMesh.minus_x_wind_load_point_ids,
                'plus_x_wind_load_point_ids': floor_obj.speckMesh.plus_x_wind_load_point_ids,
                'minus_y_wind_load_point_ids' : floor_obj.speckMesh.minus_y_wind_load_point_ids,
                'plus_y_wind_load_point_ids' : floor_obj.speckMesh.plus_y_wind_load_point_ids,
                'vert_shear_walls' : floor_obj.speckMesh.vert_shear_walls.copy(),
                'horiz_shear_walls' : floor_obj.speckMesh.horiz_shear_walls.copy(),
                'fixed_nodes': False,
            }

        pb, state = get_sfepy_pb(**options)
        create_mesh_reactions(pb)

        shear_wall_data = {}

        return JsonResponse({'shear_wall_data': shear_wall_data}, status = 200)
    return JsonResponse({}, status = 400)