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

def get_client(HOST):
    # create and authenticate a client
    if HOST == 'localhost:3000':
        import os
        from dotenv import load_dotenv

        load_dotenv()

        token = os.getenv('token')
        print('token', token)
        client = SpeckleClient(host=HOST, use_ssl=False)
        client.authenticate_with_token(token)
    else:
        client = SpeckleClient(host=HOST)
        account = get_default_account()
        client.authenticate_with_account(account)

    return client

def get_transport(client, STREAM_ID):
    return ServerTransport(STREAM_ID, client)

def get_object(transport, obj_id):
    return operations.receive(obj_id=obj_id, remote_transport=transport)

# def get_latest_commit(client, STREAM_ID):
#     return client.commit.list(STREAM_ID, limit=1)[0]

def get_latest_commit_for_branch(client, STREAM_ID, name):
    branch = client.branch.get(STREAM_ID, name)

    # get the latest commit if globals branch exists
    try:
        latest_commit = branch.commits.items[0]
        return latest_commit
    except:
        print(f'No branch named {name}')
        return Base()

def get_latest_obj(client, transport, STREAM_ID, branch_name='main'):
    branch = client.branch.get(STREAM_ID, branch_name)
    print('branch', branch, branch_name, STREAM_ID)

    # get the latest commit if branch exists
    try:
        latest_commit = branch.commits.items[0]
        print('latest_commit', latest_commit, latest_commit.referencedObject)
        return operations.receive(obj_id=latest_commit.referencedObject, remote_transport=transport)
    except:
        print(f'No branch named {branch_name}')
        return Base()

def create_branch(client, STREAM_ID, name, description = ''):
    client.branch.create(STREAM_ID, name, description)

# def get_globals_obj(client, transport, STREAM_ID):
#     # get the `globals` branch
#     branch = client.branch.get(STREAM_ID, "globals")

#     # get the latest commit if globals branch exists
#     try:
#         latest_commit = branch.commits.items[0]
#     # if the globlas branch doesn't exist, create it and return empty base object
#     except:
#         create_branch(client,STREAM_ID, "globals", "Global Variables")
#         return Base()

#     # receive the globals object
#     return operations.receive(latest_commit.referencedObject, transport)

def send_to_speckle(client, transport, STREAM_ID, obj, branch_name='main', commit_message=''):
    # get the `globals` branch
    branch = client.branch.get(STREAM_ID, branch_name)

    # get the latest commit if globals branch exists
    try:
        latest_commit = branch.commits.items[0]
    # if the globlas branch doesn't exist, create it and return empty base object
    except:
        client.branch.create(STREAM_ID, branch_name, "created automatically by RevDesign")
        # create_branch(client,STREAM_ID, branch_name, "created automatically by RevDesign")

    # TODO this isn't recognizing that the data is already in the server so it's storing multiple copies
    obj_id = operations.send(obj, [transport])

    # now create a commit on that branch with your updated data!
    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        branch_name=branch_name,
        message=commit_message,
    )

    return obj_id

def edit_data_in_obj(obj, data_to_edit):
    '''
    This function expects a dictionary structured as,
    {
        'obj id' : {
            'old_attr': new_value,
            'new_attr': new_value,
        }, 
    }
    '''

    prop_names = obj.get_member_names()
    for name in prop_names:
        try:
            dummy = obj[name]
        except:
            continue
        if isinstance(obj[name], list):
            for obj in obj[name]:
                if obj.id in data_to_edit.keys():
                    for key, value in data_to_edit[obj.id].copy().items():
                        obj[key] = value
                        data_to_edit[obj.id].pop(key)
                        if data_to_edit[obj.id] == {}:
                            data_to_edit.pop(obj.id)
                            if data_to_edit == {}:
                                break

        # not a list
        else:
            if hasattr(obj[name], 'id'):
                if obj[name].id in data_to_edit.keys():
                    for key, value in data_to_edit[obj.id].copy().items():
                        obj[key] = value
                        data_to_edit[obj.id].pop(key)
                        if data_to_edit[obj.id] == {}:
                            data_to_edit.pop(obj.id)
                        if data_to_edit == {}:
                                break
    
    for key, value in data_to_edit.copy().items():
        obj[key] = value
        data_to_edit.pop(key)

    # if isinstance(data_to_add, Base):
    #     if not hasattr(obj, f'@{data_to_add.speckle_type}'):
    #         obj[f'@{data_to_add.speckle_type}'] = data_to_add
    #     elif isinstance(obj[f'@{data_to_add.speckle_type}'], list):
    #         obj[f'@{data_to_add.speckle_type}'].append(data_to_add)
    #     elif isinstance(obj[f'@{data_to_add.speckle_type}'], Base):
    #         temp = obj[f'@{data_to_add.speckle_type}']
    #         obj[f'@{data_to_add.speckle_type}'] = [temp, data_to_add]

    print('DATA TO EDIT', data_to_edit)