import numpy as np
from sfepy.mechanics.matcoefs import stiffness_from_youngpoisson

def is_equal(p1, p2):
    tol = 1e-2
    if abs(p2 - p1) < tol:
        return True
    else:
        return False

def get_wind_region(coors, domain, point_ids_list, mesh_points):
    print('\n\n WIND CURVE \n\n', point_ids_list)
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
    print('wind_flag', flag)
    return flag

def linear_tension(ts, coor, mode=None, **kwargs):
    if mode == 'qp':
        val = np.tile([[0],[-1.0]], (coor.shape[0], 1, 1))

        print('COOR.SHAPE, VAL ', coor.shape, val, val.shape)

        return {'val' : val}

def define(**kwargs):
    
    filename_mesh = 'RevDesign.mesh'

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
        'linear_tension' : (linear_tension,),
    }

    regions = {
        'Omega' : 'all',
        'plus_x_wind_region' : ('vertices by plus_x_wind_region', 'facet'),
        'minus_x_wind_region' : ('vertices by minus_x_wind_region', 'facet'),
        'plus_y_wind_region' : ('vertices by plus_y_wind_region', 'facet'),
        'minus_y_wind_region' : ('vertices by minus_y_wind_region', 'facet'),
    }

    materials = {
        'solid' : ({'D': stiffness_from_youngpoisson(dim=2, young=1280*144 * 1/12, poisson=.2, plane='strain')},),
        'load' : ({'val' : [[.2],[-.8]]},),
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

    ebcs = {
        'all' : ('Omega', {'u.all' : 0.0}),
    }

    equations = {
        'balance_of_forces' :
        f"""dw_lin_elastic.2.Omega(solid.D, v, u) =
        dw_surface_ltr.2.plus_y_wind_region(load.val, v)""",
    }

    solvers = {
        'ls': ('ls.auto_direct', {}),
        'newton': ('nls.newton', {
            'i_max'      : 1,
            'eps_a'      : 1e-10,
        }),
    }

    return locals()