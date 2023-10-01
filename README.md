# BGG Scripts
Scripts for BoardGameGeek functions

## Software requirements

You'll need to have Python 3 installed on your computer. This is the minimum required. 

# Golden Turtleback scripts

The folder contains three scripts to use for managing the Golden Turtleback result calculation and submission.
A SQLite database is used to store the results from each competition.

## Setup

The requests library is needed

```bash
python -m pip install requests
python -m pip install Mako
```

Run the store_turle_result.py script to create the default database goldenTurtle.db. The scripts are designed to run 
from the command line (either bash on Linux, or cmd or PowerShell on Windows).

```bash
python store_turtle_result.py
```

This will create a database file called goldenTurtle.db. If the file already exists it will be replaced with a 
new version. The database is loaded with the hall of fame as reported at April 2019 (list 255947). The database
stores future results based on the date the list was submitted (so sometimes, such as June/July 2019 they both
occur in the same month).

## Running

You can generate each months results by running the script golden_turtle.py

```bash
python golden_turtle.py
```

This requires the goldenTurtle.db database in the same directory (see the above step to create it). The most recent
list results are downloaded and added to the results database. A random thumber is selected and stored in the database.
Finally a template file for the results are produced in a file called results-XXXX-XX-XX.txt where the last part is 
the date the date the list was submitted. The template is compatible with the BGG formatting so can be cut and pasted
into comments. The results file doesn't contain any honourable mention results (they are at your discretion).

The script doesn't add points for any user that has already scored 100 points in the hall of fame. Points are 
shared where people have the same thumb count. All results are entered in the database, even those that don't score 
any points.

You can generate the results for older lists by adding a list ID to the golden_turtle.py command. These will bring you
up to date with the missing results.

```bash
python golden_turtle.py 257173
python golden_turtle.py 258249
```
**Note** Running the golden_turtle.py script *will* modify your database. I recommend you make a backup before
running the script to be able to undo any unwanted changes.

You can run the result generation script without modifying the database by using

```bash
python get_turtle_result.py
```

The random thumber will be changed each time you run the script and will likely not be the value used when
you run the golden_turtle.py results.


To find the number of times users from a current entry have appeared in the list use
```
select user,count(*),sum(points) from results where user in (select user from results where month='2019-11-01') group by user;
```

And to get just those people for encouragement awards

```
select user, entered from (select  user,count(*) as entered,sum(points) as pts from results where user in (select user from results where month='2019-11-01') group by user) where pts=0;
```
