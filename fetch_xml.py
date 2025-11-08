import xml.etree.ElementTree as ET
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Keep trying to get the XML until it returns
# Returns the BGG XML document that has been fetched as converted by ElementTree
# url - The URL to fetch th XML document from
# bearer_token - Token to access the XML data
def fetch_xml(url, bearer_token): 
  # If you hit the server too hard you get bounced for a while, so
  # we have to be nice
  time.sleep(2)
  try:
    headers = {
      "Authorization": f"Bearer {bearer_token}",
    }
    req = Request(url, headers=headers)
    
    #print("Fetch from {}".format(url))
    response = urlopen(req)
  except HTTPError as e:
    # If the server thinks we have been too pushy back off a bit
    if e.code == 429:
      print ("Too many requests by {}".format(url))
      time.sleep(30)
      return fetch_xml(url, bearer_token=bearer_token)
    else:
      raise e
  except URLError as t:
    print("Network error")
    time.sleep(30)
    return fetch_xml(url, bearer_token=bearer_token)
  
  xml = response.read()
  # Work around for a bug where character 11 was included but XML parsing couldn't handle it
  #xml = str(xml,"UTF-8")
  #xml = xml.replace("\x0b", " ")
  try:
    root = ET.fromstring(xml)
    if root.tag == 'message':
      print ("Received wait request for {}".format(url))
      time.sleep(5)
      return fetch_xml(url, bearer_token=bearer_token)

  except xml.etree.ElementTree.ParseError:
    print("Couldn't read from url {}".format(url))
    raise
    
  return root