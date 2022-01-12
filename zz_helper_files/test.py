import sqlite3

def test():
    con = sqlite3.connect('C:/Users/civy/Music/GitHub/RevDesign/db.sqlite3')
    cur = con.cursor()
    model_member = cur.execute('SELECT * FROM model_Member WHERE id = ? LIMIT 1', ('11111',))
    print('MM', model_member)

def linkRevitWithDB():
    '''
        DATABASE STRUCTURE

        Member - id, type, node1, node2, modified

        node - id, display_id, x, y, z

    '''
    print('program start')
    con = sqlite3.connect('C:/Users/civy/Music/GitHub/RevDesign/db.sqlite3')

    try:
        cur = con.cursor()
        print('curser created')

        node1_index = 2
        node2_index = 3
        tolerance = .0001

        num_elements = len(selection)
        for index in range(num_elements):
            print(index)
            el = gdict['e{}'.format(index+1)]
            element = {}

            try:
                usage = str(el.StructuralType).lower()
            except:
                print('No structural type defined')
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

            else:
                continue

            # if the program has made it to this point then el is a structural member
            model_member = cur.execute('SELECT * FROM model_Member WHERE id = ? LIMIT 1',(str(el.UniqueId),)).fetchone()

            # check if nodes exist
            x1,y1,z1 = location_to_attributes(el.Location.Curve.GetEndPoint(0).ToString())
            x2,y2,z2 = location_to_attributes(el.Location.Curve.GetEndPoint(1).ToString())

            node1 = cur.execute('SELECT * FROM model_node WHERE ABS(x-:x1) < :tolerance AND ABS(y-:y1) < :tolerance AND ABS(z-:z1) < :tolerance LIMIT 1',{'tolerance':tolerance, 'x1':x1, 'y1':y1, 'z1':z1}).fetchone()
            node2 = cur.execute('SELECT * FROM model_node WHERE ABS(x-:x2) < :tolerance AND ABS(y-:y2) < :tolerance AND ABS(z-:z2) < :tolerance LIMIT 1',{'tolerance':tolerance, 'x2':x2, 'y2':y2, 'z2':z2}).fetchone()

            if node1:
                print('node1 exists')
                # turn tuple of single record into single record
                node1_id = node1[0]

            else:
                print('node1 DNE')
                # if there isn't already a node with these coordinates in the database, create one
                query = (   
                    'INSERT INTO model_node (display_id,x,y,z)'
                    'VALUES (0,?,?,?)'  
                )
                cur.execute(query,(str(x1),str(y1),str(z1)))
                id_tuple = cur.execute('SELECT LAST_INSERT_ROWID();').fetchone()
                node1_id = id_tuple[0]

            if node2:
                print('node2 exists')
                # turn tuple of single record into single record
                node2_id = node2[0]

            else:
                print('node2 DNE')
                # if there isn't already a node with these coordinates in the database, create one
                query = (   
                    'INSERT INTO model_node (display_id,x,y,z)'
                    'VALUES (0,?,?,?)' 
                )
                cur.execute(query,(str(x2),str(y2),str(z2)) )
                id_tuple = cur.execute('SELECT LAST_INSERT_ROWID();').fetchone()
                node2_id = id_tuple[0]

            # if there isn't already a member with this ID in the database, create one
            if not model_member:
                print('member DNE')
                # check if there is a 'new' member that has the same nodes


                cur.execute('INSERT INTO model_Member (id,type,node1_id,node2_id) VALUES (?,?,?,?)',(str(el.UniqueId), str(usage), str(node1_id), str(node2_id)))

            else:
                print('member exists')
                # cols = cur.execute("PRAGMA table_info(model_Member)")
                # print('COLS',cols.fetchall())
                print(node1_id)
                if not (node1_id == model_member[node1_index]): # would cause beam to seem 'new' if it were just flipped where node1=node2 and vice versa 
                    query = (   
                        'UPDATE model_Member'
                        'SET new_node1_id = ?'
                        'WHERE id = ?'
                    )
                    cur.execute(query, (str(node1_id), str(model_member[0])))
                if not (node2_id == model_member[node2_index]): 
                    query = (   
                        'UPDATE model_Member'
                        'SET new_node2_id = ?'
                        'WHERE id = ?'
                    )
                    cur.execute(query, (str(node2_id), str(model_member[0])))
        con.commit()

    except Exception as e: 
        print('ERROR',str(e))

    cur.close()
    con.close()
        

# given string in this format, '(x, y, z)', return float(x), float(y), float(z)
def location_to_attributes(string):
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


linkRevitWithDB()

# Useful code for finding info about DB
# cols = cur.execute("PRAGMA table_info(model_Member)")
# print('COLS',cols.fetchall())