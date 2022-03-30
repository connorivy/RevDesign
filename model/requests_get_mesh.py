from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from .models import *
import pygmsh
import numpy as np
import json
import math

from .sfepy_pb_description.SpeckMesh import SpeckMesh
from .sfepy_pb_description.connectToSpeckle import edit_data_in_obj, get_client, get_globals_obj, get_latest_commit, get_transport, get_object, send_to_speckle

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base
from gql.gql import gql


@csrf_exempt
def get_floor_mesh(request):
    if request.is_ajax and request.method == "POST":
        HOST = request.POST.get('HOST')
        STREAM_ID = request.POST.get('STREAM_ID')
        OBJECT_ID = request.POST.get('OBJECT_ID')
        FLOOR_ID = request.POST.get('FLOOR_ID')

        # create and authenticate a client
        client = get_client(HOST)

        # create an authenticated server transport from the client
        transport = ServerTransport(STREAM_ID, client)

        floor_obj = get_object(transport, FLOOR_ID)
        coord_list_floor = get_coords_list(floor_obj=floor_obj, num_decimals=1)
        coord_dict_walls = query_shearwalls(client, STREAM_ID, OBJECT_ID, num_decimals = 1)
        coord_list_floor = add_coords_for_shear_walls(coord_dict_walls, coord_list_floor)

        print(coord_list_floor)

        mesh_size = 5
        # print('NEW_COORD_LIST', coord_list_floor)

        # print('NEW_DICT_WALLS', coord_dict_walls)

        # get the floor coord_list from the client side.
        # coord_list_floor = json.loads(request.POST.get('coord_list_floor'))
        # coord_dict_walls = json.loads(request.POST.get('coord_dict_walls'))
        # print(coord_list_floor, coord_list_walls, request.POST)

        # This will be a huge job, but eventually I need to combine my Django and speckle servers
        # then I wouldn't be passing the floor coord_list_floor into this function,
        # I would just query those from the database

        mesh, wlc, vert_shear_walls, horiz_shear_walls = generate_mesh_for_user(coord_list_floor, coord_dict_walls, mesh_size)

        # get rid of edges and 'vertex' cells (whatever that is) so the mesh can be read as vtk
        mesh.remove_orphaned_nodes()
        mesh.remove_lower_dimensional_cells()

        print(mesh.points.tolist())
        for x in mesh.cells:
            print(x, x[0])
            if x[0] == 'triangle':
                for y in x[1]:
                    print(y)

        mesh.write('.\\model\\sfepy_pb_description\\RevDesign.vtk')
        mesh.write('.\\model\\sfepy_pb_description\\RevDesign.mesh')

        options = {
            'minus_x_wind_load_point_ids' : wlc['minus_x_wind_load_point_ids'],
            'plus_x_wind_load_point_ids': wlc['plus_x_wind_load_point_ids'],
            'minus_y_wind_load_point_ids' : wlc['minus_y_wind_load_point_ids'],
            'plus_y_wind_load_point_ids' : wlc['plus_y_wind_load_point_ids'],
            'vert_shear_walls' : vert_shear_walls.copy(),
            'horiz_shear_walls' : horiz_shear_walls.copy(),
            'fixed_nodes': False,
        }

        speckMesh = SpeckMesh(
            mesh.points.tolist(), 
            mesh.cells, 
            mesh.point_data,
            mesh.cell_data, 
            mesh.field_data,
            mesh.point_sets,
            mesh.cell_sets,
            mesh.gmsh_periodic,
            mesh.info,
            **options
        )

        data_to_edit = {
            FLOOR_ID: {
                'speckMesh' : speckMesh
            }
        }

        # committing the data to edit to globals and then committing to that to the stream is sort of a band aid fix to the fact that objects ids
        # are changed when I push those (unchanged) objects to speckle (specifically the id values change in floor_obj.speckMesh.vert_shear_walls)
        # https://speckle.community/t/specklepy-storing-unchanged-objects-multiple-times/2533

        # this is the code I would use if the issue was fixed
        # latest_commit = get_latest_commit(client, STREAM_ID)
        # latest_commit_obj = get_object(transport, latest_commit.referencedObject)
        # edit_data_in_obj(latest_commit_obj, data_to_replace)
        # send_to_speckle(client, transport, STREAM_ID, latest_commit_obj, commit_message='Edit speckMesh for floor')

        globals_obj = get_globals_obj(client, transport, STREAM_ID)
        edit_data_in_obj(globals_obj, data_to_edit)
        send_to_speckle(client, transport, STREAM_ID, globals_obj, branch_name='globals', commit_message='Edit speckMesh for floor')

        return JsonResponse({'success': 'yee'}, status = 200)
    return JsonResponse({}, status = 400)

def generate_mesh_for_user(coord_list_floor, coord_dict_walls, mesh_size):
    # Must run django without multithreading in order to do this (python manage.py runserver --nothreading --noreload). Who knows how we'll handle this in deployment
    vert_shear_walls = []
    horiz_shear_walls = []
    boundary_layers = []
    with pygmsh.geo.Geometry() as geom:
        # add lines from floor
        # for coord in coord_list_floor:
        #     # round to nearest 6 decimal places bc revit is only accurate to 5 (I think?)
        #     polygon.append([coord[0], coord[1]])

        surface = geom.add_polygon(coord_list_floor, mesh_size=mesh_size)
        # boundary_layers.append(geom.add_boundary_layer(
        #         edges_list = surface.curves,
        #         lcmin = mesh_size / 5,
        #         lcmax = mesh_size / .8,
        #         distmin = .3,
        #         distmax = mesh_size / 1
        #     ))

        # https://github.com/nschloe/pygmsh/issues/537 
        # https://github.com/nschloe/meshio/issues/550
        # someday maybe I can label the groups as I create them to be more efficient
        # geom.add_physical(surface, label='surface')
        # add points from shear walls
        # for index in range(len(coord_list_walls)):
        for wall_id in coord_dict_walls:
            p0 = None
            p1 = None
            x0 = coord_dict_walls[wall_id][0]
            y0 = coord_dict_walls[wall_id][1]
            x1 = coord_dict_walls[wall_id][2]
            y1 = coord_dict_walls[wall_id][3]

            # create lists of shear wall objects 
            if abs(x1 - x0) < 1e-4:
                vert_shear_walls.append([x0,y0,x1,y1,wall_id])
            elif abs(y1-y0) < 1e-4:
                horiz_shear_walls.append([x0,y0,x1,y1,wall_id])

            # maybe make this loop a little more clever
            for point in surface.points:
                if is_equal_2d_list([point.x[0], point.x[1]], [x0, y0], tol = 1e-4):
                    p0 = point
                    if p0 and p1:
                        break

                elif is_equal_2d_list([point.x[0], point.x[1]], [x1, y1], tol = 1e-4):
                    p1 = point
                    if p0 and p1:
                        break

            # if both points are already defined, there is already a line between them so move on to the next wall
            if p0 and p1:
                for edge_line in surface.lines:
                    if p0._id in [edge_line.points[0]._id, edge_line.points[1]._id] and p1._id in [edge_line.points[0]._id, edge_line.points[1]._id]:
                        line = edge_line
                        print('LINE', edge_line)
            else:    
                if not p0:
                    p0 = geom.add_point([x0, y0])
                if not p1:
                    p1 = geom.add_point([x1, y1])
                line = geom.add_line(p0, p1)

                # embed new line in surface
                geom.in_surface(line,surface)

            boundary_layers.append(geom.add_boundary_layer(
                edges_list = [line],
                lcmin = mesh_size / 5,
                lcmax = mesh_size / 1,
                distmin = .1,
                distmax = mesh_size / 1
            ))
            # geom.add_physical(line, label=f'SW{wall_id}')

        wlc = get_wind_load_point_ids(coord_list_floor, surface)
        geom.set_background_mesh(boundary_layers, operator="Min")
        mesh = geom.generate_mesh()

    return mesh, wlc, vert_shear_walls, horiz_shear_walls

def get_wind_load_point_ids(polygon, surface):
    np_poly = np.asarray(polygon)

    # sort surves in acending order by the avarage x and y values or the curves
    # only works for lines at the moment, not curves
    curves_sorted_by_x = sorted(surface.curves, key=lambda x: (x.points[0].x[0] + x.points[1].x[0]) / 2, reverse=False)
    curves_sorted_by_y = sorted(surface.curves, key=lambda x: (x.points[0].x[1] + x.points[1].x[1]) / 2, reverse=False)

    max_x, max_y = np_poly.max(axis=0)
    min_x, min_y = np_poly.min(axis=0)

    wind_line_vert = [[min_y, max_y]]
    wind_line_horiz = [[min_x, max_x]]

    wlc = {}
    wlc['minus_x_wind_load_point_ids'] = get_point_ids_from_wind_line(curves_sorted_by_x, wind_line_vert.copy(), 1)
    wlc['plus_x_wind_load_point_ids'] = get_point_ids_from_wind_line(reversed(curves_sorted_by_x), wind_line_vert.copy(), 1)
    wlc['minus_y_wind_load_point_ids'] = get_point_ids_from_wind_line(curves_sorted_by_y, wind_line_horiz.copy(), 0)
    wlc['plus_y_wind_load_point_ids'] = get_point_ids_from_wind_line(reversed(curves_sorted_by_y), wind_line_horiz.copy(), 0)

    return wlc

def get_point_ids_from_wind_line(curves_sorted, wind_line, dir):
    '''
    dir = 0 if dealing with the horizontal direction, 1 if dealing with the vertical direction
    '''
    curves = []
    point_ids = []
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

    for curve in curves:
        point_ids.append([curve.points[0]._id, curve.points[1]._id])

    return point_ids

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

def lines_overlap(segment, curve, dir):
    # print('lines overlap', wind_line, curve, dir)
    if max(segment) <= min(curve.points[0].x[dir], curve.points[1].x[dir]) or min(segment) >= max(curve.points[0].x[dir], curve.points[1].x[dir]):
        # print('lines overlap', 'False')
        return False
    else:
        # print('lines overlap', 'True')
        return True

def adjust_wind_line(wind_line, segment, curve, dir):
    '''
    wind line = [[min_value, max_value]]
    segment = [min_value, max_value]
    curve = pygmsh curve object
    '''
    min_segment = min(segment)
    max_segment = max(segment)
    min_curve = min(curve.points[0].x[dir], curve.points[1].x[dir])
    max_curve = max(curve.points[0].x[dir], curve.points[1].x[dir])

    #           --------------                curve
    #     -----------------------------       segment
    if min_segment < min_curve and max_segment > max_curve:
        wind_line.append([min_segment, min_curve])
        wind_line.append([max_curve, max_segment])

    # --------------                          curve
    #        -----------------------------    segment
    elif min_segment >= min_curve and max_segment > max_curve:
        wind_line.append([max_curve, max_segment])

    #                       --------------    curve
    # -----------------------------           segment
    elif min_segment < min_curve and max_segment <= max_curve:
        wind_line.append([min_segment, min_curve])

    #         --------------                  curve
    #            -------                      segment
    else:
        pass

    wind_line.remove(segment)
    return wind_line

def is_equal_2d_list(p1, p2, tol=3.33e-1):
    if abs(p2[0] - p1[0]) < tol and abs(p2[1] - p1[1]) < tol:
        return True
    else:
        return False

def get_coords_list(floor_obj, num_decimals):
    coords = []
    seen_coords = set()
    for segment in floor_obj.outline.segments:
        x0 = round(segment.start.x, num_decimals)
        y0 = round(segment.start.y, num_decimals)
        x1 = round(segment.end.x, num_decimals)
        y1 = round(segment.end.y, num_decimals)
        if (x0, y0) not in seen_coords:
            seen_coords.add((x0, y0))
            coords.append((x0, y0))
        if (x1, y1) not in seen_coords:
            seen_coords.add((x1, y1))
            coords.append((x1, y1))

    if len(coords) != len(floor_obj.outline.segments):
        print('WARNING: # of coords != # 0f segments')

    return coords

def add_coords_for_shear_walls(coord_dict_walls, coord_list_floor):
    # we have to 'close' the polygon for the function to work
    coord_list_floor.append(coord_list_floor[0])

    for wall_id in coord_dict_walls:
        x0 = coord_dict_walls[wall_id][0]
        y0 = coord_dict_walls[wall_id][1]
        x1 = coord_dict_walls[wall_id][2]
        y1 = coord_dict_walls[wall_id][3]

        if distance_formula((x0, y0), (x1, y1)) < 1:
            print('short wall')
            tol = 4.16e-2
            num_decimals = 1
        else:
            tol = 3.33e-1
            num_decimals = 1

        p0inPoly = point_in_poly((x0, y0), (coord_list_floor,), num_decimals)
        p1inPoly = point_in_poly((x1, y1), (coord_list_floor,), num_decimals)
        # print((x0, y0), (x1, y1))
        # print('pinpoly', p0inPoly, p1inPoly)

        # one or both of the points is outside the slab, don't count it.
        if p0inPoly[0] == 0 or p1inPoly[0] == 0:
            print('outside slab')
            continue
        # both points are inside the slab, yay
        if p0inPoly[0] == 1 and p1inPoly[0] == 1:
            print('inside slab')
        # both points are on the border of the polygon
        elif p0inPoly[0] == 2 and p1inPoly[0] == 2:
            print('on perim')
            print(f'comparing {coord_list_floor[p0inPoly[1]]} and {coord_list_floor[p0inPoly[1]+1]} to {(x0, y0)}')
            print(f'comparing {coord_list_floor[p1inPoly[1]]} and {coord_list_floor[p1inPoly[1]+1]} to {(x1, y1)}')
            print('len of wall', distance_formula((x0, y0), (x1, y1)))

            p0IsCorner = is_equal_2d_list(coord_list_floor[p0inPoly[1]],(x0, y0), tol) or is_equal_2d_list(coord_list_floor[p0inPoly[1]+1],(x0, y0), tol)
            p1IsCorner = is_equal_2d_list(coord_list_floor[p1inPoly[1]],(x1, y1), tol) or is_equal_2d_list(coord_list_floor[p1inPoly[1]+1],(x1, y1), tol)

            # if both are corners, just add to coord array walls
            if p0IsCorner and p1IsCorner:
                print('both corners')
            elif p0IsCorner:
                print('p0 is corner')
                coord_list_floor.insert(p1inPoly[1]+1, (x1, y1))
            elif p1IsCorner:
                print('p1 is corner')
                coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
            # neither point is on a corner
            else:
                print('no corners')
                # find the point that has the largest index in the list, insert there, and then insert the new point into the smaller index
                if p0inPoly[1] > p1inPoly[1]:
                    coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
                    coord_list_floor.insert(p1inPoly[1]+1, (x1, y1))
                elif p0inPoly[1] < p1inPoly[1]:
                    coord_list_floor.insert(p1inPoly[1]+1, (x1, y1))
                    coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
                # if the indicies are the same, then the points are on the same line. Find the one furthest away from the corner point and insert that right after the point,
                # then insert the closer point right after the corner point in the coodArrayFloor
                else:
                    distOfP0 = distance_formula((x0, y0), coord_list_floor[p0inPoly[1]])
                    distOfP1 = distance_formula((x1, y1), coord_list_floor[p0inPoly[1]])
                    # if p0 is closer, insert p1 then p0
                    if distOfP0 < distOfP1:
                        coord_list_floor.insert(p0inPoly[1]+1, (x1, y1))
                        coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
                    else:
                        coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
                        coord_list_floor.insert(p0inPoly[1]+1, (x1, y1))
        elif p0inPoly[0] == 2:
            #   print('p0 on perim')
            coord_list_floor.insert(p0inPoly[1]+1, (x0, y0))
        elif p1inPoly[0] == 2:
            #   print('p1 on perim')
            coord_list_floor.insert(p1inPoly[1]+1, (x1, y1))

    # remove the last item of the coord_list because pygmsh likes 'open' polygons
    coord_list_floor.pop()

    return coord_list_floor

def query_shearwalls(client, STREAM_ID, OBJECT_ID, num_decimals):
    query = gql(
        """
            query($myQuery:[JSONObject!], $stream_id: String!, $object_id: String!){
                stream(id:$stream_id){
                    object(id:$object_id){
                        children(query: $myQuery select:["start.x","start.y","start.z","end.x","end.y","end.z"]){
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
    print(dict_from_server)
    coord_dict_walls = {}
    for wall in dict_from_server['stream']['object']['children']['objects']:
        coord_dict_walls[wall['id']] = (
            round(wall['data']['start']['x'], num_decimals),
            round(wall['data']['start']['y'], num_decimals),
            round(wall['data']['end']['x'], num_decimals),
            round(wall['data']['end']['y'], num_decimals), 
        )
    
    print('coord_dict_walls', coord_dict_walls)
    return coord_dict_walls


# https:#github.com/sasamil/PointInPolygon_Py/blob/master/pointInside.py
# arguments:
# Polygon - searched polygon
# Point - an arbitrary point that can be inside or outside the polygon
# length - the number of point in polygon (Attention! The list itself has an additional member - the last point coincides with the first)

# return value:
# 0 - the point is outside the polygon
# 1 - the point is inside the polygon 
# 2 - the point is one edge (boundary)

# def is_inside_sm(polygon, point):
#   length = len(polygon)-1
#   dy2 = point[1] - polygon[0][1]
#   intersections = 0
#   ii = 0
#   jj = 1

#   while ii<length:
#     dy  = dy2
#     dy2 = point[1] - polygon[jj][1]

#     # consider only lines which are not completely above/bellow/right from the point
#     if dy*dy2 <= 0.0 and (point[0] >= polygon[ii][0] or point[0] >= polygon[jj][0]):
        
#       # non-horizontal line
#       if dy<0 or dy2<0:
#         F = dy*(polygon[jj][0] - polygon[ii][0])/(dy-dy2) + polygon[ii][0]

#         if point[0] > F: # if line is left from the point - the ray moving towards left, will intersect it
#           intersections += 1
#         elif point[0] == F: # point on line
#           return 2

#       # point on upper peak (dy2=dx2=0) or horizontal line (dy=dy2=0 and dx*dx2<=0)
#       elif dy2==0 and (point[0]==polygon[jj][0] or (dy==0 and (point[0]-polygon[ii][0])*(point[0]-polygon[jj][0])<=0)):
#         return 2

#       # there is another posibility: (dy=0 and dy2>0) or (dy>0 and dy2=0). It is skipped 
#       # deliberately to prevent break-points intersections to be counted twice.
    
#     ii = jj
#     jj += 1
            
#   #print 'intersections =', intersections
#   return intersections & 1 



# return value:
# 0 - the point is outside the polygon
# 1 - the point is inside the polygon 
# 2 - the point is on edge (boundary)
def point_in_poly(p, polygon, num_decimals=1):
    i = 0
    ii = 0
    k = 0
    f = 0
    u1 = 0
    v1 = 0
    u2 = 0
    v2 = 0

    x = round(p[0],num_decimals)
    y = round(p[1], num_decimals)

    numContours = len(polygon)
    for i in range(numContours):
        ii = 0
        contourLen = len(polygon[i]) - 1
        contour = polygon[i]

        currentP = contour[0]
        if currentP[0] != contour[contourLen][0] and currentP[1] != contour[contourLen][1]:
            print('First and last coordinates in a ring must be the same')

        u1 = round(currentP[0], num_decimals) - x
        v1 = round(currentP[1], num_decimals) - y

        for ii in range(contourLen):
            nextP = contour[ii + 1]

            v2 = round(nextP[1], num_decimals) - y

            if (v1 < 0 and v2 < 0) or (v1 > 0 and v2 > 0):
                currentP = nextP
                v1 = v2
                u1 = round(currentP[0], num_decimals) - x
                continue

            u2 = round(nextP[0], num_decimals) - x

            if v2 > 0 and v1 <= 0:
                f = (u1 * v2) - (u2 * v1)
                if f > 0:
                    k = k + 1
                elif f == 0:
                    return [2, ii]
            elif v1 > 0 and v2 <= 0:
                f = (u1 * v2) - (u2 * v1)
                if f < 0: 
                    k = k + 1
                elif f == 0:
                    return [2, ii]
            elif v2 == 0 and v1 < 0:
                f = (u1 * v2) - (u2 * v1)
                if f == 0:
                    return [2, ii]
            elif v1 == 0 and v2 < 0:
                f = u1 * v2 - u2 * v1
                if f == 0:
                    return [2, ii]
            elif v1 == 0 and v2 == 0:
                if u2 <= 0 and u1 >= 0:
                    return [2, ii]
                elif u1 <= 0 and u2 >= 0:
                    return [2, ii]

            currentP = nextP
            v1 = v2
            u1 = u2

    if k % 2 == 0:
        return [0, None]
    return [1, None]

def distance_formula(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)
