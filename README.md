![Woody from Toy Story](https://lumiere-a.akamaihd.net/v1/images/open-uri20150422-20810-10n7ovy_9b42e613.jpeg)
# woody-bot
An integration between Slack and a generic 8-channel dry contact relay board, running on a Raspberry Pi.  It is named Woody-bot because the Rpi and the relays are mounted on a piece of wood.  

This is an implementation of a custom SlackBot integration that controls an 8 channel IoT relay, such as [this one](https://www.amazon.com/Elegoo-Channel-Optocoupler-Arduino-Raspberry/dp/B01HCFJC0Y/).
The relays are connected to zone triggers on various intrusion panels made by DSC, Honeywell, Bosch.  This setup is used for project testing, because we have several remote developers who would like to trip 
some intrusion zones but don't have physical access at our site.


When logged into your Slack Account , `woody-bot` will listen on specific channel.  It listens for specific keyword commands (a command line) that is parsed and handled.

Available commands are
* `open N`     Open a trigger, N=1-8
* `close N`    Close a trigger N=1-8
* `pulse N`    Open trigger N, wait 1 sec, then close N
* `bounce N`   Same as pulse N
* `ping`       Check if woody-bot is listening
* `exit`       Make woody-bot exit and stop listening.




