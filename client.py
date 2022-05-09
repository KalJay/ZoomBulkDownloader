from zoomus import ZoomClient, util
from datetime import datetime, timedelta
import requests

import jwt


CLIENT_API_KEY = ''
CLIENT_API_SECRET = ''

#If you run into KeyErrors or other errors after a period of time that lines up with the token expiration time consider changing variable below. There are various expressions that can be used from timedelta to fit your use case.
CLIENT_API_TOKEN_EXP = timedelta(days=7) 

#This is used to "Monkey Patch" the zoomus API, as the expiration date on the JSON Web Token is hard-coded to 1 hour. This updates it to 7 days. This was the only solution I could find as refreshing the token did not work.
def generate_jwt(key, secret): 
    header = {"alg": "HS256", "typ": "JWT"}

    payload = {"iss": key, "exp": datetime.now() + CLIENT_API_TOKEN_EXP} #Only change to the API function is here

    token = jwt.encode(payload, secret, algorithm="HS256", headers=header)
    return token

#Creates the Zoom Client object that is used to handle all API calls
def CreateZoomClient():
    global zoom_client
    util.generate_jwt = generate_jwt #Monkey Patching the API for any calls for this script - DOES NOT OVERWRITE THE ACTUAL FILE OF THE LIBRARY, JUST THE RUNTIME OF THE LIBRARY IN MEMORY
    zoom_client  = ZoomClient(CLIENT_API_KEY, CLIENT_API_SECRET) #create a zoom client with the credentials above.