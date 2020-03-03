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

def outputResults(winners, resultTable, thumber, month, hallOfFamers, encouragements, numVoters):
   f = open("results-{}.txt".format(month),"w+")

   print("""

Thanks to everyone who submitted an entry.

As ever, congratulations to all last month's winners:

""", file = f)

   winnerNames = [row[0] for row in winners]

   # Show the winners
   for row in winners:
      # Only rows with points have placed
      place = "1st"
      if row[3] == 2:
         place = "2nd"
      if row[3] == 3:
         place = "3rd"

      print("[b]{}[/b], with {} thumbs, goes to [listitem={}]{}[/listitem]".format(place,row[2],row[4],row[0]), file = f)
      print("", file = f)
      print("[ImageID={} medium]".format(row[1]), file = f)
      print("", file = f)   
   
   # Show the encouragement awards
   print("[b]Encouragement awards:[/b]", file = f)
   for encourage in encouragements:
      print("[listitem={}]{}[/listitem] for".format(encourage[2],encourage[0]), file=f)
      print("", file=f)
      print("[ImageID={}]".format(encourage[1]), file=f)
   
   # Show the thumber
   print("Of {} voters our thumber of the month is:".format(numVoters), file=f);
   print("[username={}]".format(thumber), file = f)
   print("""

Thanks to everyone who entered and tipped last month and good luck to all this month's entrants.

""", file = f)

   # Show the hall of fame table
   print("""
:star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star::star:

[b]Hall of Fame[/b]

""", file = f)

   for result in resultTable:
      if result[1] > 0 and result[1] < 100:
         if result[0] in winnerNames:
            fmt = "[b]{}[/b] - {}"
         else:
            fmt = "{} - {}"
         print(fmt.format(result[0],result[1]), file = f)


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
