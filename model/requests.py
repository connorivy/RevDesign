from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .models import *
from .sfepy.linear_elastic import *
import pygmsh
import numpy as np
import json
import gmsh

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
        mesh_size = 15
        polygon = []
        vert_shear_walls = []
        horiz_shear_walls = []
        boundary_layers = []
        with pygmsh.geo.Geometry() as geom:
            # add lines from floor
            for coord in coord_list_floor:
                # round to nearest 6 decimal places bc revit is only accurate to 5 (I think?)
                polygon.append([round(coord['x'],6), round(coord['y'],6)])

            surface = geom.add_polygon(polygon, mesh_size=mesh_size)
            # boundary_layers.append(geom.add_boundary_layer(
            #         edges_list = surface.curves,
            #         lcmin = mesh_size / 10,
            #         lcmax = mesh_size / 1.2,
            #         distmin = 0,
            #         distmax = mesh_size / 1.4
            #     ))
            np_poly = np.asarray(polygon)

            # sort surves in acending order by the avarage x and y values or the curves
            # only works for lines at the moment, not curves
            curves_sorted_by_x = sorted(surface.curves, key=lambda x: (x.points[0].x[0] + x.points[1].x[0]) / 2, reverse=False)
            curves_sorted_by_y = sorted(surface.curves, key=lambda x: (x.points[0].x[1] + x.points[1].x[1]) / 2, reverse=False)

            max_x, max_y = np_poly.max(axis=0)
            min_x, min_y = np_poly.min(axis=0)

            wind_line_vert = [[min_y, max_y]]
            wind_line_horiz = [[min_x, max_x]]

            minus_x_wind_load_curves = get_curves_with_wind_load(curves_sorted_by_x, wind_line_vert.copy(), 1)
            plus_x_wind_load_curves = get_curves_with_wind_load(reversed(curves_sorted_by_x), wind_line_vert.copy(), 1)
            minus_y_wind_load_curves = get_curves_with_wind_load(curves_sorted_by_y, wind_line_horiz.copy(), 0)
            plus_y_wind_load_curves = get_curves_with_wind_load(reversed(curves_sorted_by_y), wind_line_horiz.copy(), 0)

            # https://github.com/nschloe/pygmsh/issues/537 
            # https://github.com/nschloe/meshio/issues/550
            # someday maybe I can label the groups as I create them to be more efficient
            # geom.add_physical(surface, label='surface')

            # add points from shear walls
            for index in range(len(coord_list_walls)):
                p0 = None
                p1 = None
                x0 = round(float(coord_list_walls[index][0]),6)
                y0 = round(float(coord_list_walls[index][1]),6)
                x1 = round(float(coord_list_walls[index][2]),6)
                y1 = round(float(coord_list_walls[index][3]),6)

                # maybe make this loop a little more clever
                for point in surface.points:
                    if is_equal_2d_list([point.x[0], point.x[1]], [x0, y0]):
                        p0 = point
                        if p0 and p1:
                            break

                    elif is_equal_2d_list([point.x[0], point.x[1]], [x1, y1]):
                        p1 = point
                        if p0 and p1:
                            break
                        
                if not p0:
                    p0 = geom.add_point([x0, y0])
                if not p1:
                    p1 = geom.add_point([x1, y1])
                line = geom.add_line(p0, p1)

                # embed new line in surface
                geom.in_surface(Cheating(line), Cheating(surface))

                # print(geom._EMBED_QUEUE)


                # boundary layer overriding points that I need to fix?
                # boundary_layers.append(geom.add_boundary_layer(
                #     edges_list = [line],
                #     lcmin = mesh_size / 10,
                #     lcmax = mesh_size / 1.2,
                #     distmin = mesh_size / 10,
                #     distmax = mesh_size / 1.4
                # ))
                # geom.add_physical(line, label=f'SW{index}')

                # create lists of shear wall objects 
                if abs(line.points[0].x[0] - line.points[1].x[0]) < 1e-5:
                    vert_shear_walls.append(line)
                else:
                    horiz_shear_walls.append(line)

            for item, host in geom._EMBED_QUEUE:
                print(item.dim, [item._id], host.dim, host._id)

            print('setting mesh')
            print(dir(geom.env))
            # geom.set_background_mesh(boundary_layers, operator="Min")
            mesh = geom.generate_mesh()
            print('done')

        # get rid of edges and 'vertex' cells (whatever that is) so the mesh can be read as vtk
        for index in range(len(mesh.cells)):
            try:
                print(mesh.cells[index].type)
                if mesh.cells[index].type == 'line':
                    mesh.cells.pop(index)
                elif mesh.cells[index].type == 'vertex':
                    mesh.cells.pop(index)
            except:
                break

        mesh.write('.\model\sfepy\RevDesign.vtk')
        mesh.write('.\model\sfepy\RevDesign.mesh')

        options = {
            'minus_x_wind_load_curves' : minus_x_wind_load_curves,
            'plus_x_wind_load_curves': plus_x_wind_load_curves,
            'minus_y_wind_load_curves' : minus_y_wind_load_curves,
            'plus_y_wind_load_curves' : plus_y_wind_load_curves,
            'vert_shear_walls' : vert_shear_walls,
            'horiz_shear_walls' : horiz_shear_walls,
        }

        print('vert_shear_walls', vert_shear_walls)

        # pb = get_sfepy_pb(**options)
        # create_mesh_reactions(pb)

        return JsonResponse({'success?': 'yes'}, status = 200)
    return JsonResponse({}, status = 400)

def get_curves_with_wind_load(curves_sorted, wind_line, dir):
    '''
    dir = 0 if dealing with the horizontal direction, 1 if dealing with the vertical direction
    '''
    curves = []
    for curve in curves_sorted:
        if not wind_line:
            break
        
        # only works with cardinal directions
        if is_nearly_perpendicular(curve, dir, .176): #.176 is the slope of a line a 10deg with the horizon
            continue
        for segment in wind_line:
            if lines_overlap(segment, curve, dir):
                curves.append(curve)
                wind_line = adjust_wind_line(wind_line, segment, curve, dir)
                break
    return curves

def is_nearly_perpendicular(curve, dir, tol):
    '''
    dir = 0 if dealing with the horizontal direction, 1 if dealing with the vertical direction
    '''

    # print('is_nearly_perpendicular', curve, dir)
    # if curve has the same x value, then line is vertical and slope equantion will fail
    if abs(curve.points[1].x[0] - curve.points[0].x[0]) < .001:
        # print('is_nearly_perpendicular', not dir)
        return not dir

    # if slope is close to zero, then its a horizontal line
    slope = abs((curve.points[1].x[1] - curve.points[0].x[1]) / (curve.points[1].x[0] - curve.points[0].x[0]))
    if slope < tol:
        # print('is_nearly_perpendicular', dir)
        return dir
    else:
        # print('is_nearly_perpendicular', not dir)
        return not dir

def lines_overlap(wind_line, curve, dir):
    # print('lines overlap', wind_line, curve, dir)
    if max(wind_line) < min(curve.points[0].x[dir], curve.points[1].x[dir]) or min(wind_line) > max(curve.points[0].x[dir], curve.points[1].x[dir]):
        # print('lines overlap', 'False')
        return False
    else:
        # print('lines overlap', 'True')
        return True

def adjust_wind_line(wind_line, segment, curve, dir):
    print('adjust_wind_line', wind_line, segment, curve, dir)
    min_segment = min(segment)
    max_segment = max(segment)
    min_curve = min(curve.points[0].x[dir], curve.points[1].x[dir])
    max_curve = max(curve.points[0].x[dir], curve.points[1].x[dir])

    #           --------------                curve
    #     -----------------------------       segment
    if min_segment < min_curve and max_segment > max_curve:
        wind_line.append([min_segment, min_curve])
        wind_line.append([max_segment, max_curve])

    # --------------                          curve
    #        -----------------------------    segment
    elif min_segment < min_curve and max_segment > max_curve:
        wind_line.append([max_segment, max_curve])

    #                       --------------    curve
    # -----------------------------           segment
    elif min_segment < min_curve and max_segment > max_curve:
        wind_line.append([min_curve, min_segment])

    #         --------------                  curve
    #            -------                      segment
    else:
        pass

    wind_line.remove(segment)
    print('adjust_wind_line', wind_line)
    return wind_line

def is_equal_2d_list(p1, p2):
    tol = 1e-5
    if abs(p2[0] - p1[0]) < tol and abs(p2[1] - p1[1]) < tol:
        return True
    else:
        return False

class Cheating():
    def __init__(self, entity) -> None:
        self.dim = entity.dim
        self._id = entity
