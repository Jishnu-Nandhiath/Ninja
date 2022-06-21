import slack
import os
# from pathlib import Path
from dotenv import load_dotenv


# Loading the environment Variable file.
env_path = './.env'
load_dotenv(dotenv_path = env_path)


client = slack.WebClient(token = os.environ['SLACK_TOKEN'])

client.chat_postMessage(channel = '#dev_e1', text = "Hello Boys!")