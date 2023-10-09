from flask import Flask, request
from slackwrapper import SlackWrapper
import json

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'These are not the droids you are looking for'

@app.route('/events', methods=['POST', 'GET'])
def slack_events():
    print(f"/events {json.dumps(request.form)} | {request.get_data(as_text=True)}", flush=True)

    data = request.get_data(as_text=True)
    if data[0] == '{':
        data = json.loads(data)
    else:
        data = {'text': data}

    # When you first install an events handler, Slack calls it with a challenge
    # to see if it's running and responsive
    if 'challenge' in data:
        print(f"Challenge: {data['challenge']}", flush=True)
        return data['challenge']

    if 'event' in data:
        event = data['event']

        # ignore system / bot messages
        if 'user' not in event:
            print('Ignoring bot message', flush=True)
            return ''


        sl = SlackWrapper()
        sl.handle_event(event)

    return ''

if __name__ == '__main__':
    app.run()
