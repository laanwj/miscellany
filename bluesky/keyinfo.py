#!/usr/bin/python3
'''Print some info about a bluesky key'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
# pip install secp256k1
import sys

import base58
import secp256k1

PREFIX_SECP256K1_PUB = bytes([0xe7, 0x01])
PREFIX_SECP256K1_PRIV = bytes([0x81, 0x26])
PREFIX_SECP256R1_PUB = bytes([0x80, 0x24])
PREFIX_SECP256R1_PRIV = bytes([0x86, 0x26])

def main():
    key_str = sys.argv[1]

    key_str = key_str.removeprefix('did:key:')

    assert key_str[0] == 'z'
    data = base58.b58decode(key_str[1:])

    if data[0:2] == PREFIX_SECP256K1_PUB:
        print('pubkey [secp256k1]')
        print(f'pubhex {data[2:].hex()}')
    elif data[0:2] == PREFIX_SECP256K1_PRIV:
        pk = secp256k1.PrivateKey(data[2:])
        pubkey = pk.pubkey.serialize()
        pubkey_multibase = 'z' + base58.b58encode(PREFIX_SECP256K1_PUB + pubkey)

        print('privkey [secp256k1]')
        print(f'privhex {data[2:].hex()}')

        print(f'pubhex {pubkey.hex()}')
        print(f'pubmult did:key:{pubkey_multibase}')
    elif data[0:2] == PREFIX_SECP256R1_PUB:
        print('pubkey [secp256r1]')
        print(f'pubhex {data[2:].hex()}')
    elif data[0:2] == PREFIX_SECP256R1_PRIV:
        print('privkey [secp256r1]')
        print(f'privhex {data[2:].hex()}')
    else:
        print('unknown')

if __name__ == '__main__':
    main()

