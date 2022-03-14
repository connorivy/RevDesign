import numpy as np
from sfepy.mechanics.matcoefs import stiffness_from_youngpoisson
import math

def is_equal(p1, p2):
    tol = 1e-5
    if abs(p2 - p1) < tol:
        return True
    else:
        return False

def is_equal_wind(p1, p2):
    tol = 1e-1
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
        # for curve in curve_list:
            if is_equal(x[index],curve[0]) and y[index] <= max(curve[1], curve[3]) + 1e-5 and y[index] >= min(curve[1], curve[3]) - 1e-5:
                flag = np.append(flag, int(index))

    print('\n\nVERT CURVE\n\n', coords_2d_list, curve, flag)

    return flag

def horiz_shear_walls(coors, domain, coords_2d_list):
    # there can only be one default value for a function, so pass in the whole list of curves and then remove them as they are used
    curve = coords_2d_list.pop(0)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        # for curve in curve_list:
            if is_equal(y[index],curve[1]) and x[index] <= max(curve[0], curve[2]) + 1e-5 and x[index] >= min(curve[0], curve[2]) - 1e-5:
                flag = np.append(flag, int(index))

    print('\n\nHORIZ CURVE\n\n', coords_2d_list, curve, flag)

    return flag

def get_wind_region(coors, domain, curve_list):
    print('\n\n WIND CURVE \n\n', curve_list)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        for curve in curve_list:
            # only works for vertical or horizontal lines
            # horizontal
            if is_equal_wind(y[index],curve.points[0].x[1]):
                if x[index] <= max(curve.points[0].x[0], curve.points[1].x[0]) + 1e-5 and x[index] >= min(curve.points[0].x[0], curve.points[1].x[0]) - 1e-5:
                    flag = np.append(flag, int(index))
                    break
            # vertical
            elif is_equal_wind(x[index],curve.points[0].x[0]):
                if y[index] <= max(curve.points[0].x[1], curve.points[1].x[1]) + 1e-5 and y[index] >= min(curve.points[0].x[1], curve.points[1].x[1]) - 1e-5:
                    flag = np.append(flag, int(index))
                    break

    print('wind_flag', flag)

    return flag

def get_length_of_sw(curve):
    return math.sqrt((curve[0] - curve[2])**2 + (curve[1] - curve[3])**2)

def define(**kwargs):
    
    filename_mesh = 'RevDesign.mesh'

    options = {
        'output_dir' : '.',
    }

    functions = {
        'plus_x_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, curve_list=kwargs['plus_x_wind_load_curves']),
                                ),
        'minus_x_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, curve_list=kwargs['minus_x_wind_load_curves']),
                                ),
        'plus_y_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, curve_list=kwargs['plus_y_wind_load_curves']),
                                ),
        'minus_y_wind_region' : (lambda coors, domain=None, **kwargsv:
                                    get_wind_region(coors, domain, curve_list=kwargs['minus_y_wind_load_curves']),
                                ),
    }

    regions = {
        'Omega' : 'all',
        'plus_x_wind_region' : ('vertices by plus_x_wind_region', 'facet'),
        'minus_x_wind_region' : ('vertices by minus_x_wind_region', 'facet'),
        'plus_y_wind_region' : ('vertices by plus_y_wind_region', 'facet'),
        'minus_y_wind_region' : ('vertices by minus_y_wind_region', 'facet'),
    }

    materials = {
        'solid' : ({'D': stiffness_from_youngpoisson(dim=2, young=1280*144 * 4/12, poisson=.2, plane='strain')},),
        'spring': ({'.stiffness' : 100000}, ),
        'load' : ({'val' : -1},),
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

    fixed_nodes = True
    rhs = ''
    # region_type = 'facet'
    region_type = 'vertex'
    for index in range(len(kwargs['horiz_shear_walls'])):
        functions[f'horiz_shear_wall{index}'] = (lambda coors, domain=None, **kwargsv:
                                                    horiz_shear_walls(coors, domain, coords_2d_list=kwargs['horiz_shear_walls']),
                                                )
        if get_length_of_sw(kwargs['horiz_shear_walls'][index]) < 1:
            print(f'horiz_shear_wall{index}', 'vertex')
            region_type = 'vertex'
        regions[f'horiz_shear_wall{index}'] = f'vertices by horiz_shear_wall{index}', region_type
        ebcs[f'horiz_shear_wall{index}'] = f'horiz_shear_wall{index}', {'u.0' : 0.0}
        # if fixed_nodes:
        #     ebcs[f'horiz_shear_wall{index}'] = f'horiz_shear_wall{index}', {'u.0' : 0.0}
        # else:
        #     rhs += f'dw_point_lspring.2.horiz_shear_wall{index}(spring.stiffness, v, u) + '
        #     lcbcs[f'horiz_shear_wall{index}'] = f'horiz_shear_wall{index}', {'u.all' : None}, None, 'rigid'

    # region_type = 'facet'
    for index in range(len(kwargs['vert_shear_walls'])):
        functions[f'vert_shear_wall{index}'] = (lambda coors, domain=None, **kwargsv:
                                                    vert_shear_walls(coors, domain, coords_2d_list=kwargs['vert_shear_walls']),
                                                )
        if get_length_of_sw(kwargs['vert_shear_walls'][index]) < 2:
            print(f'vert_shear_wall{index}', 'vertex')
            region_type = 'vertex'
        regions[f'vert_shear_wall{index}'] = f'vertices by vert_shear_wall{index}', region_type
        if fixed_nodes:
            ebcs[f'vert_shear_wall{index}'] = f'vert_shear_wall{index}', {'u.1' : 0}
        else:
            rhs += f'dw_point_lspring.2.vert_shear_wall{index}(spring.stiffness, v, u) + '
            lcbcs[f'vert_shear_wall{index}'] = f'vert_shear_wall{index}', {'u.all' : None}, None, 'rigid',

    equations = {
        'balance_of_forces' :
        f"""dw_lin_elastic.2.Omega(solid.D, v, u) = {rhs}
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