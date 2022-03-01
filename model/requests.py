from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .models import *
import pygmsh
import json

@csrf_exempt
def get_floor_mesh(request):
    if request.is_ajax and request.method == "POST":
        # get the floor coord_list from the client side.
        coord_list_floor = json.loads(request.POST.get('coord_list_floor'))
        coord_list_walls = request.POST.get('coord_list_walls')
        print(coord_list_floor, coord_list_walls)

        # This will be a huge job, but eventually I need to combine my Django and speckle servers
        # then I wouldn't be passing the floor coord_list_floor into this function,
        # I would just query those from the database

        # Must run django without multithreading in order to do this (python manage.py runserver --nothreading --noreload). Who knows how we'll handle this in deployment
        polygon = []
        with pygmsh.geo.Geometry() as geom:
            for coord in coord_list_floor:
                polygon.append([coord['x'], coord['y']])
            geom.add_polygon(polygon, mesh_size=1)
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
        mesh.write('test1.vtk')

        return JsonResponse({'success?': 'yes'}, status = 200)
    return JsonResponse({}, status = 400)
