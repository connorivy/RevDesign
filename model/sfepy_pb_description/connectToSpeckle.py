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

def get_client(HOST, STREAM_ID):
    # create and authenticate a client
    client = SpeckleClient(host=HOST)
    account = get_default_account()
    client.authenticate(token=account.token)

    return client

def get_transport(client, STREAM_ID):
    return ServerTransport(STREAM_ID, client)

def get_object(transport, obj_id):
    return operations.receive(obj_id=obj_id, remote_transport=transport)

def get_latest_commit(client, STREAM_ID):
    return client.commit.list(STREAM_ID, limit=1)[0]

def send_to_speckle(client, transport, STREAM_ID, data_to_replace = None, data_to_add = None, commit_message=''):
    '''
    This function expects a dictionary structured as,
    {
        'obj id' : {
            'old_attr': new_value,
            'new_attr': new_value,
        }, 
    }
    '''
    # TODO - get branch that the user is working on and only commit to that branch
    latest_commit = get_latest_commit(client, STREAM_ID)
    latest_commit_obj = get_object(transport, latest_commit.referencedObject)

    # if isinstance(data_to_add, Base):
    #     if not hasattr(latest_commit_obj, f'@{data_to_add.speckle_type}'):
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'] = data_to_add
    #     elif isinstance(latest_commit_obj[f'@{data_to_add.speckle_type}'], list):
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'].append(data_to_add)
    #     else:
    #         temp = latest_commit_obj[f'@{data_to_add.speckle_type}']
    #         latest_commit_obj[f'@{data_to_add.speckle_type}'] = [temp, data_to_add]

    prop_names = latest_commit_obj.get_member_names()
    for name in prop_names:
        try:
            dummy = latest_commit_obj[name]
        except:
            continue
        if isinstance(latest_commit_obj[name], list):
            for obj in latest_commit_obj[name]:
                if obj.id in data_to_replace.keys():
                    for key, value in data_to_replace[obj.id].copy().items():
                        obj[key] = value
                        data_to_replace[obj.id].pop(key)
                        if data_to_replace[obj.id] == {}:
                            data_to_replace.pop(obj.id)
                            if data_to_replace == {}:
                                break

        # not a list
        else:
            if hasattr(latest_commit_obj[name], 'id'):
                if latest_commit_obj[name].id in data_to_replace.keys():
                    for key, value in data_to_replace[obj.id].copy().items():
                        obj[key] = value
                        data_to_replace[obj.id].pop(key)
                        if data_to_replace[obj.id] == {}:
                            data_to_replace.pop(obj.id)
                        if data_to_replace == {}:
                                break

    # TODO this isn't recognizing that the data is already in the server so it's storing multiple copies
    obj_id = operations.send(latest_commit_obj, [transport])

    # now create a commit on that branch with your updated data!
    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        message=commit_message,
    )

def send_to_speckle(client, transport, STREAM_ID):

    latest_commit = get_latest_commit(client, STREAM_ID)
    latest_commit_obj = get_object(transport, latest_commit.referencedObject)

    obj_id = operations.send(latest_commit_obj, [transport])

    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        message='same objects, right?',
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