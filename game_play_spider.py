import calendar
import xml.etree.ElementTree as ET
import sys
from datetime import date, timedelta
import datetime
import json
import time
import yaml
import math
from urllib.request import urlopen
from urllib.error import HTTPError
import requests

# pip install requests
   
# config requires "bggusername" and "bggpassword", where the password is the session key,
# not the raw password
with open('config.json') as json_file:
  cookie = json.load(json_file)

with open(sys.argv[1], 'r') as stream:
  config = yaml.safe_load(stream)

listid = int(sys.argv[2])

playdate = date.fromisoformat( config['playDate'] + "-01" )


# Keep trying to get the XML until it returns
# url - The URL to fetch the XML document from
def fetch_xml(url): 
  # If you hit the server too hard you get bounced for a while, so
  # we have to be nice
  time.sleep(1)
  try:
    response = urlopen(url)
  except HTTPError as e:
    # If the server thinks we have been too pushy back off a bit
    if e.code == 429:
      print ("Too many requests by {}".format(url))
      time.sleep(30)
      return fetch_xml(url)
    else:
      raise e

  xml = response.read()
  try:
    root = ET.fromstring(xml)
    if root.tag == 'message':
      print ("Received wait request for {}".format(url))
      time.sleep(5)
      return fetch_xml(url)

  except xml.etree.ElementTree.ParseError:
    sys.stderr.write("Couldn't read %s" % (xml,))
    raise
    
  return root
  
# Get the details of the list  
url = "https://www.boardgamegeek.com/xmlapi/geeklist/{}".format(listid)
xml = fetch_xml(url)

session = requests.Session()

# Get the items so we can fill in the spider links
listitems = []
listKeys = {}
for listelement in xml.iter('item'):
  listitem = {}
  listitem['listid'] = int(listelement.attrib['id'])
  listitem['objectid'] = int(listelement.attrib['objectid'])
  listitem['objectname'] = listelement.attrib['objectname']
  listitem['comment'] = listelement.findtext('body')
  listitems.append(listitem)
  listKeys[int(listelement.attrib['id'])] = listitem

# Oldest play tracking - we keep a list of games that are oldest incase there is a shared date
oldestPlay = config['playDate']
# Fill with a list of tuples (listitemid, gamename)
oldestGames = []
# Fill with a list of tuples (listitem,gamename)
firstGames = []

gamelist = config['games']

# Build a map of list item  index to game id
itemGameIds = []
for game in gamelist:
  itemGameIds.append(game['rootid'])

# We want gameid to (game name, listitem id, list item object id)
gameToList = {}
for idx,game in enumerate(gamelist):
  gameToList[game['rootid']] = ( game['rootname'], listitems[idx]['listid'], listitems[idx]['objectid'] )

for idx,game in enumerate(gamelist):

  itemid = gameToList[game['rootid']][1]
  item = listKeys[itemid]
	
  # Is this the oldest play found
  if 'mostRecentlyPlayed' in game:
    gameLastPlayed = date.fromisoformat(game['mostRecentlyPlayed']).strftime("%Y-%m")
    if gameLastPlayed == oldestPlay:
      oldestGames.append((itemid,game['rootname']))
    elif gameLastPlayed < oldestPlay:
      oldestPlay = gameLastPlayed
      oldestGames.clear()
      oldestGames.append((itemid,game['rootname']))
  elif 'firstPlayed' in game:
    firstGames.append((itemid, game['rootname']))

  # If there are any game spider results shown them now
  linkages = []
  if len(game['crossplays']) > 0:
  
    # Sort them by number of plays
    sortedLinks = sorted(game['crossplays'].items(), key=lambda x:x[1], reverse=True)

    comments = []
    comments.append("")
    comments.append("Number of players also playing:")

    line = []
    lastPlayCount = -1
    idx = 0
    for cp in sortedLinks:
      listgamename = gameToList[cp[0]][0]
      listitemid = gameToList[cp[0]][1]

      if cp[1] == lastPlayCount:
        linebit = ""
        if idx%2 == 0:
          linebit = linebit + "[i]"
        linebit = linebit + "[listitem={}]{}[/listitem]".format(listitemid,listgamename)
        if idx%2 == 0:
          linebit = linebit + "[/i]"
        line.append(linebit)
        idx = idx+1
      else:
        # Add the last tallied plays line to the comments then reset for the new group
        if len(line) > 0:
          comments.append(", ".join(line))
        line.clear()

        line.append( "[b]{}[/b] for [listitem={}]{}[/listitem]".format(cp[1],listitemid,listgamename))
        lastPlayCount = cp[1]
        idx = 0

    comments.append(", ".join(line))    

    query = {'itemid': itemid, 'listid':listid, 'action':'save','objecttype':'thing',
           'objectid': game['highestPlayed'], 'comments': item['comment']+"\n"+"\n".join(comments)}

    url = 'https://boardgamegeek.com/geeklist/item/save'
    print("POSTing results for {}".format(game['rootname']))
    res = session.post(url, data=query, cookies=cookie)
    #print(query)

commentAdd = []


if len(firstGames) > 0:
  firstPlays = "First recorded play for "
  firstPlayEntry = ["[listitem={}]{}[/listitem]".format(fgame[0],fgame[1]) for fgame in firstGames]
  firstPlays = firstPlays + ", ".join(firstPlayEntry) + "."
  commentAdd.append("")
  commentAdd.append(firstPlays)

# If the oldest play isn't this month
if oldestPlay != config['playDate']:
  oldplayDate = date.fromisoformat(oldestPlay+"-01")
  oldPlays = "Longest time between plays go to "
  oldPlayEntry = ["[listitem={}]{}[/listitem]".format(oldGame[0],oldGame[1]) for oldGame in oldestGames]
  oldPlays = oldPlays + ", ".join(oldPlayEntry) + " from " + oldplayDate.strftime("%B, %Y") + "."
  commentAdd.append("")
  commentAdd.append(oldPlays)

# Modify the description  
if len(commentAdd) > 0:
  print("\n".join(commentAdd))
