import sqlite3

def createTables(c):
   # Create table for each months results
   c.execute("CREATE TABLE results (user text, month text, votes int, image int, points int, encourage int, geeklistitemid int)")
   c.execute("CREATE TABLE thumber (user text, month text, numvoters int)")

def getHallOfFame(c):
   halloffame = set()
   for row in c.execute('SELECT * FROM (SELECT user, SUM(points) AS sumpoints FROM results GROUP BY user) WHERE sumpoints > 100'):
      halloffame.add(row[0])
   return halloffame

# c - Connection to database
# month - ISO month for the results
# results - List of tuples ordered by votes. (username, imageid, votes, geeklistitemid )
# places - List of tuples of (username, place)
def addResult(c, month, results, places):

   placePoints = [5,3,1]

   # Map the 
   userPoints = {}
   for placed in places:
      userPoints[placed[0]] = placePoints[placed[3]-1]

   rows = []
   for res in results:
      points = 0
      if res[0] in userPoints:
         points = userPoints[res[0]]
   
      # Build a results row
	  # user text, month text, votes int, image int, points int, encourage int, geeklistitemid int
      insRow = (res[0], month, res[2], res[1], points, 0, res[3])
      rows.append(insRow)

   # Now we can save this data
   c.executemany('INSERT INTO results VALUES (?,?,?,?,?,?,?)', rows)   

def addThumber(c, dt, user, numvoters):
   c.execute("INSERT INTO thumber(user, month, numvoters) VALUES (?,?,?)",(dt,user,numvoters))

def getResults(c,month):
   return c.execute('SELECT * FROM results WHERE month=? ORDER BY votes', (month))

def getTable(c):
   table = []
   query = ("SELECT user, sumpoints "
            "FROM (SELECT user, SUM(points) AS sumpoints, MAX(DATE(month)) AS lastEntry FROM results GROUP BY user) "
            "WHERE lastEntry >= DATE('now','-12 months') ORDER BY sumpoints DESC")
   return c.execute(query).fetchall()

# Fetch a list of tuples containing the usernames, the number of times they have entered the competition,
# the number of encouragement awards they've received and the months votes, image and geeklistitemid for the given month.
# This list only returns users that have never received any points.
def getEncourageRecommendation(c,month):
   return c.execute('''SELECT rec.user, entered, encouraged, votes, image, geeklistitemid FROM
                       (SELECT user,count(*) as entered,sum(points) AS pts, SUM(encourage) AS encouraged 
					    FROM results 
					    WHERE user in (select user from results where month=?) 
					    GROUP BY user) AS rec 
					   left join 
					   (select user, votes, image, geeklistitemid 
					    FROM results 
						WHERE month=?) AS monthentry 
					   ON rec.user = monthentry.user 
					   WHERE pts=0
					   ORDER BY entered''',(month,month)).fetchall()

# Set the encourage value for the given users in the given month
# month - String of month being displayed
# encouraged - List of users to encourage
def saveEncouragements(c,month,encouraged):
  for encourage in encouraged:
     c.execute('UPDATE results SET encourage=1 WHERE user=? AND month=?',(encourage,month))

# Get a list of user names, image and geeklistid who were encouraged for the month
def getEncouragements(c,month):
  return c.execute('SELECT user, image, geeklistitemid FROM results WHERE encourage=1 AND month=?',(month,)).fetchall()

# Prepare an initial database, using data from April 2019 list 51364
if __name__ == "__main__":
   conn = sqlite3.connect('goldenTurtle.db')
   c = conn.cursor()
   createTables(c)
   conn.commit()

   initialTable = [
 ("Roolz", 101), 
 ("Vinssounet", 77), 
 ("Tadpoleface", 67),
 ("Muzza", 63),
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