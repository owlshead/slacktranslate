from flask import Flask, request, abort
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

    sl = SlackWrapper()

    #   Somebody is trying to hack us?
    if data['token'] != sl.slack_verification:
        abort(404)      # Ain't nobody here but us chickens!
        return None

    if 'event' in data:
        event = data['event']

        # ignore system / bot messages
        if 'user' not in event:
            print('Ignoring bot message', flush=True)
            return ''


        sl.handle_event(event)

    return ''

if __name__ == '__main__':
    app.run()
