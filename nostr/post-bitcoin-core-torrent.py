#!/usr/bin/python3
'''
Auto-post bitcoin core torrent as a nostr note (https://github.com/nostr-protocol/nips/blob/master/35.md).
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
# uses built-in bencode implementation ported from python 2.7 code by Petru Paler
import argparse
import hashlib
import json
import os

import bencode
from nostr.key import NostrKey
from nostr.util import encode_naddr, encode_nevent
from nostr.client import send_to_relays

def compute_info_hash(torrent):
    '''
    Compute the torrent "info hash" as used in magnet links.
    '''
    # from: https://stackoverflow.com/a/4173411
    return hashlib.sha1(bencode.bencode(torrent[b'info'])).hexdigest()

def parse_args():
    parser = argparse.ArgumentParser(
        description='Post bitcoin torrent to nostr.',
    )
    parser.add_argument('-p', dest='test', action='store_false', help="Run in production mode instead of test mode")
    parser.add_argument('-b', dest='broadcast', action='store_true', help="Broadcast to relays")
    parser.add_argument('torrent', help="Torrent file to load")

    return parser.parse_args()

def main():
    args = parse_args()
    if args.test:
        from auth.testkey import private_key, RELAYS
        print('[running in test mode]')
        test_prefix = '[test] '
    else:
        from auth.corekey import private_key, RELAYS
        print('[running in production mode]')
        test_prefix = ''

    key = NostrKey(private_key)

    with open(args.torrent, 'rb') as f:
        torrent_data = f.read()
    torrent = bencode.bdecode(torrent_data)
    info = torrent[b'info']
    info_hash = compute_info_hash(torrent)
    print(f'hash {info_hash}')

    # use file mtime (wget sets this) from the torrent file as timestamp
    created_at = int(os.stat(args.torrent).st_mtime)

    # torrent comment as event content
    content = torrent[b'comment'].decode('utf-8')
    if args.test:
        content = '# TEST\n\n' + content

    # build tags
    tags = [
        ['title', content],
        ['x', info_hash],
        ['t', 'application'],
        ['t', 'bitcoin'],
    ]
    # add file information
    for file_info in info[b'files']:
        file_name = (b'/'.join(file_info[b'path'])).decode('utf-8')
        file_size = file_info[b'length']
        tags.append(['file', file_name, str(file_size)])

    # parse trackers from a list of lists into a set
    trackers = set()
    for announce_info in torrent[b'announce-list']:
        for tracker in announce_info:
            trackers.add(tracker.decode('utf8'))

    # add trackers
    for tracker in sorted(trackers):
        tags.append(['tracker', tracker])

    event = {
        'pubkey': key.public_key,
        'created_at': created_at,
        'kind': 2003,
        'tags': tags,
        'content': content,
    }
    #print(event)

    key.sign_event(event)
    print('event size is', len(json.dumps(event)))
    print('created', encode_nevent(event['id'], relays=RELAYS))

    if args.broadcast:
        send_to_relays(RELAYS, event)
        print(f'broadcasted to relays: {RELAYS}')

if __name__ == '__main__':
    main()

