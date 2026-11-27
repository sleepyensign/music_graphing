import os, io, base64, json, time, threading
import matplotlib.pyplot as plt
#from enum import Enum
from dotenv import load_dotenv
from requests import post, get

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COUNTRY_CODE = "US"
DEFAULT_LIMIT = 1
RETRY_ADD = 2
RATE_LIMIT = 1
BILLBOARD_BASE_URL = "https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/"

SETTINGS_DEFAULT = {
    "graph_types": ["hist"]
}

### Load Settings

PATH = os.getcwd()

settings_file = os.path.join(PATH, "saved_settings.json")

if os.path.isfile(settings_file) and os.access(settings_file, os.R_OK):
    print("Settings exists and is readable.")
else:
    print("Settings is missing or not readable, creating file...")
    with io.open(settings_file, 'w') as file:
        file.write(json.dumps(SETTINGS_DEFAULT))

with open("saved_settings.json", "r") as file:
    settings = json.load(file)

### Load Billboard Cache

billboard_cache_file = os.path.join(PATH, "billboard_cache.json")
billboard_cache = {}

if os.path.isfile(billboard_cache_file) and os.access(billboard_cache_file, os.R_OK):
    print("Billboard cache exists and is readable.")
    with open("billboard_cache.json", "r") as file:
        billboard_cache = json.load(file)
else:
    print("Billboard cache is missing or not readable.")

sentinel = -1
temp_input = None
interrupt = False

### API Functions

def get_token():
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data  = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

token = get_token()
print("Established connection with Spotify servers.")

### Spotify Functions

def search_track(token, track_name):
    base_url = "https://api.spotify.com/v1/search"

    params = {
        "q": track_name,
        "type": "track",
        "market": COUNTRY_CODE,
        "limit": DEFAULT_LIMIT
    }
    headers = get_auth_header(token)

    result = get(base_url, headers=headers, params=params)
    print(result)
    if result.status_code == 200:
        time.sleep(RATE_LIMIT)
        
    elif result.status_code == 429:
        json_result = json.loads(result.content)
        with open("temp3.json", "w", encoding="utf-8") as file:
            json.dump(json_result, file, indent=4)
        
        if "error" in json_result and json_result["error"]["reason"] == "QUOTA_EXCEEDED":
            print("The Spotify 24 hour developer quota has been exceeded. Quitting...")
            quit_program()
        else:
            print("Too many requests, retrying after " + str(result.headers["Retry-After"] + str(RETRY_ADD)) + " seconds.")
            time.sleep(int(result.headers["Retry-After"]) + RETRY_ADD)
            print("Retrying...")
            result = get(base_url, headers=headers, params=params)
            print(result, result.url)
    
    else:
        print("Something went wrong in the search, saving and quitting...")
        quit_program()

    json_result = json.loads(result.content)
    return json_result

### Billboard Hot 100 Functions

def billboard_search_recent():
    url = BILLBOARD_BASE_URL + "recent.json"

    result = get(url)
    print(result, result.url)

    json_result = json.loads(result.content)
    return json_result

def billboard_download_all():
    url = BILLBOARD_BASE_URL + "all.json"

    result = get(url)
    print(result, result.url)

    json_result = json.loads(result.content)
    with open("billboard_all.json", "w", encoding="utf-8") as file:
        json.dump(json_result, file, indent=4)

def billboard_cache_search(name):
    if name in billboard_cache:
        print("Found in cache: " + name)
        return billboard_cache[name]
    else:
        print("Not found in cache: " + name)
        return -1

def billboard_cache_add(name, data):
    billboard_cache[name] = data

### Graphing Functions

def graph(x, date="[Date Unknown]"):

    for i in range(len(settings["graph_types"])):

        match settings["graph_types"][i]:
            case "hist":
                plt.hist(x, bins=20, range=(0, 1))
                plt.xlabel("Relative Position on Album")
                plt.ylabel("Number of Songs")
                plt.title("Billboard Hot 100 " + date + " - Position on Album Distribution")
                plt.xlim(0, 1)
                plt.xticks([i / 20 for i in range(21)])
                plt.show()

### Cool Functions

def billboard_recent_search_and_graph():
    billboard_result = billboard_search_recent()
    x = []

    for i in range(100):
        result = search_track(token, str(billboard_result["data"][i]["song"] + " by " + billboard_result["data"][i]["artist"]))
        if result["tracks"]["items"][0]["album"]["album_type"] != "single":
            x.append((result["tracks"]["items"][0]["track_number"] - 1) / (result["tracks"]["items"][0]["album"]["total_tracks"] - 1))

    print("Singles not graphed: " + str(100 - len(x)) + "/100 songs")
    print("Total songs graphed: " + str(len(x)))
    graph(x, date_format(billboard_result["date"]))

def billboard_all_read_and_graph():
    billboard_all_file = os.path.join(PATH, "billboard_all.json")
    
    if os.path.isfile(billboard_all_file) and os.access(billboard_all_file, os.R_OK):
        print("Billboard history exists and is readable.")
    else:
        temp_input = input("Billboard history is missing or not readable, would you like to download the latest version of the Billboard Hot 100 all time history? (y/n): ")
        if temp_input[0].lower() == "y":
            billboard_download_all()
        else:
            return
    
    with open("billboard_all.json", "r") as file:
        billboard_result = json.load(file)
        temp_input = input("The downloaded Billboard Hot 100 history was last updated " + date_format(billboard_result[-1]["date"]) + ", would you like to download the latest version? (y/n): ")
        if temp_input[0].lower() == "y":
            billboard_download_all()
    
    print("The Billboard history search function checks entries from newest to oldest, r songs (1-100) in every nth entry (1-1000) for i iterations (1-250).")
    r, n, i = -1, -1, -1
    
    while r < 1 or r > 100:
        temp_input = input("r: ")
        try:
            r = int(temp_input)
        except ValueError:
            print("Please input a valid number 1-100.")
    
    while n < 1 or n > 1000:
        temp_input = input("n: ")
        try:
            n = int(temp_input)
        except ValueError:
            print("Please input a valid number 1-1000.")
    
    while i < 1 or i > 250:
        temp_input = input("i: ")
        try:
            i = int(temp_input)
        except ValueError:
            print("Please input a valid number 1-250.")
    
    print("Beginning search, " + str(r) + " songs in every " + str(n) + "th entry for " + str(i) + " iterations.")
    x = []
    searched = []
    
    for j in range(i):
        index = -((j * n) + 1)
        print("Searching from " + date_format(billboard_result[index]["date"]) + " (index: " + str(index) + ", iteration: " + str(j) + ")...")
        threading.Thread(target=listen_for_enter, daemon=True).start()
        for q in range(r):
            if interrupt:
                print("Saving and quitting...")
                quit_program()
            
            track_name = billboard_result[index]["data"][q]["song"] + " by " + billboard_result[index]["data"][q]["artist"]
            result = billboard_cache_search(track_name)
            
            if track_name in searched:
                print("Skipping already searched: " + track_name)
                continue
            
            if result == -1:
                result = search_track(token, track_name)
                if len(result["tracks"]["items"]) < 1:
                    print("Song not found, continuing...")
                    billboard_cache_add(track_name, result)
                else:
                    
                    billboard_cache_add(track_name, result)
                    searched.append(track_name)
                    if result["tracks"]["items"][0]["album"]["album_type"] != "single":
                        x.append((result["tracks"]["items"][0]["track_number"] - 1) / (result["tracks"]["items"][0]["album"]["total_tracks"] - 1))
            else:
                if len(result["tracks"]["items"]) < 1:
                    print("Song not found, continuing...")
                    continue
                searched.append(track_name)
                if result["tracks"]["items"][0]["album"]["album_type"] != "single":
                    x.append((result["tracks"]["items"][0]["track_number"] - 1) / (result["tracks"]["items"][0]["album"]["total_tracks"] - 1))
    
    print("Singles not graphed and songs not found: " + str((r * i) - len(x)) + "/" + str(r * i) + " songs")
    print("Total songs graphed: " + str(len(x)))
    graph(x, "(" + str(r) + " songs in every " + str(n) + "th entry for " + str(i) + " iterations from present to " + date_format(billboard_result[-(n * i)]["date"]) + ")")

### Misc Functions

def print_list(list, with_index=True):
    if with_index:
        for i in range(len(list)):
            print(str(i) + ": " + str(list[i]))
    else:
        for item in list:
            print(str(item))

def date_year_sub(date, amount=-1):
    date_list = date.split("-")
    new_year = int(date_list[0]) - 1
    new_date = str(new_year) + "-" + date_list[1] + "-" + date_list[2]
    return new_date

def date_format(date):
    date_list = date.split("-")
    new_date = date_list[1] + "-" + date_list[2] + "-" + date_list[0]
    return new_date

def listen_for_enter():
    global interrupt
    input("Press enter at any time to save and quit.\n")
    interrupt = True

def quit_program():
    with open("saved_settings.json", "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)
    with open("billboard_cache.json", "w", encoding="utf-8") as file:
        json.dump(billboard_cache, file, indent=4)
    quit()

### Adam Smasher? I hardly know her!

menu_options = ["Quit Program", "Change Graphing Types", "Billboard Hot 100 - Recent", "Billboard Hot 100 - All", "Test Plotting"]
menu_options_desc = ["Quits the program."]

while sentinel != 0:
    interrupt = False
    print("\nWhat would you like to do?\n")
    print_list(menu_options)
    temp_input = input("\nNumber: ")

    try:
        sentinel = int(temp_input)

        match sentinel:
            case 0:
                break

            case 1:
                print("change graphing types")

            case 2:
                billboard_recent_search_and_graph()

            case 3:
                billboard_all_read_and_graph()

            case 4:
                graph([.2, .5], date="Valid Date")

            case _:
                print("Please enter a valid option.")

    except ValueError:
        print("Please enter a valid number.")

quit_program()