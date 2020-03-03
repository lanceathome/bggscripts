from fetch_xml import fetch_xml
import re
import requests
import operator
import sys
from random import random
import math
import time
import datetime

def getLatestCompetition():
   # Download the Golden Turtle list and find the last entry on it
   masterxml = fetch_xml('https://www.boardgamegeek.com/xmlapi/geeklist/51364')

   # We want geeklist/item[-1]/@objectid to find the last competition geeklist/51364
   item = masterxml[-1]
   compid = item.attrib['objectid']
   
   print(compid)

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

def getCompetitionMonth(compxml):
   postdate = compxml.find('postdate')
   datestr = postdate.text
   dt = time.strptime(datestr, '%a, %d %b %Y %H:%M:%S %z')
   return dt

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

      results.append( (username, imageid, votes, listitem) )

      voters = getVotesForGame(listitem)
      allvoters.update(voters)

   # Sort all of the results
   return { "results" : sorted(results, key=operator.itemgetter(2), reverse=True), 
            "voters": list(allvoters),
            "month": time.strftime('%Y-%m-%d', getCompetitionMonth(compxml))}

def getPlaces(results,halloffame):
   # Assume the first row is the current winner (it is if sorted properly)   
   maxVotes = -1
   
   place = 1
   
   rows = []
   for res in results:
      if res[0] not in halloffame:
         # The first entry we accept is the first place - this will exclude any hall of fame members who win the competition
         if maxVotes < 0:
            place = 1
            maxVotes = res[2]
         # If the person we've accepted has less votes than the last person then increase their place
         elif res[2] < maxVotes:
            place = place + 1
            maxVotes = res[2]
            # We only take 1st, 2nd and 3rd. After that abort finding places
            if place > 3:
               break
         
         insRow = (res[0], res[1], res[2], place, res[3])
         rows.append(insRow)
      
   return rows

if __name__ == "__main__":
   # Get the latest list or a specific one
   if (len(sys.argv) > 1):
      compxml = getCompetitionXml(sys.argv[1])
   else:
      compxml = getLatestCompetition()

   compresults = getCompetitionResults(compxml)

   print(compresults['month'])
   for entry in compresults['results']:
      print("{} scored {} for {}".format(entry[0],entry[2],entry[1]))

   print()
   thumber = int( math.floor(random() * (len(compresults['voters'])) ))
   print("Random thumber is {} of {}".format( compresults['voters'][thumber], len(compresults['voters']) ))
