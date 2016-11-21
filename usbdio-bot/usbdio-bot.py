"""
A slackbot that controls a USBDIO via commands from a Slack channel. This uses the RTM API.

   Required environment variables (example only, these are not real tokens).
   Get these from the Slack account settings
   USBDIO_BOT_ID = 'U20981S736'
   USBDIO_BOT_TOKEN = 'xoxb-106076235608-AbacukynpGahsicJqugKZC'
   USBDIO_PATH = 'C:\Program Files (x86)\usbdio'

"""
import os
import time
import subprocess
from slackclient import SlackClient


BOT_NAME = 'usbdio-bot'
# usbdio-bot's ID as an environment variable
BOT_ID = os.environ.get('USBDIO_BOT_ID')
USBDIO_PATH = os.environ.get('USBDIO_PATH')
USBDIO_TOOL = os.path.join(USBDIO_PATH, 'usbdio_info.exe')

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "help"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('USBDIO_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "I don't understand that command.  Try 'help'."
    if command.startswith(('help', '?', '-h', '-v', '-l', '-e', '-o', '-i')):
        usbdio_args = [USBDIO_TOOL, ]
        usbdio_args.extend([cmd for cmd in command.split()])
        print 'Calling subprocess: {}'.format(usbdio_args)
        response = subprocess.check_output(usbdio_args)
        print 'Response: {}'.format(response)
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        This parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("usbdio-bot {} connected and running!".format(BOT_ID))
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")