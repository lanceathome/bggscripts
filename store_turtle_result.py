import sqlite3

def createTables(c):
   # Create table for each months results
   c.execute("CREATE TABLE results (user text, month text, votes int, image int, points int)")
   c.execute("CREATE TABLE thumber (user text, month text)")

def getHallOfFame(c):
   halloffame = set()
   for row in c.execute('SELECT * FROM (SELECT user, SUM(points) AS sumpoints FROM results GROUP BY user) WHERE sumpoints > 100'):
      halloffame.add(row[0])
   return halloffame

# c - Connection to database
# month - ISO month for the results
# results - List of tuples ordered by votes. (username, imageid, votes )
def addResult(c, month, results):
   # Use the hall of fame to exclude points from winners who are already too good
   halloffame = getHallOfFame(c)

   # Assume the first row is the current winner (it is if sorted properly)   
   maxVotes = results[0][2]
   # Points for each place
   placePoints = [5,3,1,0]
   
   rows = []
   for res in results:
      if len(placePoints) > 0:
         points = placePoints[0]
      else:
         points = 0

      # A hall of fame user doesn't get any points
      if res[0] in halloffame:
         points = 0
      else:
         # Have we gone to a lower place for points
         if res[2] < maxVotes:       
            # Update the points if this is a lower place
            if len(placePoints) > 0:
               placePoints.pop(0)
               maxVotes = res[2]
            else:
               maxVotes = -1

      # Build a results row
      insRow = (res[0], month, res[2], res[1], points)
      rows.append(insRow)

   # Now we can save this data
   c.executemany('INSERT INTO results VALUES (?,?,?,?,?)', rows)   

def addThumber(c, dt, user):
   c.execute("INSERT INTO thumber(user, month) VALUES (?,?)",(dt,user))

def getResults(c,month):
   return c.execute('SELECT * FROM results WHERE month=? ORDER BY votes', (month))

def getTable(c):
   table = []
   return c.execute('SELECT user, SUM(points) AS sumpoints FROM results GROUP BY user ORDER BY sumpoints DESC').fetchall()


# Prepare an initial database
if __name__ == "__main__":
   conn = sqlite3.connect('goldenTurtle.db')
   c = conn.cursor()
   createTables(c)
   conn.commit()

   initialTable = [
 ("Roolz", 101), 
 ("Vinssounet", 77), 
 ("Tadpoleface", 67),
 ("muzza", 63),
 ("Stratagon", 51),
 ("Jormi_Boced", 50),
 ("oneilljgf", 46),
 ("Pauljima", 42),
 ("dasambi", 39),
 ("dagobal", 37),
 ("Alexandra27", 30),
 ("Vickers", 29),
 ("Syfen", 29),
 ("gilesdorrington", 26),
 ("EyeLost", 24),
 ("muzfish4", 24),
 ("fisha", 21),
 ("Kattavippa", 20),
 ("TeflonBilly9", 15),
 ("Rinceart",  13),
 ("pavunisi",  12),
 ("darthain",  11),
 ("Devon Harman",  11),
 ("badrobot",  11),
 ("neoshmengi",  10),
 ("minksling",  10),
 ("beam1306",  9),
 ("Skkrohmagnon",  8),
 ("birdman37",  8),
 ("puzzlemonkey",  8),
 ("rhox",  8),
 ("ScottE",  7),
 ("braveheart101",  7),
 ("Fluisterwoud",  6),
 ("AGN1964",  5),
 ("Belak0r",  5),
 ("Nekku",  5),
 ("manowarplayer",  5),
 ("garion",  5),
 ("paleogirl",  5),
 ("kkone",  5),
 ("beckerdo",  5),
 ("refinery",  5),
 ("heinrichsteven",  5),
 ("zozmachine",  5),
 ("leaxe",  5),
 ("ilfranz",  5),
 ("bigblock75",  5),
 ("eekamouse",  4),
 ("Geert Dijstelbloem",  4),
 ("caradoc",  4),
 ("Geirerik",  4),
 ("drtanglebones",  3),
 ("ParisPink",  3),
 ("Trikels",  3),
 ("Parduckoponya",  3),
 ("bookblogger",  3),
 ("Bastion of Insanity",  3),
 ("jwhyne",  3),
 ("fydo",  3),
 ("Minis by DJS",  3),
 ("xTHAWx",  3),
 ("Boromir_and_Kermit", 3),
 ("Avicus",  3),
 ("tpchid",  3),
 ("wolfzell",  3),
 ("cuzzle",  3),
 ("Ghool",  2),
 ("Originaldibbler",  2),
 ("enie",  1),
 ("jambang",  1),
 ("Tgov",  1),
 ("haslo",  1),
 ("salonikios",  1),
 ("strictly",  1),
 ("lmyrick",  1),
 ("Berthold",  1),
 ("smittenkitten",  1),
 ("bhj",  1), 
 ("spacewolf",  1),
 ("MrPinkEyes",  1),
 ("iraparsons1",  1),
 ("ganotisim",  1),
 ("captainraffi",  1),
 ("Chromit90",  1),
 ("MB75",  1 ),
 ("brewgeek",  1)
]

   c.executemany('INSERT INTO results (user,points) VALUES (?,?)', initialTable)   
   conn.commit()