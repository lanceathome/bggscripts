from fetch_xml import fetch_xml
import re
import requests
import operator
import sys
from random import random
import math

def getLatestCompetition():
   # Download the Golden Turtle list and find the last entry on it
   masterxml = fetch_xml('https://www.boardgamegeek.com/xmlapi/geeklist/51364')

   # We want geeklist/item[-1]/@objectid to find the last competition geeklist/51364
   item = masterxml[-1]
   compid = item.attrib['objectid']

   # Now get the competition information
   return getCompetitionXml(compid)

def getCompetitionXml(compid):
   compxml = fetch_xml('https://www.boardgamegeek.com/xmlapi/geeklist/{}'.format(compid))
   return compxml;

def getVotesForGame(listitem):
   query = {'itemtype': 'listitem', 'action':'recspy', 'itemid':listitem}
   r = requests.post("https://boardgamegeek.com/geekrecommend.php", data=query)
   prog = re.compile('>(\w*)</a>')

   voters = set()
   for item in prog.findall(r.text):
      voters.add(item)

   return voters

def getCompetitionResults(compxml):
   prog = re.compile('\[imageid=(\d+)(\D*)\]', re.IGNORECASE)

   allvoters = set()
   results = []

   # Lets get the results from each entry
   for item in compxml.iter('item'):
      listitem = int(item.attrib['id'])
      username = item.attrib['username']
      votes = int(item.attrib['thumbs'])

	  # Search through the body for the first image id
      body = item[0]
      match = prog.search(body.text)
      imageid = int(match.groups()[0])

      results.append( (username, imageid, votes ))

      voters = getVotesForGame(listitem)
      allvoters.update(voters)

   # Sort all of the results
   return { "results" : sorted(results, key=operator.itemgetter(2), reverse=True), "voters": list(voters) }

# Get the latest list or a specific one
if (len(sys.argv) > 1):
   compxml = getCompetitionXml(sys.argv[1])
else:
   compxml = getLatestCompetition()

compresults = getCompetitionResults(compxml)
for entry in compresults['results']:
   print("{} scored {} for {}".format(entry[0],entry[2],entry[1]))

print()
thumber = int( math.floor(random() * (len(compresults['voters'])+1) ))
print("Random thumber is {}".format( compresults['voters'][thumber] ))
