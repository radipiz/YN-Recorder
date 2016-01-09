# YN-Recorder
Gets Paramateres to record Livestreams and Records from YouNow

## Features
* Recording live streams
* Download records
* Listing Records 

## Requirements
* Python 3
* requests
* rtmpdump 2.3 binary in working directory (Version 2.4 won't work)

## Usage
```
./ynrecord.py  [-h] [--yes] [--onlylive] Username/Recordurl
```
Enter a username and the program checks, if the user is streaming right now. It will offer to start dumping the stream.
You can modify the behaviour of this with the parameters `--yes` to tell the program to start downloading a livestream automatically.
`--onlylive` checks if the user is streaming and if so, it ask to download it (see `--yes`). After checking and a possible download, it will exit.

Otherwise you can enter an full URL to an record as `start` parameter. The program will download it.

## Notice
This is program does not claim to be well done or stable. Use it a your own risk.
Also this tool does not belong to YouNow in any relationship. It just works with their website. So do not abuse it!
