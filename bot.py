from time import thread_time, thread_time_ns
import slack
import string
import os
# from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from datetime import datetime,timedelta



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

welcome_messages = dict()

bad_words = ['fuck','shit','hell','sucker']

schedule_messages = [
    {'channel': 'C03LSHR7V1P', 'post_at': int((datetime.now() + timedelta(seconds = 20)).timestamp()), 'text' : 'First Message !',} ,
    {'channel': 'C03LSHR7V1P', 'post_at': int((datetime.now() + timedelta(seconds = 30)).timestamp()), 'text' : 'Second Message !!',} ,
]

# ============================================================================================
#               Welcome Message Formatting Class.

class WelcomeMessage:
    
    #start_text is the text that has been sent, mrkdwn refers to formatted text.
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this awesome channel! \n\n'
                '*Get started by completing the tasks!*'
            )
        }
    }

    # divider refers to a single line, like <hr>
    DIVIDER = {'type': 'divider'}

    
    #text between colon is way of representing emojis in slack. 
    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False
    
    # this is to group all the text, including the welcome_message, divider and the reaction_task.
    # the return value is being passed as a dict, so that it can be directly unpacked to the chat_postMessage.
    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel':self.channel,
            'username':'Welcome Robot!',
            'icon_emoji':self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }


    # this refers to the text below the welcome message.
    def _get_reaction_task(self):
        checkMark = ':white_check_mark:'

        if not self.completed:
            checkMark = ':white_large_square:'

        text = f'{checkMark} *React to this message!*'

        return {'type': 'section', 'text': {'type':'mrkdwn', 'text':text}}
        

def badWordChecker(message):
    message = message.lower()
    message = message.translate(str.maketrans('','',string.punctuation))

    return any(word in message for word in bad_words)

#   ======================================================================================
#                       Sent that welcome Message.

# this is the place where the welcome message is being sent. timestamp is updated from response.
# ** is used to unpack the dictionary. So that all the attributes of chat_postMessage are automatically filled.
def send_welcome_message(channel,user):
    
    if channel not in welcome_messages:
        welcome_messages[channel] = {}
   
    if user in welcome_messages[channel]:
        return

    welcome = WelcomeMessage(channel,user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)    
    welcome.timestamp = response['ts']

    # this is to keep track of the welcome message elements that is being sent. Just like a local log database.

    welcome_messages[channel][user] = welcome


def schedule_message(messages):
    ids = []
    for message in messages:
        response = client.chat_scheduleMessage(**message)

        _id = response.get('scheduled_message_id')
        ids.append(_id)

    return ids

# this section is not properly working, needs more debugging.

def delete_message(ids, channel):
    for _id in ids:
        client.chat_deleteScheduledMessage(channel= channel, scheduled_message_id= _id)

#===============================================================================================
#                    Handling Messages

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
    #when bot is updating a message user_id is kept none, by slack. So the first condition is added so that 
    #the if else check won't break.

    if(user_id != None and bot_id != user_id):
        if user_id in message_counter:
            message_counter[user_id] += 1
        else:
            message_counter[user_id] = 1

        # client.chat_postMessage(channel = channel_id, text = user_message)

        #when the user enters start, the method is called and the message is being sent.
        # in here the message is sent as dm. that's why channel part is populated with @user_id
        if(user_message.lower() == 'start'):
            send_welcome_message(f'@{user_id}',user_id)
        elif(badWordChecker(user_message)):
            ts = event.get('ts')
            client.chat_postMessage(channel= channel_id, thread_ts = ts, text = "WARNING!:warning:")


#=================================================================================
#       Reaction handling

#payload varies for different events. Check the payload of the events to fetch different fields accordingly.
@slack_event_adapter.on('reaction_added')
def react(payload):
    # print(payload)
    event = payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    # client.chat_postMessage(channel = channel_id, text = "Don't react. Sent emoji")

    # We don't want to check reactions of non welcoming messages.
    if f'@{user_id}' not in welcome_messages:
        return 

    #fetch the welcome mes  sage object associated with current user_id and channel_id
    welcome = welcome_messages[f'@{user_id}'][user_id]

    #change the flag
    welcome.completed = True
    welcome.channel = channel_id

    # edit the current message to change the task completion emoji.
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']

    


#=================================================================================
# managing slack commands
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
    idList = schedule_message(schedule_messages)
    delete_message(idList, channel='C03LSHR7V1P')
    app.run(debug = True)