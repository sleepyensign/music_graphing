import os, base64, json
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from requests import post, get

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COUNTRY_CODE = "US"
DEFAULT_LIMIT = 1
BILLBOARD_BASE_URL = "https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/"

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

### Cool Functions that do everything

def serial_position_100_search_and_graph():
    billboard_result = billboard_search_recent()
    x = []

    for i in range(100):
        result = search_track(token, str(billboard_result["data"][i]["song"] + " by " + billboard_result["data"][i]["artist"]))
        if result["tracks"]["items"][0]["album"]["album_type"] != "single":
            x.append((result["tracks"]["items"][0]["track_number"] - 1) / (result["tracks"]["items"][0]["album"]["total_tracks"] - 1))

    print("Singles not graphed: " + str(100 - len(x)) + "/100 songs")

    plt.hist(x, bins=20, range=(0, 1))
    plt.xlabel("Relative Position in Album")
    plt.ylabel("Number of Songs")
    plt.title("Billboard Hot 100 " + billboard_result["date"] + " - Position on Album Distribution")
    plt.xlim(0, 1)
    plt.xticks([i / 20 for i in range(21)])
    plt.show()

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

serial_position_100_search_and_graph()