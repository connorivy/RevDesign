r"""
Biot problem - deformable porous medium with the no-penetration boundary
condition on a boundary region.

Find :math:`\ul{u}`, :math:`p` such that:

.. math::
    \int_{\Omega} D_{ijkl}\ e_{ij}(\ul{v}) e_{kl}(\ul{u})
    - \int_{\Omega}  p\ \alpha_{ij} e_{ij}(\ul{v})
    = 0
    \;, \quad \forall \ul{v} \;,

    \int_{\Omega} q\ \alpha_{ij} e_{ij}(\ul{u})
    + \int_{\Omega} K_{ij} \nabla_i q \nabla_j p
    = 0
    \;, \quad \forall q \;,

    \ul{u} \cdot \ul{n} = 0 \mbox{ on } \Gamma_{walls} \;,

where

.. math::
    D_{ijkl} = \mu (\delta_{ik} \delta_{jl}+\delta_{il} \delta_{jk}) +
    \lambda \ \delta_{ij} \delta_{kl}
    \;.
"""
from __future__ import absolute_import
import os
import numpy as np

from sfepy.linalg import get_coors_in_tube
from sfepy.mechanics.matcoefs import stiffness_from_lame

def define(**kwargs):
    from sfepy import data_dir

    filename = data_dir + '/meshes/3d/cylinder.mesh'
    output_dir = 'output'
    return define_input(filename, output_dir, **kwargs)

def cinc_simple(coors, mode):
    axis = np.array([1, 0, 0], np.float64)
    if mode == 0: # In
        centre = np.array([0.0, 0.0, 0.0], np.float64)
        radius = 0.019
        length = 0.00002
    elif mode == 1: # Out
        centre = np.array([0.1, 0.0, 0.0], np.float64)
        radius = 0.019
        length = 0.00002
    elif mode == 2: # Rigid
        centre = np.array([0.05, 0.0, 0.0], np.float64)
        radius = 0.015
        length = 0.03
    else:
        raise ValueError('unknown mode %s!' % mode)

    return get_coors_in_tube(coors,
                             centre, axis, -1, radius, length)

def define_regions(filename):
    if filename.find('simple.mesh'):
        dim = 3
        regions = {
            'Omega' : 'all',
            'Walls' : ('vertices of surface -v (r.Outlet +f r.Inlet)', 'facet'),
            'Inlet' : ('vertices by cinc_simple0', 'facet'),
            'Outlet' : ('vertices by cinc_simple1', 'facet'),
            'Rigid' : 'vertices by cinc_simple2',
        }

    else:
        raise ValueError('unknown mesh %s!' % filename)

    return regions, dim

def get_pars(ts, coor, mode, output_dir='.', **kwargs):
    if mode == 'qp':
        n_nod, dim = coor.shape
        sym = (dim + 1) * dim // 2

        out = {}
        out['D'] = np.tile(stiffness_from_lame(dim, lam=1.7, mu=0.3),
                           (coor.shape[0], 1, 1))

        aa = np.zeros((sym, 1), dtype=np.float64)
        aa[:dim] = 0.132
        aa[dim:sym] = 0.092
        out['alpha'] = np.tile(aa, (coor.shape[0], 1, 1))

        perm = np.eye(dim, dtype=np.float64)
        out['K'] = np.tile(perm, (coor.shape[0], 1, 1))

        return out

def is_equal(p1, p2):
    tol = 1e-5
    if abs(p2 - p1) < tol:
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

    # print('\n\n SHEAR FLAG\n\n', flag, flag.shape[0])

    return flag

def get_wind_region(coors, domain, curve_list):
    # print('\n\n WIND CURVE \n\n', curve_list)
    flag = np.array([ ], dtype='int16')
    x, y = coors[:, 0], coors[:, 1]
    for index in range(len(x)):
        for curve in curve_list:
            # only works for vertical or horizontal lines
            # horizontal
            if is_equal(y[index],curve.points[0].x[1]):
                if x[index] <= max(curve.points[0].x[0], curve.points[1].x[0]) + 1e-5 and x[index] >= min(curve.points[0].x[0], curve.points[1].x[0]) - 1e-5:
                    flag = np.append(flag, int(index))
                    break
            # vertical
            elif is_equal(x[index],curve.points[0].x[0]):
                if y[index] <= max(curve.points[0].x[1], curve.points[1].x[1]) + 1e-5 and y[index] >= min(curve.points[0].x[1], curve.points[1].x[1]) - 1e-5:
                    flag = np.append(flag, int(index))
                    break

    return flag


def define_input(filename, output_dir, **kwargs):

    filename_mesh = filename
    options = {
        'output_dir' : output_dir,
        'output_format' : 'vtk',
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

    functions = {
        'cinc_simple0' : (lambda coors, domain:
                          cinc_simple(coors, 0),),
        'cinc_simple1' : (lambda coors, domain:
                          cinc_simple(coors, 1),),
        'cinc_simple2' : (lambda coors, domain:
                          cinc_simple(coors, 2),),
        'get_pars' : (lambda ts, coors, mode=None, **kwargs:
                      get_pars(ts, coors, mode,
                               output_dir=output_dir, **kwargs),),
    }
    regions, dim = define_regions(filename_mesh)

    field_1 = {
        'name' : 'displacement',
        'dtype' : np.float64,
        'shape' : dim,
        'region' : 'Omega',
        'approx_order' : 1,
    }
    field_2 = {
        'name' : 'pressure',
        'dtype' : np.float64,
        'shape' : 1,
        'region' : 'Omega',
        'approx_order' : 1,
    }

    variables = {
        'u'       : ('unknown field',   'displacement', 0),
        'v'       : ('test field',      'displacement', 'u'),
        'p'       : ('unknown field',   'pressure', 1),
        'q'       : ('test field',      'pressure', 'p'),
    }

    ebcs = {
        'inlet' : ('Inlet', {'p.0' : 1.0, 'u.all' : 0.0}),
        'outlet' : ('Outlet', {'p.0' : -1.0}),
    }

    lcbcs = {
        'rigid' : ('Outlet', {'u.all' : None}, None, 'rigid'),
    }

    material_1 = {
        'name' : 'm',
        # 'values' : {
        #             'D' : 100,
        #             'alpha' : 100
        #             }
        'function' : 'get_pars',
    }

    material_2 = {
        'name' : 'load',
        'values' : {
                    '.val' : 100000
                    }
    }

    integral_1 = {
        'name' : 'i',
        'order' : 2,
    }

    # equations = {
    #     'eq_1' :
    #     """dw_lin_elastic.i.Omega( m.D, v, u )
    #      - dw_biot.i.Omega( m.alpha, v, p )
    #      = 0""",
    # }

    equations = {
        'balance_of_forces' :
        """dw_lin_elastic.2.Omega(m.D, v, u) = 
        dw_surface_ltr.2.Outlet(load.val, v)""",
    }

    solvers = {
        'ls': ('ls.auto_direct', {}),
        'newton': ('nls.newton', {
            'i_max'      : 1,
            'eps_a'      : 1e-10,
        }),
    }

    print(lcbcs)

    return locals()
