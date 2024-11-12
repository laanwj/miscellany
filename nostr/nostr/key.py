'''
Nostr signing/verifying utilities.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
import hashlib
import json

import secp256k1

def compute_event_hash(event) -> str:
    data = [0, event['pubkey'], event['created_at'], event['kind'], event['tags'], event['content']]
    data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(data_str.encode()).hexdigest()

def verify_sig(pubkey: str, hash: str, sig: str) -> bool:
    pk = secp256k1.PublicKey(b'\x02' + bytes.fromhex(pubkey), True)
    return pk.schnorr_verify(bytes.fromhex(hash), bytes.fromhex(sig), None, True)

def verify_event(event) -> bool:
    if compute_event_hash(event) != event['id']:
        return False
    return verify_sig(event['pubkey'], event['id'], event['sig'])

class NostrKey:
    def __init__(self, private_key):
        self.sk = secp256k1.PrivateKey(bytes.fromhex(private_key))
        self.public_key = self.sk.pubkey.serialize()[1:].hex()

    def sign_event(self, event):
        if event['pubkey'] != self.public_key:
            raise ValueError('Unknown pubkey')
        event['id'] = compute_event_hash(event)

        sig = self.sk.schnorr_sign(bytes.fromhex(event['id']), None, raw=True)
        event['sig'] = sig.hex()
