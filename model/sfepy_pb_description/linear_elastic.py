
from __future__ import absolute_import
from sfepy.base.conf import ProblemConf
from sfepy.discrete import Problem
from sfepy.applications import PDESolverApp, EVPSolverApp, solve_pde
try:
    from . import input
except:
    import input

try:
    from . import biot_npbc
except:
    import biot_npbc

import numpy as np
import meshio

def get_sfepy_pb(**kwargs):
    conf = ProblemConf.from_dict(input.define(**kwargs), input)
    # conf = ProblemConf.from_dict(biot_npbc.define(**kwargs), biot_npbc)
    # pb = Problem.from_conf(conf, init_solvers=False)
    pb, state = solve_pde(conf)
    # out = pb.get_variables().create_output()
    pb.save_state('mesh_displacements.vtk', state=state)

    return pb, state
    
def create_mesh_reactions(pb):
    # https://sfepy.org/doc-devel/primer.html#table-of-contents
    variables = pb.get_variables()
    u = variables.get_state_parts()['u']
    pb.remove_bcs()

    f = pb.evaluator.eval_residual(u)

    pb.time_update()
    fvars = variables.copy()
    print('f', f, f.shape)
    fvars.set_state(f, reduced=False)
    out = variables.create_output()
    pb.save_state('mesh_reactions.vtk', out=out)

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

            print(total_shear, type(total_shear), type(max(abs(total_shear))), max(abs(total_shear)))
            shear_walls[region_name] = {
                'totalReaction': max(abs(total_shear)),
                # 'edited': True
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

            print(total_shear, type(total_shear), type(max(abs(total_shear))), max(abs(total_shear)))

            shear_walls[region_name] = {
                'totalReaction': max(abs(total_shear)),
                # 'edited': True
            }

    return shear_walls

def send_to_speckle(client, STREAM_ID, data):
    # shear_wall = client.object.get(stream_id=STREAM_ID, object_id=region_name)
    base = Base(data=data)
    print(base, isinstance(base, Base))

    from pprint import pprint

    # for key, value in vars(res['@Analytical Nodes'][5]).items():
    #     print(key, value)

    #     try:
    #         if vars(value):
    #             print('\n\n')
    #             print(vars(value))
    #             print('\n\n')
    #     except:
    #         continue
    pprint(vars(base))
    transport = ServerTransport(STREAM_ID, client)
    obj_id = operations.send(base, [transport])

    # now create a commit on that branch with your updated data!
    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        message="testing123",
    )


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