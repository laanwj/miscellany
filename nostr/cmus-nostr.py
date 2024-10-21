#!/usr/bin/python3
'''
Publish music playing events from cmus to nostr.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
# pip install pycmus secp256k1 websocket-client
import pathlib
import time

from nostr.key import NostrKey
from nostr.client import send_to_relays

import pycmus.remote

# cmus polling frequency in seconds.
POLL_TIME = 5

# Example status output from cmus:
'''
{
    "tag": {
        "artist": "Ada Rook",
        "album": "PHOSPHOR II CODED REMAINS",
        "title": "_BREATHE",
        "date": "2017",
        "tracknumber": "1",
        "albumartist": "Ada Rook",
        "comment": "Visit https://adarook.bandcamp.com",
        "replaygain_track_gain": "-12.7 dB"
    },
    "set": {
        "aaa_mode": "all",
        "continue": "true",
        "play_library": "true",
        "play_sorted": "false",
        "replaygain": "disabled",
        "replaygain_limit": "true",
        "replaygain_preamp": "0.000000",
        "repeat": "false",
        "repeat_current": "false",
        "shuffle": "off",
        "softvol": "false",
        "vol_left": "100",
        "vol_right": "100"
    },
    "status": "playing",
    "file": ".../Ada Rook - PHOSPHOR II CODED REMAINS/Ada Rook - PHOSPHOR II CODED REMAINS - 01 _BREATHE.mp3",
    "duration": "101",
}
'''

def get_description_from_status(status):
    if status['status'] == 'playing':
        tag = status.get('tag')
        if tag is None:
            return ''
        title = tag.get('title')
        album = tag.get('album')
        artist = tag.get('artist', tag.get('albumartist'))
        if artist is not None and album is not None and title is not None:
            return f'{artist} - {album} - {title}'
        elif artist is not None and title is not None:
            return f'{artist} - {title}'
        else: # try to get it from filename
            filename = pathlib.Path(status['file'])
            return filename.stem

    return ''

def make_music_status_event(key, description):
    '''
    Make NIP-38 user status event for currently playing music.
    '''
    event = {
        'pubkey': key.public_key,
        'created_at': int(time.time()),
        'kind': 30315,
        'tags': [['d', 'music']],
        # optional ref: ['r', 'spotify:...']
        'content': description,
    }
    return event

def main():
    from auth.musickey import private_key, RELAYS
    key = NostrKey(private_key)
    prev_description = None
    while True:
        try:
            cmus = pycmus.remote.PyCmus()
            status = cmus.get_status_dict()
            description = get_description_from_status(status)
        except (FileNotFoundError, ConnectionResetError): # could not connect to cmus
            description = ''

        if description != prev_description:
            # if changed, sign and post event
            event = make_music_status_event(key, description)
            key.sign_event(event)
            print(event)
            send_to_relays(RELAYS, event)

            prev_description = description

        time.sleep(POLL_TIME)

if __name__ == '__main__':
    main()
