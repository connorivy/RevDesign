from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning
from specklepy.transports.abstract_transport import AbstractTransport
import json

def edit_object(transport, data):
    '''
    This function expects a dictionary structured as,
    {
        'obj id' : {
            'old_attr': new_value,
            'new_attr': new_value,
        }, 
    }
    '''

def send_to_speckle(HOST, STREAM_ID, data_to_add = None, data_to_replace = None):
    '''
    This function expects a dictionary structured as,
    {
        'obj id' : {
            'old_attr': new_value,
            'new_attr': new_value,
        }, 
    }
    '''

    data_to_replace = {
        '5b5b287daa98a81794f684b0ed3e9918' : {
            'area': 50,
            'new_attr': 'butts',
        }, 
        'cd93735e7cf5d00c15a2e9ef7d25d1fb' : {
            'SpeckMesh' : 'mesh'
        }
    }

    # create and authenticate a client
    client = SpeckleClient(host=HOST)
    account = get_default_account()
    client.authenticate(token=account.token)
    # stream = client.stream.get(id=STREAM_ID)

    transport = ServerTransport(STREAM_ID, client)

    # TODO - get branch that the user is working on and only commit to that branch
    latest_commit = client.commit.list(STREAM_ID, limit=1)[0]
    print('latest_commit', latest_commit.referencedObject)

    latest_commit_obj = operations.receive(obj_id=latest_commit.referencedObject, remote_transport=transport)

    # if isinstance(data_to_add, Base):
    #     if not hasattr(latest_commit_obj, f'@{data_to_add.speckle_type}'):
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'] = data_to_add
    #     elif isinstance(latest_commit_obj[f'@{data_to_add.speckle_type}'], list):
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'].append(data_to_add)
    #     else:
    #         temp = latest_commit_obj[f'@{data_to_add.speckle_type}']
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'] = [temp, data_to_add]

    # loop through all ids of latest_commit_obj
    # traverse_json(latest_commit_obj)
    

    prop_names = latest_commit_obj.get_member_names()
    print(latest_commit_obj)
    for name in prop_names:
        print(name)
        try:
            print(latest_commit_obj[name])
        except:
            continue
        if isinstance(latest_commit_obj[name], list):
            for obj in latest_commit_obj[name]:
                if obj.id in data_to_replace.keys():
                    print('OBJ ID', data_to_replace[obj.id])
                    for key, value in data_to_replace[obj.id].copy().items():
                        obj[key] = value
                        data_to_replace[obj.id].pop(key)
                        if data_to_replace[obj.id] == {}:
                            data_to_replace.pop(obj.id)
                        print(isinstance(obj, Base))

        # not a list
        else:
            if hasattr(latest_commit_obj[name], 'id'):
                if latest_commit_obj[name].id in data_to_replace.keys():
                    print('OBJ ID', data_to_replace[obj.id])
                    for key, value in data_to_replace[obj.id].copy().items():
                        obj[key] = value
                        data_to_replace[obj.id].pop(key)
                        if data_to_replace[obj.id] == {}:
                            data_to_replace.pop(obj.id)
                        print(obj.area)

    # print(dir(latest_commit_obj))

    # if isinstance(data, Base):
    #     base = data
    # else:
    #     base = Base(data=data)
    print(latest_commit_obj, isinstance(latest_commit_obj, Base))

    # from pprint import pprint

    # for key, value in vars(res['@Analytical Nodes'][5]).items():
    #     print(key, value)

    #     try:
    #         if vars(value):
    #             print('\n\n')
    #             print(vars(value))
    #             print('\n\n')
    #     except:
    #         continue
    # pprint(vars(base))
    
    # print('transport url', transport.url)
    # get_obj_ids_in_stream(transport)
    # obj_string = transport.copy_object_and_children('0a745e8955895a01c64786e6c93419e5', transport)
    # print('obj_string', obj_string)
    obj_id = operations.send(latest_commit_obj, [transport])

    # now create a commit on that branch with your updated data!
    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        message="testing123",
    )

def get_obj_ids_in_stream(transport):
    # Get the new children
        endpoint = f"{transport.url}/api/getobjects/{transport.stream_id}"
        r = transport.session.post(
            endpoint, data={'objects': ''}, stream=True
        )
        r.encoding = "utf-8"
        lines = r.iter_lines(decode_unicode=True)

        # iter through returned objects saving them as we go
        for line in lines:
            if line:
                print(line)
                # hash, obj = line.split("\t")
                # print('HASH, OBJ, ', hash, obj)