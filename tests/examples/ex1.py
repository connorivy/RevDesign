from dotmap import DotMap
import pygmsh

def define():
    HOST = 'https://speckle.xyz'
    STREAM_ID = 'd059f9a269'
    OBJECT_ID = '18ae0461a7aba309b8eecde65f887fca'
    mesh_size = 5
    outline = DotMap({
        'segments' : [
            {
                'start' : {
                    'x': 14.688162108019782,
                    'y': 42.63540133841364,
                    'z': 0
                },
                'end' : {
                    'x': -5.311837891980204,
                    'y': 42.6354013384137,
                    'z': 0
                }
            }, 
            {
                'start' : {
                    'x': -5.311837891980204,
                    'y': 42.6354013384137,
                    'z': 0
                },
                'end' : {
                    'x': -5.311837891980204,
                    'y': 41.6354013384137,
                    'z': 0
                }
            },
            {
                'start' : {
                    'x': -5.311837891980204,
                    'y': 41.6354013384137,
                    'z': 0
                },
                'end' : {
                    'x': 14.688162108019782,
                    'y': 41.6354013384137,
                    'z': 0
                }
            },
            {
                'start' : {
                    'x': 14.688162108019782,
                    'y': 41.6354013384137,
                    'z': 0
                },
                'end' : {
                    'x': 14.688162108019782,
                    'y': 42.63540133841364,
                    'z': 0
                }
            },
        ]
    })
    coords_before_adding_shearwalls = [
        (14.688162, 42.635401),
        (-5.311838, 42.635401),
        (-5.311838, 41.635401),
        (14.688162, 41.635401)
    ]
    coords_after_adding_shearwalls = [
        (14.688162, 42.635401),
        (-5.061838, 42.639964),
        (-5.311838, 42.635401),
        (-5.311838, 41.635401),
        (-5.061838, 41.635401),
        (14.688162, 41.635401)
    ]
    coord_dict_walls = {
        '40f7df8aa3ad19c457a5d71239c79209': (-5.311838, 42.635401, -5.311838, 41.635401), 
        '890059336dacebda25cdc85ef5630b42': (-5.311838, 41.635401, -5.061838, 41.635401), 
        'f7a242d3af70728d2381e9c4a09b7396': (-5.311838, 42.639964, -5.061838, 42.639964)
    }
    with pygmsh.geo.Geometry() as geom:
        surface = geom.add_polygon(coords_after_adding_shearwalls, mesh_size=mesh_size)

    minus_x_wind_load_point_ids = [(3,4)]
    plus_x_wind_load_point_ids = [(6,1)]
    minus_y_wind_load_point_ids = [(4, 5), (5, 6)]
    plus_y_wind_load_point_ids = [(2, 3), (1, 2)]

    return locals()