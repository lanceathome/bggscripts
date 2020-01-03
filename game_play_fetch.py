#!/usr/bin/python

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

from dateutil.relativedelta import *

# pip install pyyaml
# pip install python-dateutil

# May throw yaml.YAMLError
def load_expansion_list(file):
  with open(file, 'r') as stream:
    return yaml.safe_load(stream)

# Keep trying to get the XML until it returns
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

# Get a map of game rootids to a game entry.
# The game entry is just the name and root id at this time
# geeklist - Id of geeklist
# expansions - Set of games in expansions. Games in expansions aren't added to the games list.
def fetch_games(geeklist,expansions):

  url = 'https://www.boardgamegeek.com/xmlapi/geeklist/%d' % (geeklist,)
  xml = fetch_xml(url)

  games = {}

  for item in xml.iter('item'):
    rootid = int(item.attrib['objectid'])
    if rootid not in expansions:
      gameEntry = { 'rootname': item.attrib['objectname'],
                    'rootid': rootid }    
      games[rootid] = gameEntry
    else:
      print("Skipping sub-item {} {}".format(rootid,item.attrib['objectname']))

  return games


# Game plays include the name in the item section, so maybe we can remove this pass and
# get the names later
# games - Map of games by rootid to their game entry
# expansions - Map of expansions by rootid to their components
def build_games_sources(games,expansions):

  for rootid,gentry in games.items():
    # The root game always makes an entry, add any expansions that are found for it
    components = [rootid]

    if rootid in expansions:
      components = components + expansions[rootid]

    # We fetch the name when we get the plays
    compDetails = []
    for comp in components:
      compDetail = { 'gameid': comp }
      compDetails.append(compDetail)

    gentry['components'] = compDetails

#    gameidurl = ["{}".format(c) for c in components]
#    url = "https://www.boardgamegeek.com/xmlapi/boardgame/{}".format(",".join(gameidurl))
#    print(url)
#    boardgames = fetch_xml(url)

#    compDetails = []
#    for boardgame in boardgames.iter('boardgame'):
#      gameInfo = { 'gameid': boardgame.attrib['objectid'],
#                   'gamename': boardgame.find("name[@primary='true']").text }
#      compDetails.append(gameInfo)


# Add the game players, last played date and any play information 
# gameEntry - A component of a game to fill in the details
def fill_plays(gameEntry,startDate,endDate,filterCount):
  urlformat = "https://www.boardgamegeek.com/xmlapi2/plays?id={}&mindate={}&maxdate={}&page={}"
  url = urlformat.format(gameEntry['gameid'],startDate.isoformat(),endDate.isoformat(),1)

  plays = fetch_xml(url)
  # Number of play entries, not total play count
  totalPlays = int(plays.attrib['total'])
  originalPlays = 0
  countedPlays = 0
  players = set()
  questionablePlays = []

  if totalPlays > 0:
    numPages = math.ceil(int(totalPlays)/100.0)
    page = 1

    # Note game components with no plays don't have a name set,
    # but that is okay as the viewing code doesn't use the name directly
    # and we only use names of components that have been played so will have a name
    # entry
    gamename = plays.find('play/item').attrib['name']
    gameEntry['gamename'] = gamename

    while page <= numPages:
      # Fetch new data for the subsequent pages 
      if page > 1:
        url = urlformat.format(gameEntry['gameid'],startDate.isoformat(),endDate.isoformat(),page)
        plays = fetch_xml(url)

      # Extract the play information
      for play in plays.iter('play'):
        numPlays = int(play.attrib['quantity'])
        originalPlays = originalPlays + numPlays
        countedPlays = countedPlays + numPlays

        # The user must approve 
        if numPlays > filterCount:
          playcomment = play.findtext("comments","NO COMMENT")
          playuser = play.attrib['userid']
          playdate = play.attrib['date']
          questionablePlays.append( { 'plays': numPlays, 
                                      'user': playuser,
                                      'date': playdate,
                                      'comment': playcomment } )

        # Get all of the unique players. There is one recorded for the play registration,
        # and optionally other players listed
        players.add(int(play.attrib['userid']))
        for player in play.findall('players/player'):
          if len(player.attrib['username']) > 0:
            players.add(int(player.attrib['userid']))
      
      page = page+1

    # Now we have to find the last recorded play. Luckily the plays are returned in
    # descending order so the first entry is the one we want to check
    playToDate = startDate  - timedelta(days=1)
    url = "https://www.boardgamegeek.com/xmlapi2/plays?id={}&maxdate={}".format(gameEntry['gameid'],playToDate.isoformat())
    lastPlays = fetch_xml(url)
    if int(lastPlays.attrib['total']) == 0:
      gameEntry['firstPlayed'] = True
    else:
      if lastPlays.find('play').attrib['date'] != '0000-00-00':
        gameEntry['lastPlayed'] = lastPlays.find('play').attrib['date']
      else:
        gameEntry['firstPlayed'] = True
        
  # Record the play information
  gameEntry['totalPlays'] = originalPlays
  gameEntry['countedPlays'] = countedPlays
  gameEntry['players'] = players
  gameEntry['numPlayers'] = len(players)
  gameEntry['questionablePlays'] = questionablePlays  

def filter_plays(gameEntry):
  # Step over each component
  for component in gameEntry['components']:
    # If there are questionable games put them to the user
    for question in component['questionablePlays']:
      # If the user wants to remove them adjust the countedPlays down     
      print("{} of {} on {}, {}".format( question['plays'], 
                                                  component['gamename'],
                                                  question['date'],
                                                  question['comment']))
      answer = input("    Replace with 1 play? (y/n)[y] ")
      if answer == "y" or len(answer) == 0:
        removePlays = question['plays'] - 1
        component['countedPlays'] = component['countedPlays'] - removePlays;

    # We don't need this data anymore
    del component['questionablePlays']


def summarise_plays(gameTotalEntry):
  allplayers = set()

  highestPlays = 0
  totalPlays = 0

  mostRecentPlay = ''

  for comp in game['components']:
    totalPlays = totalPlays + comp['countedPlays']
    allplayers |= comp['players']
    # We don't need this data per game component in the long run
    del comp['players']

    if comp['countedPlays'] > 0:
      # Is this the biggest played game component
      if comp['countedPlays'] > highestPlays:
        highestPlays = comp['countedPlays']
        gameTotalEntry['highestPlayed'] = comp['gameid']
      # We also need to copy first play and last played summary
      if 'lastPlayed' in comp:
        if comp['lastPlayed'] > mostRecentPlay:
          mostRecentPlay = comp['lastPlayed']

  gameTotalEntry['players'] = allplayers;
  gameTotalEntry['numPlayers'] = len(allplayers)
  
  if len(mostRecentPlay) > 0:
    gameTotalEntry['mostRecentlyPlayed'] = mostRecentPlay
  else:
    # This is implied with mostRecentlyPlayed not being available, but set it
    # to make it easier to see in the data
    gameTotalEntry['firstPlayed'] = True

  gameTotalEntry['totalPlays'] = totalPlays

def spider_games(allgames):
  for game in allgames:
    spider = {}
    for matchgame in allgames:
      if matchgame['rootid'] != game['rootid']:
        # Are there any overlapping players
        overlap = len(game['players'] & matchgame['players'])
        if overlap > 0:
          spider[matchgame['rootid']] = overlap;

    game['crossplays'] = spider;

  for game in allgames:
    del game['players']

# Get the user parameters
# 1 - File with expansions
# 2 - Date (optional, current month if not set)
# 3 - Output file (optional, config file set if not set)

configuration = load_expansion_list(sys.argv[1])

# Default to the last month, or use a custom date
capturedate = date( date.today().year, date.today().month, 1)
capturedate = capturedate+relativedelta(months=-1)
if len(sys.argv) > 2:
  capturedate = date.fromisoformat( sys.argv[2] + "-01" )

# If we are setting a date we may want a custom output too
if len(sys.argv) > 3:
  outfile = sys.argv[3]
elif 'outfile' in configuration:
  outfile = configuration['outfile'].format(capturedate.strftime("%Y-%m")) 
else:
  outfile = "plays-{}.yaml".format(capturedate.strftime("%Y-%m")) 
  
expansions = configuration['expansions']

# Get the set of expansions needed when fetching games to prevent duplicates
expansionComponents = set()
for expansionEntry in expansions.values():
  expansionComponents |= set(expansionEntry)

# Join our two source lists 
sourceLists = configuration['sourceLists']
allgames = {}
for listid in sourceLists:
  allgames.update(fetch_games(listid,expansionComponents))

# This list is too big to test initially, just grab first 40
#testingGames = {}
#for game in list(allgames.values())[:20]:
#  testingGames[game['rootid']] = game
#allgames = testingGames

# Get the games and components merged
build_games_sources(allgames,expansions)

# Go through the games to get their component play counts
playsFrom = date(capturedate.year, capturedate.month, 1)
playsTo = date(capturedate.year, capturedate.month, 1) + relativedelta(day=31)

for idx,game in enumerate(allgames.values()):
  print("Filling game {}, {:.2f}%".format(game['rootname'],(idx/len(allgames))*100))
  for comp in game['components']:
    fill_plays(comp,playsFrom,playsTo,configuration['filter'])

# Second pass to remove duplicates and the prepare game summaries
for game in allgames.values():
  filter_plays(game)
  summarise_plays(game)


# Strip all of the game entries which weren't played
playedAllGames = []
for game in allgames.values():
  if game['totalPlays'] > 0:
    playedAllGames.append(game)

# Order by plays, then players, then name. Sort is ascending, so we make the numbers negative so the biggest 
# play is the smallest sorting number, then the same for the number players and then alphabetical in normal
# sorting order
sortedGames = sorted(playedAllGames, key=lambda sg: (-sg['totalPlays'],-sg['numPlayers'],sg['rootname']))
spider_games(sortedGames)

outdate = {
  'playDate': capturedate.strftime("%Y-%m"),
  'games': sortedGames
}

print("Writing results to {}".format(outfile))
f = open(outfile, "w")
f.write(yaml.dump(outdate))
f.close()

# Testing output
#for game in sortedGames:
#  print(game['rootname'], game['totalPlays'], game['numPlayers'])
#  if len(game['components']) > 1:
#    for comp in game['components']:
#      if comp['countedPlays'] > 0:
#        print ("     ", comp['gamename'], comp['countedPlays'], comp['numPlayers'])

#print(yaml.dump(playedAllGames))
#print(playedAllGames)
