from flask import Flask, request
from datetime import datetime
import requests
import json
import os

baseurl = "https://api.ciscospark.com/v1"

bot_auth_token = os.environ.get("SPARK_ACCESS_TOKEN")
port = os.environ.get("PORT")
opencage_key = os.environ.get("OPENCAGE_API_KEY")

if (bot_auth_token == '' or 
    bot_auth_token == "PASTE YOUR BOT ACCESS TOKEN HERE"):
    print("SPARK_ACCESS_TOKEN not found in environment variables")
    exit()
headers = {"Content-Type": "application/json",
           "Accept": "application/json",
           "Authorization": "Bearer %s" % bot_auth_token
           }
me_resp = requests.get(baseurl + '/people/me', headers=headers)
# Check that the Spark access token belongs to a bot
if json.loads(me_resp.text)['type'] != 'bot':
    print('SPARK_ACCESS_TOKEN does not belong to a bot...exiting')
    exit()
bot_id = json.loads(me_resp.text)['id']  # Retrieve / extract the bot's user ID
app = Flask(__name__)


def get_message(data):
    mess_id = data['id']
    mess_api = "/messages/%s" % mess_id
    mess_url = baseurl + mess_api
    mess_resp = requests.get(mess_url, headers=headers)
    mess_content = json.loads(mess_resp.text)['text']
    mess_room = json.loads(mess_resp.text)['roomId']
    return mess_room, mess_content


def send_message(room, text):
    send_api = "/messages"
    send_url = baseurl + send_api
    send_data = {"roomId": room,
                 "text": text
                 }
    send_resp = requests.post(send_url,
                              headers=headers,
                              json=send_data)
    return send_resp


def get_membership(room, email):
    get_mem_api = "/memberships"
    get_mem_param = {"roomId": room,
                     "personEmail": email
                     }
    get_mem_url = baseurl + get_mem_api
    get_mem_resp = requests.get(get_mem_url,
                                params=get_mem_param,
                                headers=headers)
    print(get_mem_resp)
    if (get_mem_resp.status_code != 200 or
            json.loads(get_mem_resp.text)["items"] == []):
        get_mem_id = None
    else:
        get_mem_id = json.loads(get_mem_resp.text)["items"][0]["id"]
    return get_mem_id


@app.route('/hook1', methods=['POST'])
def hook_1():
    spark_hook = request.json
    hook_data = spark_hook["data"]
    # Make sure this isn't a message previously posted by this bot's id
    if hook_data["personId"] == bot_id:
        return "OK"
    mess_room, mess_content = get_message(hook_data)
    print(mess_content)
    geodata = requests.get("https://api.opencagedata.com/geocode/v1/json?key=" + opencage_key + "&q=" + mess_content)
    print(json.loads(geodata.text)['results'])
    sunrise = json.loads(geodata.text)['results'][0]['annotations']['sun']['rise']['apparent']
    sunset = json.loads(geodata.text)['results'][0]['annotations']['sun']['set']['apparent']
    offset = json.loads(geodata.text)['results'][0]['annotations']['timezone']['offset_sec']
    tz = json.loads(geodata.text)['results'][0]['annotations']['timezone']['short_name']
#    city = json.loads(geodata.text)['results'][0]['components']['city']
    print(json.loads(geodata.text)['results'][0]['components'])
    print(sunrise)
    print(sunset)
    print(offset)
    print(tz)
    send = send_message(mess_room, "Sunrise: " +
                        datetime.utcfromtimestamp(sunrise+offset).strftime("%I:%M%p ") + tz +
                        ".\nSunset: " +
                        datetime.utcfromtimestamp(sunset+offset).strftime("%I:%M%p ") + tz + "."
    )
    return json.dumps({"did-it-work": "A-OK"})


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=port)
