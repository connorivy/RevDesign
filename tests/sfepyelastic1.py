'''
Created on Oct 23, 2015

@author: m9imhof
'''
import numpy as np

import sys
sys.path.append('.')

import sfepy
from sfepy.base.base import IndexedStruct
from sfepy.discrete import FieldVariable, Material, Integral, Equation, Equations, Problem
from sfepy.discrete.fem import Mesh, FEDomain, Field
from sfepy.terms import Term
from sfepy.discrete.conditions import Conditions, EssentialBC, LinearCombinationBC
from sfepy.solvers.ls import ScipyDirect
from sfepy.solvers.nls import Newton


def main():
    print(sfepy.__version__)

    from sfepy import data_dir
    mesh = Mesh.from_file('.\model\sfepy_pb_description\RevDesign.vtk')

    domain = FEDomain('domain', mesh)

    omega = domain.create_region('Omega', 'all', 'cell')
    gamma= domain.create_region('Gamma', 'vertices of surface', 'facet')
    delta = domain.create_region('Delta', 'vertex 2', 'vertex')

    field = Field.from_args('displacement', np.float64, 'vector', omega, approx_order=1)

    u = FieldVariable('u', 'unknown', field)
    v = FieldVariable('v', 'test', field, primary_var_name='u')

    m = Material('m', lam=1.0, mu=1.0)
    integral = Integral('i', order=2)

    t1 = Term.new('dw_lin_elastic_iso(m.lam, m.mu, v, u)', integral, omega, m=m, v=v, u=u)
    eq = Equation('balance', t1)
    eqs = Equations([eq])

    ebcs = Conditions( [
                        # EssentialBC('fixed', delta, {'u.0' : 100.0, 'u.1' : 1.0}),
                        # EssentialBC('fixed', gamma, {'u.all' : 0.0}),
                        ])

    lcbcs = Conditions( [
                        LinearCombinationBC(name='rigid', regions=[gamma,None], dofs={'u.all' : None, }, dof_map_fun=None, kind='rigid', arguments=()),
                        # LinearCombinationBC(name='normal', regions=[gamma,None], dofs={'u.all' : None, }, dof_map_fun=None, kind='no_penetration', arguments=(None,)),
                        ])

    ls = ScipyDirect({})
    nls_status = IndexedStruct()

    pb = Problem('elasticity', equations=eqs)
    pb.time_update(ebcs=ebcs, lcbcs=lcbcs)

    ev = pb.get_evaluator()
    nls = Newton({}, lin_solver=ls, status=nls_status,
                 fun=ev.eval_residual, fun_grad=ev.eval_tangent_matrix)

    pb.set_solver(nls)

    vec = pb.solve()


    pb.save_regions_as_groups('regions')

    print(nls_status)
    print(np.amin(vec.vec), np.amax(vec.vec))
    #print 'vec', vec.vec.tolist()

if __name__ == '__main__':
    main()
