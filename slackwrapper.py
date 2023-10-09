"""
    SlackWrapper

    This handles the incoming message events from Slack by:

    1.  Determining if we need to translate the message
    2.  Converting user ids in the message to names
    3.  Sending the text out to get translated
    4.  Posting the translated text into the "other" channel

"""
import os
import requests
import json
from openaiwrapper import OpenAIWrapper
from threading import Thread

class SlackWrapper:

    #   Init is responsible for fetching the environment variables that have
    #   API keys, endpoints, and channel ids for our particular org
    def __init__(self):
        self.channel_english = os.getenv('SLACK_ENG_CHAN_ID')
        self.channel_spanish = os.getenv('SLACK_ESP_CHAN_ID')
        self.slack_token = os.getenv('SLACK_TOKEN')
        self.post_english = os.getenv('SLACK_ENG_URL')
        self.post_spanish = os.getenv('SLACK_ESP_URL')


    # Lookup a user's name from their id
    def get_user_name(self, id:str):
        payload = {'token': self.slack_token, 'user': id}
        print(self.slack_token[:10], flush=True)
        resp = requests.post('https://slack.com/api/users.info', data=payload)
        print(resp, flush=True)
        data = json.loads(resp.content)
        if 'error' in data:
            print(f'get_user_name({id}): Error {data["error"]}', flush=True)
        if 'user' in data and 'name' in data['user']:
            return data['user']['name']
        return '-system-'

    # Take a line of text with 0 or more embedded <@id> in it and expand the
    # ids to user names
    def expand_users(self, text):
        result = ''

        while (loc := text.find('<@')) != -1:
            result = result + text[:loc] + '@'
            text = text[loc + 2:]
            end = text.find('>')
            if end == -1:
                break

            user_id = text[:end]
            text = text[end + 1:]
            user_name = self.get_user_name(user_id)
            result = result + user_name

        result = result + text
        return result


    @staticmethod
    def post_text(url, text):
        headers = { 'content-type': 'application/json' }

        data = { 'text': text }

        r = requests.post(url, data=json.dumps(data), headers=headers)

        return r    # Not that anyone cares...

    # This runs in the background so we can respond to slack quickly
    def do_translate(self, to_lang, text, user):
        text = self.expand_users(text)

        if user is not None:
            user = self.get_user_name(user)

        oai = OpenAIWrapper()

        if to_lang == 'english':
            new_text = oai.to_english(text)
            if user is not None:
                new_text = f"_{user} said:_\n" + new_text
            self.post_text(self.post_english, new_text)

        else:
            new_text = oai.to_spanish(text)
            if user is not None:
                new_text = f"_{user} dijo:_\n" + new_text
            self.post_text(self.post_spanish, new_text)

    # Handle an event notification from slack
    # Because the call to open
    def handle_event(self, event):

        c = event['channel']

        # We may get a lot more traffic than we'd like, so make sure
        # it's coming from the channels we're interested in
        if c not in [self.channel_english, self.channel_spanish]:
            return ''

        if 'user' not in event:
            # system message
            return ''

        # Make sure there's something to translate
        if 'text' not in event or len(event['text'].strip()) == 0:
            return ''

        to_language = ['english', 'spanish'][c != self.channel_spanish]

        th = Thread(target=self.do_translate, args=(to_language, event['text'], event['user']))
        th.start()
        return ''



