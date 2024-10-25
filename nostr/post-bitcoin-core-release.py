#!/usr/bin/python3
'''
Auto-post bitcoin core release post as a longform nostr note.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
import argparse
import json
import re
import sys
import time
import datetime

import yaml
from nostr.key import NostrKey
from nostr.util import encode_naddr, encode_nevent
from nostr.client import send_to_relays

def load_jekyll(source):
    '''
    Load and split Jekyll yaml file into metadata and content part.
    '''
    with open(source, 'r') as f:
        documents = []
        for line in f.readlines():
            line = line.rstrip('\n')
            if line == '---' and len(documents) < 2:
                doc = []
                documents.append(doc)
            else:
                doc.append(line)
        for i in range(len(documents)):
            documents[i] = '\n'.join(documents[i])

    metadata = yaml.safe_load(documents[0])
    content = documents[1]
    return(metadata, content)

def filter_jekyll_macros(content):
    '''
    Filter out jekyll macros and pragmas.
    '''
    lines = content.split('\n')
    lines = (l for l in lines if not l.startswith('{%'))
    return '\n'.join(lines)

MIDDLE_OF_DAY = datetime.time(12, 0, tzinfo=datetime.UTC)
def middle_of_day(d):
    '''
    Return integer timestamp for 12:00 UTC on the date provided.
    '''
    return int(datetime.datetime.combine(d, MIDDLE_OF_DAY).timestamp())

def parse_args():
    parser = argparse.ArgumentParser(
        description='Post bitcoin release notes to nostr.',
    )
    parser.add_argument('-p', dest='test', action='store_false', help="Run in production mode instead of test mode")
    parser.add_argument('-u', dest='update_mode', action='store_true', help="Use update mode instead of creation mode")
    parser.add_argument('-b', dest='broadcast', action='store_true', help="Broadcast to relays")
    parser.add_argument('source', help="Jekyll markdown file to source from")

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

    (metadata, content) = load_jekyll(args.source)
    content = filter_jekyll_macros(content)

    if args.test:
        content = '# TEST\n\n' + content

    # replace download links
    newspec = '- 🌐 <\\1>\n' + \
              '- 🧲 [Magnet link](' + metadata['optional_magnetlink'].replace('\\', '\\\\') + ')'
    (content, n) = re.subn('^\s*<(https://bitcoincore.org/bin/bitcoin-core-.*?/)>\s*$', newspec, content, count=1, flags=re.MULTILINE)
    if n != 1:
        print("Couldn't find download link to replace.")
        exit(1)

    published_at = middle_of_day(metadata['date'])

    tags = [
        ['d', metadata['id']],
        ['title', test_prefix + metadata['title']],
        ['summary', metadata['excerpt']],
        ['t', 'bitcoin'],
        ['t', 'release notes'],
        # ['image', ...],
        ['published_at', str(published_at)],
        # ['alt', ''],
    ]

    print(tags)

    event = {
        'pubkey': key.public_key,
        'created_at': published_at,
        'kind': 30023,
        'tags': tags,
        'content': content,
    }
    # use update mode if the post alrady exists, this will use the
    # current date for the event instead of the release date.
    if args.update_mode:
        event['created_at'] = int(time.time())

    key.sign_event(event)
    print('event size is', len(json.dumps(event)))
    print('created', encode_nevent(event['id'], relays=RELAYS))

    if args.broadcast:
        send_to_relays(RELAYS, event)
        print(f'broadcasted to relays: {RELAYS}')

    print('addr', encode_naddr(metadata['id'], relays=RELAYS, author=event['pubkey'], kind=event['kind']))

if __name__ == '__main__':
    main()
