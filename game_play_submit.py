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

from dateutil.relativedelta import *

# pip install requests
   
# config requires "bggusername" and "bggpassword", where the password is the session key,
# not the raw password
with open('config.json') as json_file:
  cookie = json.load(json_file)

with open(sys.argv[1], 'r') as stream:
  config = yaml.safe_load(stream)

listid = int(sys.argv[2])


# Default to the last month, or use a custom date
playdate = date.fromisoformat( config['playDate'] + "-01" )
ignorePlayDate = date( playdate.year, playdate.month, 1)
ignorePlayDate = ignorePlayDate+relativedelta(months=-1)
ignorePlayMonth = date(ignorePlayDate.year, ignorePlayDate.month, 1).strftime("%Y-%m")
print ("Dont show plays in {}".format(ignorePlayMonth))

session = requests.Session()

pageUrl = 'https://boardgamegeek.com/geeklist/{}'.format(listid)
url = 'https://boardgamegeek.com/geeklist/item/save'
res = session.get(url, cookies=cookie)
sessionId = session.cookies.get_dict()['SessionID']

gameIndex = 0

# Iterate over each game, submitting an entry (as at this point each game has a play)
for game in config['games']:
  
  gameIndex = gameIndex + 1
  
  # Build the comments
  comments = []
  # Record how many plays occurred
  playSummaryLine = ""
  if game['totalPlays'] > 1:
    playSummaryLine = "{} total plays".format(game['totalPlays'])
  else:
    playSummaryLine = "{} total play".format(game['totalPlays'])
	
  # Add the player count
  if game['numPlayers'] > 1:
    playSummaryLine = "{}, {} players".format(playSummaryLine, game['numPlayers'])
  else:
    playSummaryLine = "{}, 1 player".format(playSummaryLine)
  comments.append(playSummaryLine)

  # Future - show comparison results
  anyModified = False
  
  # The gameId of unplayed games
  unplayedGames = []

  # Show components if more than 1
  comments.append("")
  comments.append("Game plays taken from:")
  for comp in game['components']:
    playLabel = "plays"
    playersLabel = "players"
    if comp['countedPlays'] == 1:
      playLabel = "play"
    if comp['numPlayers'] == 1:
      playersLabel = "player"

    if comp['countedPlays'] > 0:
      # Have I modified the play count, mark it if so
      modified = comp['countedPlays'] != comp['totalPlays']
      anyModified = anyModified | modified
      modifiedLabel = ""
      if modified:
        modifiedLabel = "*"

      viewUrl = "http://www.boardgamegeek.com/plays/thing/{}?date={}".format(comp['gameid'],playdate.strftime("%Y-%m"))
      allUrl = "http://boardgamegeek.com/playsummary/thing/{}".format(comp['gameid'])
      comments.append("  • [thing={}][/thing]: {}{} [url={}]{}[/url] by {} {}    ([url={}]all plays[/url])".format( 
                    comp['gameid'], comp['countedPlays'], modifiedLabel, viewUrl, playLabel, comp['numPlayers'], playersLabel, allUrl))
    else:
      unplayedGames.append(comp['gameid'])

  # List all of the games that weren't played in a single line
  if len(unplayedGames) > 0:
    comments.append("")
    # Convert gameId into the thing string, then join them all by ", " and then replace the last join with the word "and" (if it exists)
    comments.append( "Unplayed game sources " + "] and [".join( ", ".join(map(lambda gameid: "[thing={}][/thing]".format(gameid,), unplayedGames)).rsplit('], [',1)))
  
  # Mark modified entries with a summary of what happened
  if anyModified:
    comments.append("")
    comments.append("[b]* This play count has been modified down[/b]")

  # If this game was played earlier than the last month make a note of that
  
  comments.append("")
  if 'firstPlayed' in game:
    comments.append("First recorded play of this game")
  elif game['mostRecentlyPlayed'][:7] != ignorePlayMonth:
    lastPlayedDate = date.fromisoformat(game['mostRecentlyPlayed'])
    comments.append("Last played in {}".format(lastPlayedDate.strftime("%B, %Y")))

  # If there are any game spider results shown them now
#  linkages = []
#  if len(game['crossplays']) > 0:
    # Sort them by number of plays
#    sortedLinks = sorted(game['crossplays'].items(), key=lambda x:x[1], reverse=True)
#    item['crossplays'].sort(key=lambda cp: cp['players'])

#    comments.append("")
#    comments.append("Number of players also playing:")

#    line = ""
#    lastPlayCount = -1
#    idx = 0
#    for cp in sortedLinks:
#      if cp[1] == lastPlayCount:
#        if idx%2 == 0:
#          line = line + "[i]"
#        line = line + "[thing={}][/thing]".format(cp[0])
#        if idx%2 == 0:
#          line = line + "[/i]"
#        idx = idx+1
#      else:
#        if len(line) > 0:
#          comments.append(line)
#        line = "[b]{}[/b] for [thing={}][/thing]".format(cp[1], cp[0])
#        lastPlayCount = cp[1]
#        idx = 0

#    comments.append(line)

  queryData = {
    "item": {
      "type": "things",
      "id": game['highestPlayed']
    },
    "imageid": None,
    "imageOverridden": False,
    "index": gameIndex,
    "body": "\n".join(comments),
    "rollsEnabled": False
  }
  
  query = json.dumps(queryData)

  url = "https://api.geekdo.com/api/geeklists/{}/listitems".format(listid)
  headers = {'authorization': 'GeekAuth ' + sessionId}
  
  print("POSTing results for {}".format(game['rootname']))

  res = session.post(url, data=query, cookies=cookie, headers=headers)
