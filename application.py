#! /usr/bin/python3
from flask import Flask, render_template, request, session
from flask_session import Session  # Ensure to install Flask-Session
import csv
import os
import urllib.parse
from botConfig import myBotName, chatBG, botAvatar, useGoogle, confidenceLevel
from botRespond import getResponse

##Experimental Date Time
from dateTime import getTime, getDate

application = Flask(__name__)
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

chatbotName = myBotName
print("Bot Name set to: " + chatbotName)
print("Background is " + chatBG)
print("Avatar is " + botAvatar)
print("Confidence level set to " + str(confidenceLevel))

# This could be replaced with a database connection in production
user_conversations = {}

def get_user_conversation(user_id):
    return user_conversations.get(user_id, [])

def update_user_conversation(user_id, message, bot_reply):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append((message, bot_reply))

application.secret_key = 'Hilman1310'

#Create Log file
try:
    file = open('BotLog.csv', 'r')
except IOError:
    file = open('BotLog.csv', 'w')

def tryGoogle(myQuery):
    myQuery = myQuery.replace("'", "%27")
    showQuery = urllib.parse.unquote(myQuery)
    return "<br><br>You can try this from my friend Google: <a target='_blank' href='https://www.google.com/search?q=" + myQuery + "'>" + showQuery + "</a>"

@application.route("/")
def home():
    return render_template("index.html", botName=chatbotName, chatBG=chatBG, botAvatar=botAvatar)

@application.route("/get")
def get_bot_response():
    user_id = session.get("user_id")
    if not user_id:
        user_id = session["user_id"] = os.urandom(24).hex()  # Generate a random user session ID

    print(f"Session ID: {user_id}")
    # Increment message count in session
    session['message_count'] = session.get('message_count', 0) + 1
    print(f"Message Count: {session['message_count']}")

    userText = request.args.get('msg')

    # Using session management to track conversation
    conversation_history = get_user_conversation(user_id)

    # Obtain bot response and translate if needed
    botReply = getResponse(userText, conversation_history)

    # Update the conversation history
    update_user_conversation(user_id, userText, botReply)

    # Optional: log conversation to CSV for further analysis or debugging
    with open('BotLog.csv', 'a', newline='') as logFile:
        csv.writer(logFile).writerow([user_id, userText, botReply])

    return botReply

if __name__ == "__main__":
    application.run()
