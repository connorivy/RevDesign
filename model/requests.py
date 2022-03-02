from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .models import *
import pygmsh
import numpy as np
import json

@csrf_exempt
def get_floor_mesh(request):
    if request.is_ajax and request.method == "POST":
        # get the floor coord_list from the client side.
        coord_list_floor = json.loads(request.POST.get('coord_list_floor'))
        coord_list_walls = json.loads(request.POST.get('coord_list_walls'))
        # print(coord_list_floor, coord_list_walls, request.POST)

        # This will be a huge job, but eventually I need to combine my Django and speckle servers
        # then I wouldn't be passing the floor coord_list_floor into this function,
        # I would just query those from the database

        # Must run django without multithreading in order to do this (python manage.py runserver --nothreading --noreload). Who knows how we'll handle this in deployment
        mesh_size = 1
        polygon = []
        with pygmsh.geo.Geometry() as geom:
            # add lines from floor
            for coord in coord_list_floor:
                polygon.append([coord['x'], coord['y']])
            geom.add_polygon(polygon, mesh_size=mesh_size)

            # add points from shear walls
            boundary_layers = []
            for wall in coord_list_walls:
                p0 = geom.add_point([float(wall[0]), float(wall[1])])
                p1 = geom.add_point([float(wall[2]), float(wall[3])])
                poly = geom.add_line(p0, p1)
                print('POLY', poly)
                boundary_layers.append(geom.add_boundary_layer(
                    edges_list = [poly],
                    lcmin = mesh_size / 10,
                    lcmax = mesh_size / 1.2,
                    distmin = mesh_size / 10,
                    distmax = mesh_size / 1.4
                ))
            # print('BLS', boundary_layers)
            geom.set_background_mesh(boundary_layers, operator="Min")
            mesh = geom.generate_mesh()

        # with pygmsh.geo.Geometry() as geom:
        #     geom.add_polygon(
        #         [
        #             [0.0, 0.0],
        #             [1.0, -0.2],
        #             [1.1, 1.2],
        #             [0.1, 0.7],
        #         ],
        #         mesh_size=0.1,
        #     )
        #     mesh = geom.generate_mesh()
        mesh.write('test1.mesh')

        return JsonResponse({'success?': 'yes'}, status = 200)
    return JsonResponse({}, status = 400)

def get_points_from_wall(wall, mesh_size=1):
    a = np.array([float(wall[0]), float(wall[1])])
    b = np.array([float(wall[2]), float(wall[3])])
    parts = np.ceil(np.linalg.norm(a-b) / mesh_size) + 1
    print(np.linspace(a,b,int(parts)).tolist())
    return np.linspace(a,b,int(parts)).tolist()

def get_poly_from_wall(wall, mesh_size=1):
    return pygmsh.common.Polygon([[float(wall[0]), float(wall[1])],[float(wall[2]), float(wall[3])]], mesh_size)
