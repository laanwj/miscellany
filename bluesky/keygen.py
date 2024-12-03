#!/usr/bin/python3
'''Generate bluesky key.'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
# pip install secp256k1
import os
import sys

import base58
import secp256k1

from util import PREFIX_SECP256K1_PUB, PREFIX_SECP256K1_PRIV, PREFIX_SECP256R1_PUB, PREFIX_SECP256R1_PRIV

def main():
    try:
        key_kind = sys.argv[1]
    except IndexError:
        print(f'Please specify algorithm: secp256k1 or secp256r1', file=sys.stderr)
        exit(1)

    if key_kind == 'secp256k1':
        prefix = PREFIX_SECP256K1_PRIV
        keydata = os.urandom(32)
    elif key_kind == 'secp256r1':
        prefix = PREFIX_SECP256R1_PRIV
        keydata = os.urandom(32)
    else:
        print(f'Unknown algorithm {key_kind}', file=sys.stderr)
        exit(1)

    privkey_multibase = 'z' + base58.b58encode(prefix + keydata)
    print(f'privhex {keydata.hex()}')
    print(f'privmult {privkey_multibase}')

    if prefix == PREFIX_SECP256K1_PRIV:
        pk = secp256k1.PrivateKey(keydata)
        pubkey = pk.pubkey.serialize()
        pubkey_multibase = 'z' + base58.b58encode(PREFIX_SECP256K1_PUB + pubkey)

        print(f'pubhex {pubkey.hex()}')
        print(f'pubmult did:key:{pubkey_multibase}')

if __name__ == '__main__':
    main()


