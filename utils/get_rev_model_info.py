
def get_gbs():
    gb_cl = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType()
    wall_cl = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    gbs = []
    walls = []
    cols = []
    for el in gb_cl:
        if str(el.StructuralMaterialType).lower() == 'concrete':
            if str(el.StructuralType).lower() == 'beam':
                gbs.append(el)
            elif str(el.StructuralType).lower() == 'column':
                cols.append(el)
    for el in wall_cl:
        if str(el.StructuralUsage).lower() == 'bearing':
            walls.append(el)

    #Set the file path
    filepath = 'C:/Users/civy/Desktop/revit_output.txt'
    
    #Delete the file if it exists.
    if (System.IO.File.Exists(filepath) == True):
        System.IO.File.Delete(filepath)
    
    #Create the file
    file = System.IO.StreamWriter(filepath)
    
    #Write some things to the file
    for el in gbs:
        start_loc = el.Location.Curve.GetEndPoint(0).ToString()
        end_loc = el.Location.Curve.GetEndPoint(1).ToString()
        width_param = el.LookupParameter('Beam Width')
        depth_param = el.LookupParameter('Beam Depth')
        if width_param:
            width = width_param.AsDouble()
        else:
            width = .25
        if depth_param:
            depth = depth_param.AsDouble()
        else:
            depth = .25

        file.WriteLine('%s %s %f %f' %(start_loc, end_loc, width, depth))

    for el in walls:
        start_loc = el.Location.Curve.GetEndPoint(0).ToString()
        end_loc = el.Location.Curve.GetEndPoint(1).ToString()
        width_param = el.Width
        depth_param = el.LookupParameter('Unconnected Height')
        if width_param:
            width = width_param
        else:
            width = .25
        if depth_param:
            depth = depth_param.AsDouble()
        else:
            depth = .25

        file.WriteLine('%s %s %f %f' %(start_loc, end_loc, width, depth))
    
    #Close the StreamWriter
    file.Close()


    # # VERY USEFUL CODE TO FIND PARAMETERS OF ELEMENTS IN REVIT
    # for param in el.Parameters:
    #     print(param.Definition.Name)

    # h = el.GetParameters('Depth')
    # print(h[0].AsDouble())

import System
def classify_selected_elements():
    #Set the file path
    filepath = 'C:/Users/civy/Music/revit_output.txt'
    
    #Delete the file if it exists.
    if (System.IO.File.Exists(filepath) == True):
        System.IO.File.Delete(filepath)

    file = System.IO.StreamWriter(filepath)

    num_elements = len(selection)
    for idx in range(num_elements):
        el = gdict['e{}'.format(idx+1)]
        element = {}

        try:
            usage = str(el.StructuralType).lower()
        except:
            print('continue')
            continue

        element['id'] = str(el.UniqueId)
        element['type'] = usage

        location = el.Location.ToString()
        if location == 'Autodesk.Revit.DB.LocationCurve':
            element['x1'], element['y1'], element['z1'] = location_to_attributes(el.Location.Curve.GetEndPoint(0).ToString())
            element['x2'], element['y2'], element['z2'] = location_to_attributes(el.Location.Curve.GetEndPoint(1).ToString())
            print(usage)


        elif location == 'Autodesk.Revit.DB.LocationPoint':
            loc = el.Location.Point.ToString()
            continue

        elif location == 'Autodesk.Revit.DB.Location':
            loc = el.Location.Point.ToString()
            continue

        # if usage == 'beam':
        #         gbs.append(el)
        # elif usage == 'column':
        #         cols.append(el)
        # elif usage == 'footing':

        # elif usage == 'brace':

        x = Element(**element)
        file.WriteLine('%f,%f,%f,%f,%f,%f' %(x.x1, x.y1, x.z1, x.x2, x.y2, x.z2))
    file.Close()

def location_to_attributes(string):
    # given string in this format, '(x, y, z)', return float(x), float(y), float(z)
    string = string.split(',')
    coords = []
    for coord in string:
        coords.append(replace_non_nums(coord))

    return float(coords[0]), float(coords[1]), float(coords[2])

def replace_non_nums(string):
    acceptable_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-']
    new_char = ''
    for char in string:
        if char in acceptable_chars:
            new_char += char
    return new_char

        
class Element:
    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
                setattr(self, k, v)


        