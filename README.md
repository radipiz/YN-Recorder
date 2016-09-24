# YN-Recorder
Gets Parameters to dump livestreams and records from YouNow.

## Features
* Recording live streams
* Downloading records

## Requirements
* Python 3
* requests

## Usage
```
./ynrecord.py  [-h] [--yes] [--onlylive] Username/Recordurl
```
Enter a username and the program checks if the user is streaming right now. It will offer to start dumping the stream. You can modify the behaviour of the startup by changing the parameters `--yes` to tell the program to start downloading a livestream without further userinteraction.
Use `--onlylive` to check if the user is streaming and if so it offers you to download it (see `--yes`). When it's finished it will exit.

Otherwise you can enter an full URL to a record as `start` parameter. The program will then start to download it.

## Notice
This is program does not claim to be well done or stable. Use it a your own risk.
Also this tool does not belong to YouNow in any relationship. It just works with their website. So do not abuse it!
