from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .models import *
from .sfepy.linear_elastic import *
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
        vert_shear_walls = []
        horiz_shear_walls = []
        with pygmsh.geo.Geometry() as geom:
            # add lines from floor
            for coord in coord_list_floor:
                # round to nearest 6 decimal places bc revit is only accurate to 5 (I think?)
                polygon.append([round(coord['x'],6), round(coord['y'],6)])

            boundary = geom.add_polygon(polygon, mesh_size=mesh_size)
            np_poly = np.asarray(polygon)
            np_curves = np.array(boundary.curves)

            plus_x = []
            minus_x = []
            plus_y = []
            minus_y = []

            max_x, max_y = np_poly.max(axis=0)
            min_x, min_y = np_poly.min(axis=0)

            


            # https://github.com/nschloe/pygmsh/issues/537 
            # https://github.com/nschloe/meshio/issues/550
            # someday maybe I can label the groups as I create them to be more efficient
            # geom.add_physical(boundary, label='boundary')

            # add points from shear walls
            boundary_layers = []
            for wall in coord_list_walls:
                p0 = None
                p1 = None
                x0 = round(float(wall[0]),6)
                y0 = round(float(wall[1]),6)
                x1 = round(float(wall[2]),6)
                y1 = round(float(wall[3]),6)

                # maybe make this loop a little more clever
                for point in boundary.points:
                    if [point.x[0], point.x[1]] == [x0, y0]:
                        p0 = point
                        if p0 and p1:
                            break

                    elif [point.x[0], point.x[1]] == [x1, y1]:
                        p1 = point
                        if p0 and p1:
                            break
                        
                if not p0:
                    p0 = geom.add_point([x0, y0])
                if not p1:
                    p1 = geom.add_point([x1, y1])
                line = geom.add_line(p0, p1)

                boundary_layers.append(geom.add_boundary_layer(
                    edges_list = [line],
                    lcmin = mesh_size / 10,
                    lcmax = mesh_size / 1.2,
                    distmin = 0,
                    distmax = mesh_size / 1.4
                ))
                # geom.add_physical(line, label='SW')

            # create lists of shear wall objects 
            print('LINE', line.points[0], line.points[1], line.points[0]._id)
            if abs(line.points[0].x[0] - line.points[1].x[0]) < 1e-5:
                vert_shear_walls.append(line)
            else:
                horiz_shear_walls.append(line)

            geom.set_background_mesh(boundary_layers, operator="Min")
            mesh = geom.generate_mesh()

        # print('cell_sets', mesh.cell_sets, mesh.cell_data)
        mesh.write('test1.vtu')

        # pb = get_sfepy_pb()
        # create_mesh_reactions(pb)

        return JsonResponse({'success?': 'yes'}, status = 200)
    return JsonResponse({}, status = 400)
