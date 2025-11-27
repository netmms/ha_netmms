# Snapserver Add-on Documentation

## What is Snapserver?
Snapserver is the server part of Snapcast: it receives audio from inputs (pipes, MPD, RTP, etc.) and distributes synchronized audio to Snapcast clients.

## Using a Pipe Source
1. Create a named pipe:
   ```bash
   ha> login
   # inside host shell:
   mkfifo /share/snapserver/stream
