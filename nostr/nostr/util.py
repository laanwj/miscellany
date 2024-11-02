'''
General nostr encoding/decoding utilities.
'''
# W.J. van der Laan 2024
# SPDX-License-Identifier: MIT
import re
import struct

from . import bech32

EMBED_RE = re.compile('nostr:([0-9a-z]+)')

def parse_tlv(data):
    try:
        rv = {}
        ptr = 0
        while ptr < len(data):
            t = data[ptr]
            l = data[ptr + 1]
            if t not in rv:
                rv[t] = []
            rv[t].append(data[ptr + 2:ptr + 2 + l])
            ptr += 2 + l
        return rv
    except IndexError:
        return None

def encode_tlv(hrp, tlv):
    data = bytes()
    for t, values in tlv.items():
        for v in values:
            if isinstance(v, str):
                v = v.encode('utf-8')
            data += bytes([t, len(v)]) + v
    converted_bits = bech32.convertbits(data, 8, 5)
    return bech32.bech32_encode(hrp, converted_bits, bech32.Encoding.BECH32)

def embeds_to_tags(content):
    '''
    Returns 'p' tags for embedded user profiles, and a set of relays extracted
    from nprofiles.
    '''
    tags = []
    relays_out = set()
    for match in EMBED_RE.finditer(content):
        embed = match.group(1)
        try:
            rec = decode(embed)
        except ValueError: # invalid embed, just move on
            continue

        pubkey = rec.get('pubkey', None)
        event_id = rec.get('event_id', None)
        relays = rec.get('relays', [])

        if pubkey is not None:
            if relays: # if relay supplied, specify the first one
                tags.append(['p', pubkey.hex(), relays[0]])
            else: # no relay supplied
                tags.append(['p', pubkey.hex()])

        if event_id is not None: # create mention
            marker = 'mention'

            if len(relays) >= 1:
                relay = relays[0]
            else:
                relay = ''

            if pubkey:
                tags.append(['e', event_id.hex(), relay, marker, pubkey.hex()])
            else:
                tags.append(['e', event_id.hex(), relay, marker])

        relays_out.update(relays)

    return tags, relays_out

def encode_npub(pubkey):
    if isinstance(pubkey, str):
        pubkey = bytes.fromhex(pubkey)
    converted_bits = bech32.convertbits(pubkey, 8, 5)
    return bech32.bech32_encode("npub", converted_bits, bech32.Encoding.BECH32)

def encode_nprofile(h, relays=[]):
    if isinstance(h, str):
        h = bytes.fromhex(h)
    tlv = {0: [h], 1: relays}
    return encode_tlv("nprofile", tlv)

def encode_nevent(h, relays=[], author=None, kind=None):
    if isinstance(h, str):
        h = bytes.fromhex(h)
    tlv = {0: [h], 1: relays}
    if author is not None:
        if isinstance(author, str):
            author = bytes.fromhex(author)
        tlv[2] = [author]
    if kind is not None:
        tlv[3] = [struct.pack('>I', kind)]
    return encode_tlv("nevent", tlv)

def encode_naddr(h, relays=[], author=None, kind=None):
    tlv = {0: [h], 1: relays}
    if author is not None:
        if isinstance(author, str):
            author = bytes.fromhex(author)
        tlv[2] = [author]
    if kind is not None:
        tlv[3] = [struct.pack('>I', kind)]
    return encode_tlv("naddr", tlv)

def decode(embed):
    '''
    Decode public, non-deprecated NIP-19 data types.
    '''
    rv = {}
    (hrp, data, spec) = bech32.bech32_decode(embed, 1000)
    if hrp is None or data is None or spec is None:
        raise ValueError('not valid bech32')
    rv['hrp'] = hrp
    data = bytes(bech32.convertbits(data, 5, 8, False))

    if hrp == 'nprofile':
        tlv = parse_tlv(data)
        if tlv is None or 0x00 not in tlv or len(tlv[0x00][0]) != 32:
            raise ValueError('no valid tlv, no key, or invalid-length key')
        rv['pubkey'] = tlv[0x00][0]
        rv['relays'] = [relay.decode('utf8') for relay in tlv.get(0x01, [])]
    elif hrp == 'npub':
        if len(data) != 32:
            raise ValueError('invalid npub data length')
        rv['pubkey'] = data
    elif hrp == 'note':
        if len(data) != 32:
            raise ValueError('invalid note data length')
        rv['event_id'] = data
    elif hrp == 'nevent':
        tlv = parse_tlv(data)
        if tlv is None or 0x00 not in tlv or len(tlv[0x00][0]) != 32:
            raise ValueError('no valid tlv, no key, or invalid-length key')
        rv['event_id'] = tlv[0x00][0]
        rv['relays'] = [relay.decode('utf8') for relay in tlv.get(0x01, [])]
        if 0x02 in tlv:
            rv['pubkey'] = tlv[0x02][0]
    else:
        raise ValueError(f'invalid hrp {hrp}')

    return rv

def find_tag(event, tag, idx):
    n = 0
    for e in event['tags']:
        if e[0] == tag:
            if n == idx:
                return e[1:]
            else:
                n += 1
    return None

if __name__ == '__main__':
    print(embeds_to_tags('[test] Merged PR from laanwj (nostr:nprofile1qqsq4gu7tthengqq577mpdyezkxf90z25g8mvkf355ks2k67km0lwwqpzdmhxue69uhkummnw3ezu7psvchx7un8zn5kcn nostr:npub1p23eukh0nxsqpfaakz6fj9vvj27y4gs0kevnrffdq4d4adkl7uuq7crnl6): pr2 https://github.com/laanwj/test/pull/2'))
    print(embeds_to_tags('[test] Merged PR from laanwj (nostr:nprofile1qqsq4gu7tthengqq577mpdyezkxf90z25g8mvkf355ks2k67km0lwwqpz3mhxue69uhhyetvv9ujuerpd46hxtnfdur2ev7c): pr5 https://github.com/laanwj/test/pull/5'))
    print(embeds_to_tags('<nostr:nevent1qqsx4e0dsr3srcf0k45pgryhvdgu47wld0f7ylg5lg3tqfs7snmfs9cpzdmhxue69uhkummnw3ezu7psvchx7un8qy28wumn8ghj7un9d3shjtnyv9kh2uewd9hsz9thwden5te0wp6hyurvv4ex2mrp0yhxxmmd35rvfv>'))
    print(encode_nevent('6ae5ed80e301e12fb568140c976351caf9df6bd3e27d14fa22b0261e84f69817', ['wss://nostr.x0f.org'], 'b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816', 1))
    print(encode_npub('b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816'))
    print(encode_nprofile('b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816', relays=['wss://nostr.x0f.org']))
    print(encode_naddr('en-release-28.0', relays=['wss://nostr.x0f.org'], author='b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816', kind=30023))
    print(decode('nprofile1qqsq4gu7tthengqq577mpdyezkxf90z25g8mvkf355ks2k67km0lwwqpzdmhxue69uhkummnw3ezu7psvchx7un8zn5kcn'))
    print(decode('npub1p23eukh0nxsqpfaakz6fj9vvj27y4gs0kevnrffdq4d4adkl7uuq7crnl6'))
    print(decode('nevent1qqsr46hsp2e8fl4whjdxfhp2knnzjj088wmu3vh8x50xwaaercftckqhhvjk2'))
    print(decode('note10gvceh72dtwe9g2zscfmr6v75va9hd55uv8207g3g3ywknjaqrqs8rtr5w') == {'hrp': 'note', 'event_id': bytes.fromhex('7a198cdfca6add92a1428613b1e99ea33a5bb694e30ea7f9114448eb4e5d00c1')})
