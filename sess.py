import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

globalSess = requests.Session()

def GetSession():
    return globalSess
    
def CreateSession():
    
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    globalSess.mount('http://', adapter)
    globalSess.mount('https://', adapter)