# usbdio-bot
An integration between Slack and exacqVision USB I/O Module (USBDIO)

This is an implementation of a custom SlackBot integration that controls an Exacq USBDIO hardware IoT relay.  The hardware description can be found here:
 * Exacq Model 5000-50200 USB DIO - https://exacq.com/products/io/
 * Toggles 4 digital outputs + 1 dry contact relay, and read 8 digital inputs.

`usbdio-bot` internally uses the python slackclient module - http://slackapi.github.io/python-slackclient/

When logged into your Slack Account , `usbdio-bot` will listen on the #usbdio-bot channel.  It listens for specific keyword commands (a command line) that will be forwarded to the USBDIO device for processing.



