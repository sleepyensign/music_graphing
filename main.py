import os, base64, json
import matplotlib.pyplot as plt
#from enum import Enum
from dotenv import load_dotenv
from requests import post, get

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COUNTRY_CODE = "US"
DEFAULT_LIMIT = 1
BILLBOARD_BASE_URL = "https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/"

with open("saved_settings.json", "r") as file:
    settings = json.load(file)

sentinel = -1
temp_input = None

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

### Spotify Search Functions

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
    print(result, result.url)

    json_result = json.loads(result.content)
    return json_result

### Billboard Hot 100 Search Functions

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
    return None

### Graphing Functions

def graph(x, date="[Date Unknown]"):

    for i in range(len(settings["graph_types"])):

        match settings["graph_types"][i]:
            case "hist":
                plt.hist(x, bins=20, range=(0, 1))
                plt.xlabel("Relative Position in Album")
                plt.ylabel("Number of Songs")
                plt.title("Billboard Hot 100 " + date + " - Position on Album Distribution")
                plt.xlim(0, 1)
                plt.xticks([i / 20 for i in range(21)])
                plt.show()

### Cool Functions

def billboard_recent_search_and_graph(search_number=100):
    billboard_result = billboard_search_recent()
    x = []

    for i in range(search_number):
        result = search_track(token, str(billboard_result["data"][i]["song"] + " by " + billboard_result["data"][i]["artist"]))
        if result["tracks"]["items"][0]["album"]["album_type"] != "single":
            x.append((result["tracks"]["items"][0]["track_number"] - 1) / (result["tracks"]["items"][0]["album"]["total_tracks"] - 1))

    print("Singles not graphed: " + str(100 - len(x)) + "/" + str(search_number) + " songs")

def billboard_all_read_and_graph(search_number=100):
    with open("billboard_all.json", "r") as file:
        data = json.load(file)

### Misc Functions

def print_list(list, with_index=True):
    if with_index:
        for i in range(len(list)):
            print(str(i) + ": " + str(list[i]))
    else:
        for item in list:
            print(str(item))

def quit_program():
    with open("saved_settings.json", "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)
    quit()

### Adam Smasher? I hardly know her!

'''
track_search = search_track(token, "i cant do nathan")
track = track_search["tracks"]["items"][0]

print(track["name"] + " by " + track["artists"][0]["name"])
print("Track position: " + str(track["track_number"]) + "/" + str(track["album"]["total_tracks"]))

with open("temp.json", "w", encoding="utf-8") as file:
    json.dump(track_search, file, indent=4)

with open("temp2.json", "w", encoding="utf-8") as file:
    json.dump(billboard_search, file, indent=4)

x = [1000, 200, 30, 650, 30, 1200]
plt.plot(x)
plt.show()
'''

### Main Loop

menu_options = ["Quit Program", "Change Graphing Types", "Billboard Hot 100 - Recent", "Billboard Hot 100 - All", "Test Plotting"]
menu_options_desc = ["Quits the program."]

while sentinel != 0:
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
                print("search recent")

            case 3:
                print("search year")

            case 4:
                graph([.2, .5], date="Valid Date")

            case _:
                print("Please enter a valid option.")

    except ValueError:
        print("Please enter a valid number.")

quit_program()