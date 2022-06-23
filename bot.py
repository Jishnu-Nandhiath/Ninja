import slack
import os
# from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter



# Loading the environment Variable file.
env_path = './.env'
load_dotenv(dotenv_path = env_path)


#variable __name__ is referring to the current file. It is to identify the assets and packages used in this file.
app = Flask(__name__)


#To handle the events sent to us via the api. Like other users sending messages.
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'],'/slack/events',app)


#os.environ will fetch the corresponding environment values from the .env file.
client = slack.WebClient(token = os.environ['SLACK_TOKEN'])


# get the bot user_id, so that the message don't repeat infinite times. Replying back to itself.
bot_id = client.api_call("auth.test")['user_id']

"""
Since decorators are used, the decorator function calls the decorated function based on user 
interaction with bot.
"""
message_counter = dict()

# In here while using the function decorator the string passed should be the event subscription.
# In this case it is "message". Because we're sending back teh message.
@slack_event_adapter.on('message')
def message(payload):
    # print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    user_message = event.get('text')
    
    #posting the message the bot received back to user, also keeping track of each user's messages.
    if(bot_id != user_id):
        if user_id in message_counter:
            message_counter[user_id] += 1
        else:
            message_counter[user_id] = 1

        client.chat_postMessage(channel = channel_id, text = user_message)


#payload varies for different events. Check the payload of the events to fetch different fields accordingly.
@slack_event_adapter.on('reaction_added')
def react(payload):
    # print(payload)
    event = payload.get('event', {})
    channel_id = event['item']['channel']
    client.chat_postMessage(channel = channel_id, text = "Don't react. Sent emoji")


# route has been created to execute the commands.
@app.route('/message-count', methods = ['GET', 'POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    message_count = message_counter.get(user_id, 0)

    client.chat_postMessage(channel = channel_id, text = f"Message Count : {message_count}")    
    
    return Response(),200




# Run the flask web app
if __name__ == "__main__":
    app.run(debug = True)