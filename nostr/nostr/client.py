'''
Nostr relay client utilties.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
import json
import websocket

def send_to_relays(relays, event):
    '''
    Send event to relays.
    '''
    message = json.dumps(['EVENT', event])

    for relay_url in relays:
        try:
            relay = websocket.create_connection(relay_url)
            relay.send(message)
            relay.close()
        except Exception as e:
            print(f'Failed to send to {relay_url}: {e}')

