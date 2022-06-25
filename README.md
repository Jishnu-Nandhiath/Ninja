# Ninja
Ninja is a simple slack bot that can send welcome messages, display message counts, schedule, delete messages and can respond to reactions as well😎.

The code requires .env file to function completely. It has been removed due to security issues.

To make the code work, add your environment constants configured from the slack account.

Ngrok.exe - Ngrok is basically used to forward the 5000 port to another web address provided by the ngrok.
Command : ngrok http 5000  /Because 5000 is the default port where the server is run. In here we're managing a server locally to play with it.            
            
Ngrok is required because for event handling the api in which events has to be on the web to give it to the slack event request url. 

Using Ngrok we're forwarding our local server in port 5000 to another public address so, that the requests get forwarded back and forth via this.
