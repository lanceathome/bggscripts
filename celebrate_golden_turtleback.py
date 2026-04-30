import csv
import json
import sys
import xml
import requests 
from fetch_xml import fetch_xml

def get_winner_name(winner):
    last_slash = winner.rfind('/')
    if last_slash != -1:
        return winner[last_slash + 1:]
    else:
        return winner


def get_winner_image(image):
    last_slash = image.rfind('/')
    if last_slash != -1:
        return image[last_slash + 1:]
    else:
        return None
    

def get_winning_entries(entries):
    winnings = []
    while True:
        try:
            winner = entries.pop(0)
            image = entries.pop(0)
            if winner and image:
                winnings.append((get_winner_name(winner), get_winner_image(image)))
        except IndexError:
            break
    return winnings


def format_entry_body(result):
    body = "Number of entries: {}\nWinning votes: {}\n".format(result["entries"], result["votes"])
    for winner in result["winners"]:
        body += "\n"
        body += "[username={}]".format(winner[0])
        if winner[1]:
            body += "[ImageID={} medium]".format(winner[1])
    return body


def fetch_entries(bearer_token):

    url = 'https://www.boardgamegeek.com/xmlapi/geeklist/51364'
    xml = fetch_xml(url, bearer_token)

    listids = []

    for item in xml.iter('item'):
        listids.append(int(item.attrib['objectid']))

    return listids

results = {}
with open('golden_turtle_winners.csv', mode='r', newline='') as file:
    reader = csv.reader(file)
    next(reader)  # Skip the header row if there is one    
    for row in reader:
        # Find the geeklist
        geeklist = row[1][len("https://boardgamegeek.com/geeklist/"):]
        geeklist = geeklist[:geeklist.find('/')]
        geeklist = int(geeklist)
        
        entries = row[3]
        votes = row[4]
        
        winners = get_winning_entries(row[5:])

        results[geeklist] = {
            "geeklist": geeklist,
            "entries": entries,
            "votes": votes,
            "winners": winners
        }

# config requires "bggusername" and "bggpassword", where the password is the session key,
# not the raw password
with open('config.json') as json_file:
  cookie = json.load(json_file)

listid = int(sys.argv[1])

# Users must submit a session id to authenticate POST requests now
# Need to find how to get this programmatically, for now just pass it in as an argument
sessionid = str(sys.argv[2])

headers = {
  "Authorization": f"GeekAuth {sessionid}",
}

# Find all of the Geeklist item ids
entries = fetch_entries(cookie["appToken"])

for idx, geeklist_id in enumerate(entries):
    print("Adding result for geeklist {}".format(geeklist_id))
    if geeklist_id in results:
        res = results[geeklist_id]
        body = format_entry_body(res)
        image = res["winners"][0][1] if res["winners"] and res["winners"][0][1] else None
    else:
        body = "No results found for this entry."
        image = None
        
    data = {
        "body": body,
        "imageOverridden": False if image is None else True,
        "imageid": image,
        "index": idx + 1,
        "item": {
            "id": str(geeklist_id),
            "type": "geeklist"
        }
    }
    post_uri = "https://api.geekdo.com/api/geeklist/{}/listitem".format(listid)
    requests.post(post_uri, headers=headers, json=data)
    # Post gives a redirect result instead of 200
    
