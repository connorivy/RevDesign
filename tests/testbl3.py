import gmsh
import meshio
import numpy as np

def extract_to_meshio():
    # extract point coords
    idx, points, _ = gmsh.model.mesh.getNodes()
    points = np.asarray(points).reshape(-1, 3)
    idx -= 1
    srt = np.argsort(idx)
    assert np.all(idx[srt] == np.arange(len(idx)))
    points = points[srt]

    # extract cells
    elem_types, elem_tags, node_tags = gmsh.model.mesh.getElements()
    cells = []
    for elem_type, elem_tags, node_tags in zip(elem_types, elem_tags, node_tags):
        # `elementName', `dim', `order', `numNodes', `localNodeCoord',
        # `numPrimaryNodes'
        num_nodes_per_cell = gmsh.model.mesh.getElementProperties(elem_type)[3]

        node_tags_reshaped = np.asarray(node_tags).reshape(-1, num_nodes_per_cell) - 1
        node_tags_sorted = node_tags_reshaped[np.argsort(elem_tags)]
        cells.append(
            meshio.CellBlock(
                meshio.gmsh.gmsh_to_meshio_type[elem_type], node_tags_sorted
            )
        )

    cell_sets = {}
    for dim, tag in gmsh.model.getPhysicalGroups():
        name = gmsh.model.getPhysicalName(dim, tag)
        cell_sets[name] = [[] for _ in range(len(cells))]
        for e in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
            # TODO node_tags?
            # elem_types, elem_tags, node_tags
            elem_types, elem_tags, _ = gmsh.model.mesh.getElements(dim, e)
            assert len(elem_types) == len(elem_tags)
            assert len(elem_types) == 1
            elem_type = elem_types[0]
            elem_tags = elem_tags[0]

            meshio_cell_type = meshio.gmsh.gmsh_to_meshio_type[elem_type]
            # make sure that the cell type appears only once in the cell list
            # -- for now
            idx = []
            for k, cell_block in enumerate(cells):
                if cell_block.type == meshio_cell_type:
                    idx.append(k)
            assert len(idx) == 1
            idx = idx[0]
            cell_sets[name][idx].append(elem_tags - 1)

        cell_sets[name] = [
            (None if len(idcs) == 0 else np.concatenate(idcs))
            for idcs in cell_sets[name]
        ]

    # make meshio mesh
    return meshio.Mesh(points, cells, cell_sets=cell_sets)


gmsh.initialize()
model_name = "testbl3"
gmsh.model.add(model_name)
geo = gmsh.model.geo
mesh = gmsh.model.mesh
field = gmsh.model.mesh.field

# Corner points
lc = 0.2
p0 = geo.addPoint(0, 0, 0, lc)
p1 = geo.addPoint(1, 0, 0, lc)
p2 = geo.addPoint(1, 1, 0, lc)
p3 = geo.addPoint(0, 1, 0, lc)

# Fracture points
lcf = lc/10
pa = geo.addPoint(0.33, 0, 0, lcf)
pb = geo.addPoint(0.33, 0.33, 0, lcf)

# Higher dim objects
l00 = geo.addLine(p0, pa)
l01 = geo.addLine(pa, p1)
l1 = geo.addLine(p1, p2)
l2 = geo.addLine(p2, p3)
l3 = geo.addLine(p3, p0)
cl = geo.addCurveLoop([l00, l01, l1, l2, l3])
surf = geo.addPlaneSurface([cl])

# Fracture
lfrac = geo.addLine(pa, pb)
geo.synchronize()
mesh.embed(1, [lfrac], 2, surf)

# # Boundary layer on boundary edge
# '''
# Without mesh.embed, the boundary layer around [l00, l01] works.

# With mesh.embed, the following error occurs
# Error   : The 1D mesh seems not to be forming a closed loop (2 boundary nodes are considered once)
# '''
# bledge = field.add("BoundaryLayer")
# field.setNumbers(bledge, "CurvesList", [l00, l01])
# field.setNumbers(bledge, "PointsList", [p0, p1])
# field.setNumber(bledge, "SizeFar", 0.1)
# field.setNumber(bledge, "Size", lc/100)
# field.setNumber(bledge, "Thickness", 0.4)
# field.setNumber(bledge, "Ratio", 1.4)
# field.setNumber(bledge, "BetaLaw", 0.5)
# field.setAsBoundaryLayer(bledge)

# # Boundary layer on fracture
# blfracture = field.add("BoundaryLayer")
# field.setNumbers(blfracture, "CurvesList", [lfrac])
# field.setNumbers(blfracture, "PointsList", [pa, pb])
# field.setNumber(blfracture, "SizeFar", 0.1)
# field.setNumber(blfracture, "Size", lcf/10)
# field.setNumber(blfracture, "Thickness", 0.2)
# field.setNumber(blfracture, "Ratio", 1.4)
# field.setNumber(blfracture, "BetaLaw", 0.5)
# field.setAsBoundaryLayer(blfracture)


geo.synchronize()
mesh.setRecombine(2, surf)
mesh.generate(2)
outmesh = extract_to_meshio()
outmesh.write('.\model\sfepy\RevDesign.vtk')
# gmsh.write(model_name + ".msh")
gmsh.finalize()
