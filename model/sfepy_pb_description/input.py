from fileinput import filename
import numpy as np
from sfepy.mechanics.matcoefs import stiffness_from_youngpoisson
import math
from sfepy.base.base import output
from sfepy.discrete.fem.meshio import UserMeshIO
from sfepy.discrete.fem.mesh import Mesh

import meshio

def is_equal(p1, p2):
    tol = 1e-2
    if abs(p2 - p1) < tol:
        return True
    else:
        return False

def is_equal_wind(p1, p2):
    tol = 5e-2
    if abs(p2 - p1) / min(p1,p2) < tol:
        return True
    else:
        return False

def vert_shear_walls(coors, domain, coords_2d_list):
    # there can only be one default value for a function, so pass in the whole list of curves and then remove them as they are used
    curve = coords_2d_list.pop(0)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        # for curve in point_ids_list:
            if is_equal(x[index],curve[0]) and y[index] <= max(curve[1], curve[3]) + 1e-5 and y[index] >= min(curve[1], curve[3]) - 1e-5:
                flag = np.append(flag, int(index))

    # print('\n\nVERT CURVE\n\n', coords_2d_list, curve, flag)

    return flag

def horiz_shear_walls(coors, domain, coords_2d_list):
    # there can only be one default value for a function, so pass in the whole list of curves and then remove them as they are used
    curve = coords_2d_list.pop(0)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        # for curve in point_ids_list:
            if is_equal(y[index],curve[1]) and x[index] <= max(curve[0], curve[2]) + 1e-5 and x[index] >= min(curve[0], curve[2]) - 1e-5:
                flag = np.append(flag, int(index))

    # print('\n\nHORIZ CURVE\n\n', coords_2d_list, curve, flag)

    return flag

def get_wind_region(coors, domain, point_ids_list, mesh_points):
    # print('\n\n WIND CURVE \n\n', point_ids_list)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        for point_ids in point_ids_list:
            # only works for vertical or horizontal lines
            # horizontal

            # need to subtract one from the point id because the point ids start at 1 while the index starts at 0
            if is_equal(y[index], mesh_points[int(point_ids[0])-1][1]):
                if x[index] <= max(mesh_points[int(point_ids[0])-1][0], mesh_points[int(point_ids[1])-1][0]) + 1e-5 and x[index] >= min(mesh_points[int(point_ids[0])-1][0], mesh_points[int(point_ids[1])-1][0]) - 1e-5:
                    flag = np.append(flag, int(index))
                    # print('added')
                    break
            # vertical
            elif is_equal(x[index], mesh_points[int(point_ids[0])-1][0]):
                if y[index] <= max(mesh_points[int(point_ids[0])-1][1], mesh_points[int(point_ids[1])-1][1]) + 1e-5 and y[index] >= min(mesh_points[int(point_ids[0])-1][1], mesh_points[int(point_ids[1])-1][1]) - 1e-5:
                    flag = np.append(flag, int(index))
                    break

    # print('wind_flag', flag)

    return flag

def get_length_of_sw(curve):
    return math.sqrt((curve[0] - curve[2])**2 + (curve[1] - curve[3])**2)

def define(**kwargs):

    meshio_instance = meshio.Mesh(
        points=kwargs['mesh_points'],
        cells= kwargs['mesh_cells'],
        # cell_data= kwargs['cell_data'],
    )
    
    # filename_mesh = 'RevDesign.mesh'
    filename_mesh = get_sfepy_mesh_from_meshio(meshio_instance)


    options = {
        'output_dir' : '.',
    }

    functions = {
        'plus_x_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, point_ids_list=kwargs['plus_x_wind_load_point_ids'], mesh_points=kwargs['mesh_points']),
                                ),
        'minus_x_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, point_ids_list=kwargs['minus_x_wind_load_point_ids'], mesh_points=kwargs['mesh_points']),
                                ),
        'plus_y_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, point_ids_list=kwargs['plus_y_wind_load_point_ids'], mesh_points=kwargs['mesh_points']),
                                ),
        'minus_y_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, point_ids_list=kwargs['minus_y_wind_load_point_ids'], mesh_points=kwargs['mesh_points']),
                                ),
    }

    regions = {
        'Omega' : 'all',
        'plus_x_wind_region' : ('vertices by plus_x_wind_region', 'facet'),
        'minus_x_wind_region' : ('vertices by minus_x_wind_region', 'facet'),
        'plus_y_wind_region' : ('vertices by plus_y_wind_region', 'facet'),
        'minus_y_wind_region' : ('vertices by minus_y_wind_region', 'facet'),
    }

    if int(kwargs['wind_dir']) == 0:
        wind_region = 'plus_x_wind_region'
        load_val = [[-1],[0]]
    elif int(kwargs['wind_dir']) == 1:
        wind_region = 'plus_y_wind_region'
        load_val = [[0],[-1]]
    elif int(kwargs['wind_dir']) == 2:
        wind_region = 'minus_x_wind_region'
        load_val = [[1],[0]]
    elif int(kwargs['wind_dir']) == 3:
        wind_region = 'minus_y_wind_region'
        load_val = [[0],[1]]

    materials = {
        'solid' : ({'D': stiffness_from_youngpoisson(dim=2, young=1280*144 * 1/12, poisson=.2, plane='strain')},),
        'spring': ({'.stiffness' : 100000}, ),
        'load' : ({'val' : load_val},),
        # 'load' : (None, 'linear_tension'),
    }

    fields = {
        'displacement': ('real', 'vector', 'Omega', 1),
    }

    integrals = {
        'i' : 1,
    }

    variables = {
        'u' : ('unknown field', 'displacement', 0),
        'v' : ('test field', 'displacement', 'u'),
    }

    ebcs = {}

    # having a hard time mixing ebcs and lcbcs
    # also unable to make 
    lcbcs = {
        # 'rigid' : ('vert_shear_wall0', {'u.all' : None}, None, 'rigid'),
    }

    rhs = ''
    region_type = 'facet'
    # region_type = 'vertex'
    for index in range(len(kwargs['horiz_shear_walls'])):
        functions[f'id{kwargs["horiz_shear_walls"][index][-1]}'] = (lambda coors, domain=None, **kwargsv:
                                                    horiz_shear_walls(coors, domain, coords_2d_list=kwargs['horiz_shear_walls']),
                                                )
        # if get_length_of_sw(kwargs['horiz_shear_walls'][index]) < 1:
        #     # print(f'f{kwargs["horiz_shear_walls"][index][-1]}', 'vertex')
        #     region_type = 'vertex'
        regions[f'id{kwargs["horiz_shear_walls"][index][-1]}'] = f'vertices by id{kwargs["horiz_shear_walls"][index][-1]}', region_type
        ebcs[f'id{kwargs["horiz_shear_walls"][index][-1]}'] = f'id{kwargs["horiz_shear_walls"][index][-1]}', {'u.0' : 0.0}
        # if kwargs['fixed_nodes']:
        #     ebcs[f'horiz_shear_wall{index}'] = f'horiz_shear_wall{index}', {'u.0' : 0.0}
        # else:
        #     rhs += f'dw_point_lspring.2.horiz_shear_wall{index}(spring.stiffness, v, u) + '
        #     lcbcs[f'horiz_shear_wall{index}'] = f'horiz_shear_wall{index}', {'u.all' : None}, None, 'rigid'

    region_type = 'facet'
    for index in range(len(kwargs['vert_shear_walls'])):
        functions[f'id{kwargs["vert_shear_walls"][index][-1]}'] = (lambda coors, domain=None, **kwargsv:
                                                    vert_shear_walls(coors, domain, coords_2d_list=kwargs['vert_shear_walls']),
                                                )
        # if get_length_of_sw(kwargs['vert_shear_walls'][index]) < 2:
            # print(kwargs["vert_shear_walls"][index][-1], 'vertex')
            # region_type = 'vertex'
        regions[f'id{kwargs["vert_shear_walls"][index][-1]}'] = f'vertices by id{kwargs["vert_shear_walls"][index][-1]}', region_type
        if kwargs['fixed_nodes']:
            ebcs[f'id{kwargs["vert_shear_walls"][index][-1]}'] = f'id{kwargs["vert_shear_walls"][index][-1]}', {'u.1' : 0}
        else:
            rhs += f'dw_point_lspring.2.id{kwargs["vert_shear_walls"][index][-1]}(spring.stiffness, v, u) + '
            lcbcs[f'id{kwargs["vert_shear_walls"][index][-1]}'] = f'id{kwargs["vert_shear_walls"][index][-1]}', {'u.all' : None}, None, 'rigid',

    equations = {
        'balance_of_forces' :
        f"""dw_lin_elastic.2.Omega(solid.D, v, u) = {rhs}
        dw_surface_ltr.2.{wind_region}(load.val, v)""",
    }

    solvers = {
        'ls': ('ls.auto_direct', {}),
        'newton': ('nls.newton', {
            'i_max'      : 1,
            'eps_a'      : 1e-10,
        }),
    }

    return locals()

def get_sfepy_mesh_from_meshio(m):
    global_cell_types = {
        ('hexahedron', 3): '3_8',
        ('tetra', 3): '3_4',
        ('triangle', 3): '2_3',
        ('triangle', 2): '2_3',
        ('quad', 3): '2_4',
        ('quad', 2): '2_4',
        ('line', 3): '1_2',
        ('line', 2): '1_2',
        ('line', 1): '1_2',
    }

    def mesh_hook(mesh, mode):
        dim = np.sum(np.max(m.points, axis=0)
                        - np.min(m.points, axis=0) > 1e-15)

        ngkey = None
        for k in m.point_data.keys():
            if k == 'node_groups' or k.endswith(':ref'):
                ngkey = k
                break

        if ngkey is not None:
            ngroups = np.asarray(m.point_data[ngkey]).flatten()
        elif hasattr(m, 'point_sets') and len(m.point_sets) > 0:
            ngroups = np.zeros((len(m.points),), dtype=np.int32)
            keys = list(m.point_sets.keys())
            keys.sort()
            try:
                ngrps = [int(ii) for ii in keys]
            except:
                ngrps = np.arange(len(keys)) + 1

            for ik, k in enumerate(keys):
                ngroups[m.point_sets[k]] = ngrps[ik]
        else:
            ngroups = None

        cells, cgroups, cell_types = [], [], []

        # meshio.__version__ > 3.3.2
        cgkey = None
        for k in list(m.cell_data.keys()):
            if k == 'mat_id' or k.endswith(':ref'):
                cgkey = k
                break

        if cgkey is not None:
            cgdata = m.cell_data[cgkey]
        elif len(m.cell_sets) > 0:
            cgdata = []
            keys = list(m.cell_sets.keys())
            keys.sort()
            try:
                cgrps = [int(ii) for ii in keys]
            except:
                cgrps = np.arange(len(keys)) + 1

            for ic, c in enumerate(m.cells):
                cgdata0 = np.zeros((len(c.data),), dtype=np.int32)
                for ik, k in enumerate(keys):
                    cgdata0[m.cell_sets[k][ic]] = cgrps[ik]
                cgdata.append(cgdata0)
        else:
            cgdata = None

        for ic, c in enumerate(m.cells):
            if (c.type, dim) not in global_cell_types:
                output('warning: unknown cell type %s with dimension %d' % (c.type, dim))
                continue

            cells.append(c.data)
            cell_types.append(global_cell_types[(c.type, dim)])

            if cgdata is not None:
                cgroups.append(np.asarray(cgdata[ic]).flatten())
            else:
                cgroups.append(np.ones((len(c.data),), dtype=np.int32))

        mesh = Mesh.from_data('mesh', m.points[:,:dim], ngroups, cells, cgroups, cell_types)
        mesh.dim = dim

        output('number of vertices: %d' % m.points.shape[0])
        output('number of cells:')
        # for ii, k in enumerate(cell_types):
        #     output('  %s: %d' % (k, cells[ii].shape[0]))

        return mesh

    mio = UserMeshIO(mesh_hook)
    return mio