from unittest import result
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from sfepy.discrete.fem.meshio import MeshioLibIO
from .sfepy_pb_description.linear_elastic import *
from .sfepy_pb_description.connectToSpeckle import edit_data_in_obj, get_globals_obj, get_object, get_client, get_transport, send_to_speckle, get_latest_commit_for_branch

@csrf_exempt
def analyze_mesh(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        WIND_DIR = request.POST.get('WIND_DIR')
        FIXED_NODES = convert_bool(request.POST.get('FIXED_NODES'))

        data_to_edit = {}
        
        client = get_client(HOST=HOST)
        transport = get_transport(client, STREAM_ID)

        # globals_obj = get_globals_obj(client, transport, STREAM_ID)
        latest_results_commit = get_latest_commit_for_branch(client, STREAM_ID, 'results')
        results = get_object(transport, latest_results_commit.referencedObject)
        for speckMesh in results['@SpeckMeshes']:
            options = {
                'mesh_points' : speckMesh.points,
                'mesh_cells' : speckMesh.cells,
                'mesh_cell_sets' : speckMesh.cell_sets,
                # 'mesh_cell_data' : speckMesh.cell_data,
                'minus_x_wind_load_point_ids' : speckMesh.minus_x_wind_load_point_ids,
                'plus_x_wind_load_point_ids': speckMesh.plus_x_wind_load_point_ids,
                'minus_y_wind_load_point_ids' : speckMesh.minus_y_wind_load_point_ids,
                'plus_y_wind_load_point_ids' : speckMesh.plus_y_wind_load_point_ids,
                'vert_shear_walls' : speckMesh.vert_shear_walls.copy(),
                'horiz_shear_walls' : speckMesh.horiz_shear_walls.copy(),
                'fixed_nodes': FIXED_NODES,
                'wind_dir' : WIND_DIR,
                'mesh_id' : speckMesh.id,
            }

            # shear_wall_data = {}
            applied_loads = create_mesh_applied_loads(**options)
            pb, state, displacements = get_sfepy_pb(**options)

            displacements_list = displacements.tolist()
            reactions, shear_wall_data = create_mesh_reactions(pb, displacements, FIXED_NODES, speckMesh.id)
            data_to_edit = Merge(data_to_edit, shear_wall_data)

            speckMesh.cell_data['applied_loads'] = applied_loads.tolist()
            speckMesh.cell_data['displacements'] = displacements_list
            speckMesh.cell_data['reactions'] = reactions.tolist()

        # shear_wall_data = get_reactions_in_region(pb, state, [row[-1] for row in floor_obj.speckMesh.vert_shear_walls] + \
        #     [row[-1] for row in floor_obj.speckMesh.horiz_shear_walls], options['fixed_nodes'])
        # print('SHEAR WALL DATA', shear_wall_data)
        # edit_data_in_obj(globals_obj, shear_wall_data.copy())
        obj_id = send_to_speckle(client, transport, STREAM_ID, obj=results, branch_name='results', commit_message='shearwall analysis results')

        return JsonResponse({'shear_wall_data': data_to_edit, 'obj_id': obj_id}, status = 200)
    return JsonResponse({}, status = 400)

def convert_bool(bool):
    if bool.lower() == 'false':
        return False
    elif bool.lower() == 'true':
        return True

def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res