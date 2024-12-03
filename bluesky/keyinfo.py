#!/usr/bin/python3
'''Print some info about a bluesky key'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
# pip install secp256k1
import sys

import base58
import secp256k1

from util import PREFIX_SECP256K1_PUB, PREFIX_SECP256K1_PRIV, PREFIX_SECP256R1_PUB, PREFIX_SECP256R1_PRIV

def main():
    try:
        key_str = sys.argv[1]
    except IndexError:
        print(f'Please specify key', file=sys.stderr)
        exit(1)

    key_str = key_str.removeprefix('did:key:')

    assert key_str[0] == 'z'
    data = base58.b58decode(key_str[1:])

    prefix = data[0:2]
    keydata = data[2:]

    if prefix == PREFIX_SECP256K1_PUB:
        print('pubkey [secp256k1]')
        print(f'pubhex {keydata.hex()}')
    elif prefix == PREFIX_SECP256K1_PRIV:
        pk = secp256k1.PrivateKey(keydata)
        pubkey = pk.pubkey.serialize()
        pubkey_multibase = 'z' + base58.b58encode(PREFIX_SECP256K1_PUB + pubkey)

        print('privkey [secp256k1]')
        print(f'privhex {keydata.hex()}')

        print(f'pubhex {pubkey.hex()}')
        print(f'pubmult did:key:{pubkey_multibase}')
    elif prefix == PREFIX_SECP256R1_PUB:
        print('pubkey [secp256r1]')
        print(f'pubhex {keydata.hex()}')
    elif prefix == PREFIX_SECP256R1_PRIV:
        print('privkey [secp256r1]')
        print(f'privhex {keydata.hex()}')
    else:
        print('unknown')

if __name__ == '__main__':
    main()

