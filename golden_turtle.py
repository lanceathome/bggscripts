import sqlite3
from fetch_xml import fetch_xml
import re
import requests
import operator
import sys
from random import random
import math
import get_turtle_result
import store_turtle_result
import show_turtle_result
# pip install Mako
# from mako.template import Template

# Get the latest list or a specific one
if (len(sys.argv) > 1):
   compxml = get_turtle_result.getCompetitionXml(sys.argv[1])
else:
   compxml = get_turtle_result.getLatestCompetition()

# Save the information in the database
conn = sqlite3.connect('goldenTurtle.db')
c = conn.cursor()

# Get the competition information
compresults = get_turtle_result.getCompetitionResults(compxml)
hallOfFamers = store_turtle_result.getHallOfFame(c)
winners = get_turtle_result.getPlaces(compresults['results'],hallOfFamers)
# Find who the random thumber is
thumber = int( math.floor(random() * len(compresults['voters'])))

# Save the information
store_turtle_result.addResult(c,compresults['month'],compresults['results'],winners)
store_turtle_result.addThumber(c,compresults['month'],compresults['voters'][thumber], len(compresults['voters']))

# Ask the user which entries should win the encouragement award
encourage = store_turtle_result.getEncourageRecommendation(c,compresults['month'])
print("    {:<15} #Enter #Enc Votes Image Entry".format("User"))
for idx, enc in enumerate(encourage):
   print("#{:<2} {:<15} {:>6} {:>4} {:>5} https://boardgamegeek.com/image/{}/ {}".format(idx,enc[0],enc[1],enc[2],enc[3],enc[4],enc[5])) 

print("Enter selected encouragement places (comma to separate):")
selection = str(input()).split(',')
# Make sure the user made a selection before processing it
if len(selection) > 0 and len(selection[0]) > 0:
   encouragements = [encourage[int(v)][0] for v in selection]
   store_turtle_result.saveEncouragements(c,compresults['month'],encouragements)

# Save the information
conn.commit()

# Get the current table
resultTable = store_turtle_result.getTable(c)
encouragementTable = store_turtle_result.getEncouragements(c,compresults['month'])

# Output the results
show_turtle_result.outputResults(winners, resultTable, compresults['voters'][thumber], compresults['month'], hallOfFamers, encouragementTable, len(compresults['voters']))
