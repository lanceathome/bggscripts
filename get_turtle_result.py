from fetch_xml import fetch_xml
import re
import requests
import operator
import sys
from random import random, randint
import math
import time
import datetime
import json

def getLatestCompetition(bearer_token):
   # Download the Golden Turtle list and find the last entry on it
   masterxml = fetch_xml('https://www.boardgamegeek.com/xmlapi/geeklist/51364', bearer_token)

   # We want geeklist/item[-1]/@objectid to find the last competition geeklist/51364
   item = masterxml[-1]
   compid = item.attrib['objectid']
   
   # print(compid)

   # Now get the competition information
   return getCompetitionXml(compid, bearer_token)

def getCompetitionXml(compid, bearer_token):
   compxml = fetch_xml('https://www.boardgamegeek.com/xmlapi/geeklist/{}'.format(compid), bearer_token)
   return compxml;

def getVotesForGame(listitem):
   """Get the voter ids for the entry item.

   Args:
       listitem (int | str): List item id

   Returns:
       list: A list of voter IDs.
   """
   
   all_voters = set()
   
   start_query = f"https://api.geekdo.com/api/listitem/{listitem}/reaction"
   while start_query:
      r = requests.get(start_query)
      r.raise_for_status()
      data = r.json()
      voters = set(data["users"])
      all_voters.update(voters)
      next_link = next(("https://api.geekdo.com" + link["uri"] for link in data["links"] if link["rel"] == "next"), None)
      start_query = next_link
   
   return list(all_voters)

def getVoterName(userid):
   """
   Get the name of a user by their id value.

   Args:
       userid (str | int): Username of the account.

   Returns:
       str: Display name of the user.
   """
   r = requests.get(f"https://api.geekdo.com/api/user/{userid}")
   user_info = r.json()["username"]
   return user_info

def getCompetitionMonth(compxml):
   postdate = compxml.find('postdate')
   datestr = postdate.text
   dt = time.strptime(datestr, '%a, %d %b %Y %H:%M:%S %z')
   return dt

def getCompetitionResults(compxml):
   prog = re.compile(r"\[imageid=(\d+)(\D*)\]", re.IGNORECASE)

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
   with open('config.json') as json_file:
      cookie = json.load(json_file)

   # Get the latest list or a specific one
   if (len(sys.argv) > 1):
      compxml = getCompetitionXml(sys.argv[1], bearer_token=cookie["appToken"])
   else:
      compxml = getLatestCompetition(bearer_token=cookie["appToken"])

   compresults = getCompetitionResults(compxml)

   print(compresults['month'])
   for entry in compresults['results']:
      print("{} scored {} for {}".format(entry[0],entry[2],entry[1]))

   print()
   
   thumber = randint(0, len(compresults['voters'])-1)
   thumber_name = getVoterName(compresults['voters'][thumber])
   print("Random thumber is {} of {}".format(thumber_name, len(compresults['voters']) ))
