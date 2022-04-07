from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from sfepy.discrete.fem.meshio import MeshioLibIO
from .sfepy_pb_description.linear_elastic import *
from .sfepy_pb_description.connectToSpeckle import edit_data_in_obj, get_globals_obj, get_object, get_client, get_transport, send_to_speckle
from dotmap import DotMap
import meshio

@csrf_exempt
def analyze_mesh(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        FLOOR_ID = request.POST.get('FLOOR_ID')
        WIND_DIR = request.POST.get('WIND_DIR')
        FIXED_NODES = convert_bool(request.POST.get('FIXED_NODES'))
        
        client = get_client(HOST=HOST)
        transport = get_transport(client, STREAM_ID)

        globals_obj = get_globals_obj(client, transport, STREAM_ID)
        floor_obj = DotMap(globals_obj[FLOOR_ID])
        # floor_obj = get_object(transport, FLOOR_ID)

        options = {
            'mesh_points' : floor_obj.speckMesh.points,
            'minus_x_wind_load_point_ids' : floor_obj.speckMesh.minus_x_wind_load_point_ids,
            'plus_x_wind_load_point_ids': floor_obj.speckMesh.plus_x_wind_load_point_ids,
            'minus_y_wind_load_point_ids' : floor_obj.speckMesh.minus_y_wind_load_point_ids,
            'plus_y_wind_load_point_ids' : floor_obj.speckMesh.plus_y_wind_load_point_ids,
            'vert_shear_walls' : floor_obj.speckMesh.vert_shear_walls.copy(),
            'horiz_shear_walls' : floor_obj.speckMesh.horiz_shear_walls.copy(),
            'fixed_nodes': FIXED_NODES,
            'wind_dir' : WIND_DIR,
        }

        # shear_wall_data = {}
        applied_loads = create_mesh_applied_loads(**options)
        pb, state = get_sfepy_pb(**options)

        reactions, displacements, shear_wall_data = create_mesh_reactions(pb, state, FIXED_NODES)

        floor_obj.speckMesh.cell_data['applied_loads'] = applied_loads.tolist()
        floor_obj.speckMesh.cell_data['displacements'] = displacements.tolist()
        floor_obj.speckMesh.cell_data['reactions'] = reactions.tolist()

        mesh = MeshioLibIO('mesh_reactions.vtk')
        # coors = io.read(Mesh()).coors[:, 0, None]
        data = mesh.read_data(step=0)
        print(mesh)
        print(data['u'].data, type(data['u'].data))

        mio = meshio.read('mesh_reactions.vtk')
        print(mio.points)
        print(mio.cells)
        print(mio.point_data)
        print(mio.cell_data)
        # print(mio.field_data)
        # print(mio.point_sets)
        # print(mio.cell_sets)

        # shear_wall_data = get_reactions_in_region(pb, state, [row[-1] for row in floor_obj.speckMesh.vert_shear_walls] + \
        #     [row[-1] for row in floor_obj.speckMesh.horiz_shear_walls], options['fixed_nodes'])
        # print('SHEAR WALL DATA', shear_wall_data)
        # edit_data_in_obj(globals_obj, shear_wall_data.copy())
        send_to_speckle(client, transport, STREAM_ID, obj=floor_obj.speckMesh, branch_name='results', commit_message='shearwall analysis results')

        return JsonResponse({'shear_wall_data': shear_wall_data}, status = 200)
    return JsonResponse({}, status = 400)

def convert_bool(bool):
    if bool.lower() == 'false':
        return False
    elif bool.lower() == 'true':
        return True