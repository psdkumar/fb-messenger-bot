import os
import sys
import json
import base64

import requests
from flask import Flask, request
from flask_restful import reqparse

app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must
    # return the 'hub.challenge' value in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "psdk":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello, this is PSDK!!", 200


@app.route('/webhook', methods=['POST'])
def webook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message = messaging_event["message"]
                    
                    # Text Message
                    if message.get("text") :
                        msg_type = "text"
                        message_text = message["text"].encode('utf-8')  # the message's text

                        start = ["Hi","hi","HI","Hey","hey","HEY","Hello","hello","HELLO"]
                        if message_text in start:
                            user_name = get_userinfo(sender_id)
                            message_text = message["text"] + " " +  user_name

                        print msg_type, " : ", message_text
                        send_message(sender_id, msg_type, message_text)

                    # Stickers/GIFs/Images/Audios/VIdeos/Files
                    elif message.get("attachments"):
                        msg_type = message["attachments"][0]["type"]
                        url = message["attachments"][0]["payload"]["url"]
                        print msg_type, " : ", url
                        send_message(sender_id, msg_type, url)

                    # Others    
                    else:
                        print "Others"
                        send_message(sender_id,"text", "Currently, I can reply for only text/stickers/gif/images/audio/videos/files only")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def get_userinfo(user_id):
    log("Getting userinfo : {user}".format(user=user_id))

    params = {
        "access_token": "EAAJAy6EtyYgBAH2TvlczrJJ3443dGF7YZAmkutzDCraRSrdtGI3wP7b57beOmOMKEB2Pf8dD1ueRXeVgDAvXpsBZAzOX0gGnstNkLUos2dF8YCgov2AfpOi37YLocCGYkW3zs3iZBwPlwx24C9d2rNUt30BU9t8ZBsZCUbK3ZAwAZDZD"
    }
    headers = {
        "Content-Type": "application/json"
    }
    get_url = "https://graph.facebook.com/v2.6/{USER_ID}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={PAGE_ACCESS_TOKEN}".format(USER_ID=user_id,PAGE_ACCESS_TOKEN=params["access_token"])
    print "url : ", get_url
    r = requests.get(get_url)

    if r.status_code == 200 :
        info = json.loads(r.content)
        log("User Info : {data}".format(data=info))
        return info["first_name"]
    else :
        log(r.status_code)
        log(r.text)
    return ""

        

def send_message(recipient_id, msg_type, message):

    log("Sending {message_type} message to {recipient} : {msg}".format(recipient=recipient_id,message_type=msg_type,msg=message))

    params = {
        "access_token": "EAAJAy6EtyYgBAH2TvlczrJJ3443dGF7YZAmkutzDCraRSrdtGI3wP7b57beOmOMKEB2Pf8dD1ueRXeVgDAvXpsBZAzOX0gGnstNkLUos2dF8YCgov2AfpOi37YLocCGYkW3zs3iZBwPlwx24C9d2rNUt30BU9t8ZBsZCUbK3ZAwAZDZD"
    }
    headers = {
        "Content-Type": "application/json"
    }

    # Reply for Text
    if msg_type == "text":
        data = json.dumps({
            "recipient" : {
                "id" : recipient_id
            },
            "message" : {
                "text" : message
            }
        })

    # Reply for Stickers/GIFs/Images/Audios/VIdeos/Files    
    elif (msg_type == "image"
            or msg_type == "audio"
            or msg_type == "video"
            or msg_type == "file"):

        data = json.dumps({
            "recipient": {
                "id" : recipient_id
            },
            "message" : {
                "attachment" :{
                    "type" : msg_type,
                    "payload":{
                        "url" : message
                    }
                }
            }
        })
        print message
        log(data)

    # Default reply for others
    else:
        data = json.dumps({
            "recipient" : {
                "id" : recipient_id
            },
            "message" : {
                "text" : "Not text/sticker/gif/image/audio/video/file" 
            }
        })   

    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)    

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host = '0.0.0.0', port = port, debug = True, threaded = True)