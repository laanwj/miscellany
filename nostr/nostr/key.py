'''
Nostr private key utilities.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
import hashlib
import json

import secp256k1

class NostrKey:
    def __init__(self, private_key):
        self.sk = secp256k1.PrivateKey(bytes.fromhex(private_key))
        self.public_key = self.sk.pubkey.serialize()[1:].hex()

    def sign_event(self, event):
        if event['pubkey'] != self.public_key:
            raise ValueError('Unknown pubkey')
        data = [0, event['pubkey'], event['created_at'], event['kind'], event['tags'], event['content']]
        data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        event['id'] = hashlib.sha256(data_str.encode()).hexdigest()

        sig = self.sk.schnorr_sign(bytes.fromhex(event['id']), None, raw=True)
        event['sig'] = sig.hex()

