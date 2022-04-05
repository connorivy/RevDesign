from .utils import ft_inches_to_decimal as ft2dec
from specklepy.objects import Base
import math

class Project:
    def __init__(self):
        self.wind_reduction_factor = .6
        self.DL_reduction_factor = .85

        self.shear_wall_schedule = ShearWallSchedule()

    def get_DL_psf(self, type):
        if type == 'unit':
            return 27
        elif type == 'roof':
            return 15
        elif type == 'corridor':
            return 28
        else:
            print(f'{type} is not a valid dead load type')

class ShearWall(Base):
    def __init__(self, projectInfo, id, length, studHeight, start, end, baseLevelElevation, topLevelElevation, baseOffset, topOffset, topViewElevation, \
                    bottomViewElevation, totalShear, floorTrib, floorLoadType, tieDistance = 1):
        
        self.project_info = projectInfo
        self.id = id
        self.length = length
        self.stud_height = studHeight
        self.start = start
        self.end = end
        self.base_level_elevation = baseLevelElevation
        self.top_level_elevation = topLevelElevation
        self.base_offset = baseOffset
        self.top_offset = topOffset
        self.top_view_elevation = topViewElevation
        self.bottom_view_elevation = bottomViewElevation
        self.shear_point_load = totalShear
        self.floor_trib = floorTrib
        self.floor_load_type= floorLoadType
        self.tie_distance = tieDistance

        # self.get_base_elev()
        # self.get_stud_height()
        # self.get_self_weight_plf()
        # self.get_shear_point_load()
        # self.get_shear_force()
        # self.get_overturning_moment()
        # self.get_resisting_moment()
        # self.get_total_moment()
        # self.get_chord_forces()
    def get_base_elevation(self):
        self.base_elevation = self.base_level_elevation + self.base_offset

    def get_top_elevation(self):
        self.top_elevation = self.top_level_elevation + self.top_offset

    def get_self_weight_plf(self):
        self.weight = 7 * self.stud_height

    # def get_shear_point_load(self):
    #     # wind shear at level * wind trib * wall_len / greater_wall_len
    #     # don't subtract one to level because the level 1 wall is acted on by level 2 wind 
    #     self.shear_point_load = self.project_info.wind_reduction_factor * self.project_info.shear_per_lvl_plf[math.floor(self.lvl)] * self.wind_trib * self.length / self.greater_wall_len

    def get_shear_force(self):
        self.shear_force = self.shear_point_load / self.length

    def get_overturning_moment(self, elev_for_moment=-1):
        if elev_for_moment == -1:
            elev_for_moment = self.base_elevation

        self.overturning_moment = self.shear_point_load * (self.top_elevation - elev_for_moment)
        return self.overturning_moment

    def get_resisting_moment(self):
        dist_dead_load = self.project_info.get_DL_psf(self.floor_load_type) * self.floor_trib + self.weight
        self.resisting_moment = self.project_info.DL_reduction_factor * dist_dead_load * self.length ** 2 / 2

    def get_total_moment(self):
        self.total_moment = self.resisting_moment - self.overturning_moment

    def get_chord_forces(self):
        self.chord_forces = self.total_moment / (self.length - self.tie_distance)


class StackedShearWall(Base):
    # stacked shear walls is expecting input that looks like this (project_info, [these are the args for a wall except project info], [these are a differnt wall args])
    def __init__(self, id):
        self.id = id
        self.shear_walls = []

        self.shear_force = []
        self.overturning_moment = []
        self.resisting_moment = []
        self.total_moment = []
        self.chord_forces = []

    def add_shear_wall(self, obj):
        if isinstance(obj, ShearWall):
            self.shear_walls.append(obj)
        else:
            print('Only ShearWall objects allowed in StackedShearWall')

    def compute_values(self):
        self.num_shear_walls = len(self.shear_walls)
        self.shear_walls.sort(key=lambda x: x.base_elevation)

        for index in range(len(self.shear_walls)):
            print(f'BASE ELEVATION {self.shear_walls[index].base_elevation}:')
            print('---------------------------------------------')
            self.get_shear_force_at_lvl(index)
            self.get_overturning_moment_at_lvl(index)
            self.get_resisting_moment_at_lvl(index)
            self.get_total_moment_at_lvl(index)
            self.get_chord_forces_at_lvl(index)

    def get_shear_force_at_lvl(self, start_index):
        shear_force = 0
        for index in range(start_index, self.num_shear_walls):
            shear_force += self.shear_walls[index].shear_force
        self.shear_force.append(shear_force)
        # print('Shear Force', self.shear_force[-1])

    def get_overturning_moment_at_lvl(self, start_index):
        overturning_moment = 0
        moment_elevation = self.shear_walls[start_index].base_elevation

        for index in range(start_index, self.num_shear_walls):
            overturning_moment += self.shear_walls[index].get_overturning_moment(moment_elevation)

        self.overturning_moment.append(overturning_moment)
        # print('Overturning Moment', self.overturning_moment[-1])

    def get_resisting_moment_at_lvl(self, start_index):
        resisting_moment = 0
        for index in range(start_index, self.num_shear_walls):
            resisting_moment += self.shear_walls[index].resisting_moment
        self.resisting_moment.append(resisting_moment)
        # print('Resisting Moment', self.resisting_moment[-1])

    def get_total_moment_at_lvl(self, index):
        self.total_moment.append(self.overturning_moment[index] - self.resisting_moment[index])
        # print('Total Moment', self.total_moment[lvl - self.min_lvl])

    def get_chord_forces_at_lvl(self, index):
        self.chord_forces.append(self.total_moment[index] / (self.shear_walls[index].length - self.shear_walls[index].tie_distance))
        # print('Chord Forces', self.chord_forces[lvl - self.min_lvl])

class ShearWallScheduleEntry():
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self) -> str:
        return self.name

class ShearWallSchedule():
    def __init__(self) -> None:
        self.shear_walls = []

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '1',
            'material': 'GYP BOARD',
            'thickness': '5/8"',
            'fasteners': '6D COOLER (0.092" DIA x 1 7/8", 1/4" HEAD)',
            'max_fas_spacing': '7" OC',
            'blocking': 'UNBLOCKED',
            'holddown_force': 0,
            'wind_shear': 230
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '2',
            'material': 'GYP BOARD',
            'thickness': '5/8"',
            'fasteners': '6D COOLER (0.092" DIA x 1 7/8", 1/4" HEAD)',
            'max_fas_spacing': '7" OC',
            'blocking': 'UNBLOCKED',
            'holddown_force': 5,
            'wind_shear': 230
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '3',
            'material': 'GYP BOARD',
            'thickness': '5/8"',
            'fasteners': '6D COOLER (0.092" DIA x 1 7/8", 1/4" HEAD)',
            'max_fas_spacing': '4" OC',
            'blocking': 'UNBLOCKED',
            'holddown_force': 0,
            'wind_shear': 290
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '4',
            'material': 'GYP BOARD',
            'thickness': '5/8"',
            'fasteners': '6D COOLER (0.092" DIA x 1 7/8", 1/4" HEAD)',
            'max_fas_spacing': '4" OC',
            'blocking': 'BLOCKED',
            'holddown_force': 0,
            'wind_shear': 350
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '5',
            'material': 'GYP BOARD',
            'thickness': '5/8"',
            'fasteners': '6D COOLER (0.092" DIA x 1 7/8", 1/4" HEAD)',
            'max_fas_spacing': '4" OC',
            'blocking': 'BLOCKED',
            'holddown_force': 5,
            'wind_shear': 350
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '6',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '6" OC',
            'blocking': None,
            'holddown_force': 0,
            'wind_shear': 730
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '7',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '6" OC',
            'blocking': None,
            'holddown_force': 10,
            'wind_shear': 730
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '8',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '4" OC',
            'blocking': None,
            'holddown_force': 5,
            'wind_shear': 1065
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '9',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '4" OC',
            'blocking': None,
            'holddown_force': 15,
            'wind_shear': 1065
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '10',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '3" OC',
            'blocking': None,
            'holddown_force': 15,
            'wind_shear': 1370
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '11',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '3" OC',
            'blocking': None,
            'holddown_force': 25,
            'wind_shear': 1370
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '12',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '2" OC',
            'blocking': None,
            'holddown_force': 15,
            'wind_shear': 1790
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '13',
            'material': 'APA RATED SHEATHING',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '2" OC',
            'blocking': None,
            'holddown_force': 25,
            'wind_shear': 1790
        }))

        self.shear_walls.append(ShearWallScheduleEntry(**{
            'name': '14',
            'material': 'APA RATED SHEATHING - BOTH SIDES',
            'thickness': '7/16"',
            'fasteners': '8D COMMON (2 1/2" x 0.131" DIA)',
            'max_fas_spacing': '4" OC',
            'blocking': None,
            'holddown_force': 30,
            'wind_shear': 2130
        }))

    # def add_shear_wall(self, )

    def get_shear_wall(self, wind_shear, chord_force, wall_location):
        for wall in self.shear_walls:
            if wall.wind_shear / 2 < wind_shear:
                continue
            else:
                if wall.holddown_force < chord_force:
                    if wall.name in ['2', '5', '7', '9', '11', '13']:
                        print(f'WARNING AT WALL {wall_location} - SW{wall.name} does not have a large enough holddown force')
                    continue
                return wall
        print(f'ERROR AT WALL {wall_location} - There is no wall that satisfies a shear value greater than {wind_shear} and a holddown force greater than {chord_force}')
        return False





        
