from specklepy.api import operations
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base
from gql import gql

def send_to_speckle(HOST, STREAM_ID, data):

    # create and authenticate a client
    client = SpeckleClient(host=HOST)
    account = get_default_account()
    client.authenticate(token=account.token)
    stream = client.stream.get(id=STREAM_ID)

    # latest_commit = stream.commits.items[0]
    # print('latest_commit', latest_commit)

    if isinstance(data, Base):
        base = data
    else:
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
    # obj_string = transport.copy_object_and_children('0a745e8955895a01c64786e6c93419e5', transport)
    # print('obj_string', obj_string)
    obj_id = operations.send(base, [transport])

    # now create a commit on that branch with your updated data!
    commid_id = client.commit.create(
        STREAM_ID,
        obj_id,
        message="testing123",
    )