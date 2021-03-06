
from __future__ import absolute_import
from sfepy.base.conf import ProblemConf
from sfepy.discrete import Problem
from sfepy.applications import PDESolverApp, EVPSolverApp, solve_pde
try:
    from . import input, input_for_applied_loads
except:
    import input
    import input_for_applied_loads

import numpy as np
import meshio

from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base

def get_sfepy_pb(**kwargs):
    conf = ProblemConf.from_dict(input.define(**kwargs), input)
    # conf = ProblemConf.from_dict(biot_npbc.define(**kwargs), biot_npbc)
    # pb = Problem.from_conf(conf, init_solvers=False)
    pb, state = solve_pde(conf)
    # out = pb.get_variables().create_output()
    # pb.save_state(f'mesh_displacements_{kwargs["mesh_id"]}.vtk', state=state)

    variables = pb.get_variables()
    u = variables.get_state_parts()['u']

    return pb, state, u.reshape(-1, 2)

def create_mesh_applied_loads(**kwargs):
    conf = ProblemConf.from_dict(input_for_applied_loads.define(**kwargs), input_for_applied_loads)
    pb, state = solve_pde(conf)

    # https://sfepy.org/doc-devel/primer.html#table-of-contents
    variables = pb.get_variables()
    u = variables.get_state_parts()['u']
    pb.remove_bcs()

    f = pb.evaluator.eval_residual(u)

    pb.time_update()
    fvars = variables.copy()
    fvars.set_state(f, reduced=False)
    out = variables.create_output()
    # pb.save_state(f'mesh_applied_loads_{kwargs["mesh_id"]}.vtk', state=state)

    return f.reshape((-1, 2))

def create_mesh_reactions(pb, u, fixed_nodes, mesh_id):
    # https://sfepy.org/doc-devel/primer.html#table-of-contents
    variables = pb.get_variables()
    pb.remove_bcs()
    shear_walls = {}

    u = u.ravel()
    f = pb.evaluator.eval_residual(u)
    f = f.reshape(-1, 2)
    u = u.reshape(-1, 2)
    if not fixed_nodes:
        spring = pb.get_materials()['spring']

    for region in pb.domain.regions:
        region_name = region.name
        if not region_name[:2] == 'id':
            continue
        reg = pb.domain.regions[f'{region_name}']
        dofs = pb.fields['displacement'].get_dofs_in_region(reg, merge=True)
        if not fixed_nodes:
            f[dofs] = u[dofs] * spring.get_data('special', 'stiffness')
        total_shear = np.fromiter(map(sum,zip(*f[dofs])),dtype='float64')
        # print('SHEAR', max(abs(total_shear)), type(max(abs(total_shear))), type(region_name))
        shear_walls[region_name[2:]] = {
            'totalShear': max(abs(total_shear)),
        }

    f = f.ravel()
    np.round_(f, decimals = 5)
    pb.time_update()
    fvars = variables.copy()
    fvars.set_state(f, reduced=False)
    out = variables.create_output()
    # pb.save_state(f'mesh_reactions_{mesh_id}.vtk', out=out)

    return f.reshape((-1, 2)), shear_walls

def get_reactions_in_region(pb, state, regions, fixed_nodes, dim = 2):
    # https://mail.python.org/archives/list/sfepy@python.org/thread/P7BPSHZEHCMHEPUHLUQVRI7DGBOALRRS/
    # state is the State containing your variables with the problem solution.
    shear_walls = {}
    if fixed_nodes:
        state.apply_ebc()
        pb.remove_bcs()
        nls = pb.get_nls()
        residual = nls.fun(state())

        for region_name in regions:
            # then the reaction forces in the nodes of a given region can be obtained by:
            reg = pb.domain.regions[f'id{region_name}']
            dofs = pb.fields['displacement'].get_dofs_in_region(reg, merge=True)

            res = residual.reshape((-1, dim)) # dim = space dimension = DOFs per node.
            reactions = res[dofs]
            total_shear = [0,0]
            for rxn in reactions:
                total_shear += rxn

            shear_walls[region_name] = {
                'totalShear': max(abs(total_shear)),
            }
    else:
        for region_name in regions:
            reg = pb.domain.regions[f'id{region_name}']
            dofs = pb.fields['displacement'].get_dofs_in_region(reg, merge=True)
            spring = pb.get_materials()['spring']

            variables = pb.get_variables()
            u = variables.get_state_parts()['u'].reshape((-1, dim))
            reactions_list = u[dofs] * spring.get_data('special', 'stiffness')
            total_shear = np.fromiter(map(sum,zip(*reactions_list)),dtype='float64')

            shear_walls[region_name] = {
                'totalShear': max(abs(total_shear)),
            }

    return shear_walls


def stress_strain(out, pb, state, extend=False):
    """
    Calculate and output strain and stress for given displacements.
    """
    from sfepy.base.base import Struct

    ev = pb.evaluate
    strain = ev('ev_cauchy_strain.2.Omega(u)', mode='el_avg')
    stress = ev('ev_cauchy_stress.2.Omega(solid.D, u)', mode='el_avg',
                copy_materials=False)

    out['cauchy_strain'] = Struct(name='output_data', mode='cell',
                                  data=strain, dofs=None)
    out['cauchy_stress'] = Struct(name='output_data', mode='cell',
                                  data=stress, dofs=None)

    return out

# pb = get_sfepy_pb()
# create_mesh_reactions(pb)