#!/usr/env/python

"""
WOODY-BOT
A raspberry-pi slackbot that directly controls a 8-channel relay board via commands from a Slack channel.
This uses the Slack RTM (Real Time Messaging) API.  The woody name derives from the fact that
The raspi and the relay board are both mounted on a piece of scrap wood.

   Required environment variables (example only, these are not real tokens). Get these from the Slack account settings.
   BOT_ID = 'U20981S736'
   BOT_TOKEN = 'xoxb-106076235608-AbacukynpGahsicJqugKZC'
"""
import os
import time
import datetime
import logging
import signal
from threading import Event

import RPi.GPIO as GPIO  # for apt-get, use 'sudo apt-get install python-rpi.gpio'
from slackclient import SlackClient
from websocket import WebSocketConnectionClosedException

BOT_NAME = 'woody-bot'
BOT_CHAN = '#bot-test'
# woody-bot's ID as an environment variable
BOT_ID = os.environ.get('BOT_ID')
AT_BOT = '<@' + BOT_ID + '>'
BOT_COMMANDS = ['help', 'open', 'close', 'bounce', 'pulse', 'ping', 'exit']

# Basic setup
logger = logging.getLogger(__name__)
sigterm_event = Event()
bot_start = None

# GPIO setup
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO_PINS = (17, 18, 27, 22, 23, 24, 25, 4)


def sigterm_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT.  Other signals can be mapped here as well (SIGHUP?)
    Basically it just sets an event, and main() will exit it's RTM loop when the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    signames = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                    if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warn('Received {}'.format(signames[sig_num]))
    sigterm_event.set()


def switch_relay(chan, state):
    """
    Switches the state of a single relay that is connected to GPIO 0-7.
    :param chan: Index (channel) of GPIO relay, 1 - 8
    :param state: True=relay_on or False=relay_off
    :return: a Error response string to send back to Slack. None=No error.
    """
    r = None
    if chan and chan in range(1, len(GPIO_PINS)+1):
        logger.info('Setting chan {} state to {}'.format(chan, state))
        GPIO.output(GPIO_PINS[chan - 1], GPIO.LOW if state else GPIO.HIGH)
    else:
        logger.error('Invalid chan index: {}'.format(chan))
        r = 'Please provide a trigger channel 1-8'
    return r


def handle_command(cmdline, channel):
    """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.

    :param cmdline: The command line as sent to the bot (multiple args)
    :param channel: The slack channel which received the command.
    :return: A Text string response to send to the Slack channel.
    """
    logger.info('{} Received cmdline "{}" in channel {}'.format(AT_BOT, command, channel))
    response = None
    args = cmdline.lower().split()
    cmd = args[0]
    chan = None if len(args) < 2 else int(args[1])

    if cmd not in BOT_COMMANDS:
        response = 'Unknown command "{}"'.format(cmd)
        logger.error(AT_BOT + ' ' + response)

    elif cmd == 'help':
        response = 'Available commands are:' \
                   '\n```' \
                   '\n  open N     Open a trigger, N=1-8' \
                   '\n  close N    Close a trigger N=1-8' \
                   '\n  pulse N    Open trigger N, wait 1 sec, then close N' \
                   '\n  bounce N   Same as pulse N' \
                   '\n  ping       Check if ' + BOT_NAME + ' is listening' \
                   '\n  exit       Make ' + BOT_NAME + ' exit and stop listening. ' \
                   '\n```'

    elif cmd == 'open':
        # Which relay is being switched?
        response = switch_relay(chan, True)
        if response is None:
            response = 'Trigger {} is now OPEN.'.format(chan)

    elif cmd == 'close':
        response = switch_relay(chan, False)
        if response is None:
            response = 'Trigger {} is now CLOSED.'.format(chan)

    elif cmd == 'pulse' or cmd == 'bounce':
        switch_relay(chan, True)
        time.sleep(1.0)
        response = switch_relay(chan, False)
        if response is None:
            response = 'Trigger {} was pulsed for 1 second.'.format(chan)

    elif cmd == 'ping':
        response = '{} is active, uptime={}'.format(BOT_NAME, str(datetime.datetime.now() - bot_start))

    elif cmd == 'exit':
        sigterm_event.set()
        response = '{} is terminating!'.format(BOT_NAME)

    return response


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


def post_message(slack_client, msg, chan=BOT_CHAN):
    """
    Posts a message to a slack channel using the chat.PostMessage api
    :param slack_client:
    :param msg: The text string message to post
    :param chan: The slack channel name to post in
    :return:
    """
    if slack_client is not None:
        try:
            sc.api_call('chat.postMessage', channel=chan, text=msg, as_user=True)
        except Exception as x:
            logger.error('{} Failed to post message "{}" to channel "{}"'.format(AT_BOT, msg, chan))
            logger.error(str(x), exc_info=True)


if __name__ == "__main__":

    app_start_time = datetime.datetime.now()

    print '\n'\
        '-------------------------------------------------------------------\n'\
        '    Running {0}\n'\
        '    Started on {1}\n'\
        '-------------------------------------------------------------------\n'\
        .format(__file__, app_start_time.isoformat())

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s [%(threadName)-12s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)

    # Install signal handlers after all startup services are running.
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Setup the GPIO relay control outputs
    for p in GPIO_PINS:
        logger.info('{} Initializing GPIO.{}'.format(AT_BOT, p))
        GPIO.setup(p, GPIO.OUT)
        GPIO.output(p, GPIO.HIGH)

    # Main loop, keep alive forever unless we receive a SIGTERM, SIGINT
    while not sigterm_event.is_set():
        sc = None
        try:
            # Instantiate the Slack client
            logger.info('{} creating new SlackClient'.format(AT_BOT))
            sc = SlackClient(os.environ.get('BOT_TOKEN'))

            if sc.rtm_connect():
                bot_start = datetime.datetime.now()
                logger.info('{} is connected to server:\n{}'.format(AT_BOT, sc.server))
                post_message(sc, '{} is now online.'.format(BOT_NAME))

                while not sigterm_event.is_set():
                    command, channel = parse_slack_output(sc.rtm_read())
                    if command and channel:
                        resp = handle_command(command, channel)
                        post_message(sc, resp, channel)
                    time.sleep(1.0)

            else:
                logger.error('{} Connection failed, retrying ...'.format(AT_BOT))
                time.sleep(5.0)

        except WebSocketConnectionClosedException:
            # If remote host closed the connection or some network error happened, this exception will be raised.
            # This sometimes happens in the rtm_read() function.
            # See https://github.com/slackapi/python-slackclient/issues/36
            error_str = 'The Slack RTM host has unexpectedly closed its websocket.\nRestarting ...'.format(AT_BOT)
            logger.error(error_str, exc_info=True)
            post_message(sc, error_str)
            time.sleep(5.0)
            continue

        except Exception as e:
            error_str = '{} Unhandled Exception in MAIN\n{}\nRestarting ...'.format(AT_BOT, str(e))
            logger.error(error_str, exc_info=True)
            post_message(sc, error_str)
            time.sleep(5.0)
            continue

    GPIO.cleanup()
    logging.shutdown()

    # Alas, we are dying
    uptime = datetime.datetime.now() - app_start_time
    print '\n'\
        '-------------------------------------------------------------------\n'\
        '   Stopped {0}\n'\
        '   Uptime was {1}\n'\
        '-------------------------------------------------------------------\n'\
        .format(__file__, str(uptime))
