import xml.etree.ElementTree as ET
import time
from urllib.request import urlopen
from urllib.error import HTTPError

# Keep trying to get the XML until it returns
# Returns the BGG XML document that has been fetched as converted by ElementTree
# url - The URL to fetch the XML document from
def fetch_xml(url): 
  # If you hit the server too hard you get bounced for a while, so
  # we have to be nice
  time.sleep(2)
  try:
    #print("Fetch from {}".format(url))
    response = urlopen(url)
  except HTTPError as e:
    # If the server thinks we have been too pushy back off a bit
    if e.code == 429:
      print ("Too many requests by {}".format(url))
      time.sleep(30)
      return fetch_xml(url)
    else:
      raise e
  except urllib.error.URLError as t:
    print("Network error")
    time.sleep(30)
    return fetch_xml(url)
  
  xml = response.read()
  # Work around for a bug where character 11 was included but XML parsing couldn't handle it
  #xml = str(xml,"UTF-8")
  #xml = xml.replace("\x0b", " ")
  try:
    root = ET.fromstring(xml)
    if root.tag == 'message':
      print ("Received wait request for {}".format(url))
      time.sleep(5)
      return fetch_xml(url)

  except xml.etree.ElementTree.ParseError:
    print("Couldn't read from url {}".format(url))
    raise
    
  return root