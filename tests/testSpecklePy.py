from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base

HOST = "https://speckle.xyz"
STREAM_ID = "218b84525a"
COMMIT_ID = "64d82ca0df"

# create and authenticate a client
client = SpeckleClient(host=HOST)
account = get_default_account()
client.authenticate(token=account.token)

# get the specified commit data
commit = client.commit.get(STREAM_ID, COMMIT_ID)

# create an authenticated server transport from the client and receive the commit obj
transport = ServerTransport(STREAM_ID, client)

print(transport)
res = operations.receive(commit.referencedObject, transport)

print('res\n\n', res)

print(res['@Detail Items'][0].baseLine)

# material = Base.get_registered_type('')()

print(isinstance(res['@Detail Items'][0].baseLine, Base))
res['@Detail Items'][0].baseLine['shear'] = 5
print(res['@Detail Items'][0].baseLine['shear'])

base = Base(data=res['@Detail Items'][0])

obj_id = operations.send(base, [transport])

# now create a commit on that branch with your updated data!
commid_id = client.commit.create(
    STREAM_ID,
    obj_id,
    message="testing123",
)

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
pprint(vars(res))
# get the list of levels from the received object
# levels = res["Element1D"]