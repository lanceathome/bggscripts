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
# pip install Mako
from mako.template import Template

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
store_turtle_result.addThumber(c,compresults['month'],compresults['voters'][thumber])

# Save the information
conn.commit()

# Get the current table
table = store_turtle_result.getTable(c)

f = open("results-{}.txt".format(compresults['month']),"w+")

print("""

Thanks to everyone who submitted an entry.

As ever, congratulations to all last month's winners:

""", file = f)

# Show the winners
for row in winners:
   # Only rows with points have placed
   place = "1st"
   if row[3] == 2:
      place = "2nd"
   if row[3] == 3:
      place = "3rd"

   print("[b]{}[/b]".format(place), file = f)
   print("", file = f)
   print("[username={}]".format(row[0]), file = f)
   print("", file = f)
   print("[ImageID={} medium]".format(row[1]), file = f)
   print("", file = f)
   print("with {} thumbs".format(row[2]), file = f)   
   print("", file = f)   
      
# Show the thumber
print("""
Our thumber of the month is:

""", file = f)
print("[username={}]".format(compresults['voters'][thumber]), file = f)
print("""

Thanks to everyone who entered and tipped last month and good luck to all this month's entrants.

""", file = f)

# Show the hall of fame table
print("""
:star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star:

[b]Hall of Fame[/b]

""", file = f)

for result in table:
   if result[1] > 0 and result[1] < 100:
      print("{} - {}".format(result[0],result[1]), file = f)


# Show the hall of fame champions
print("""
:star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star:

[b]Hall of Fame Members[/b]

""", file = f)

for halloffame in hallOfFamers:
   print("[username={}]".format(halloffame), file = f)

print("""

[b]Hall of Fame Guidelines[/b]

:d10-1: 100 points to be granted entry into the Hall of Fame (HoF).

:d10-2: A special and exclusive microbadge will be commissioned and awarded to HoF members.

:d10-3: A HoF member is encouraged to enter but is not eligible for first, second or third place - they go to non HoF members.

:d10-4: The current members of the HoF will be noted in the comment threads announcing the winner as well as the contest notification list.[/q]
""", file = f)

f.close()
