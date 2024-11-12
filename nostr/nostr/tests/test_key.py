from nostr.key import *

def test_verify():
    event = {
        'pubkey': 'b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816',
        'created_at': 1731409010,
        'kind': 1,
        'tags': ['t', 'test'],
        'content': "#test message",
    }
    assert compute_event_hash(event) == '562ba36da0dd47b202e6c95c4aad2ba12997b8f86b2d353b08b4f0d59d179985'

    signed_event = event.copy()
    signed_event['id'] = '562ba36da0dd47b202e6c95c4aad2ba12997b8f86b2d353b08b4f0d59d179985'
    signed_event['sig'] = '1de8a6099df2d60aa7ed3471031a36fb97b7f091ef6c57b11f4346888d209902cb882274c0d448cd12c4f587eac65feae23c80bc27ea1530decae365cef7371c'
    assert verify_event(signed_event)

    corrupted_event = signed_event.copy()
    corrupted_event['content'] = 'fake'
    assert not verify_event(corrupted_event)

    assert verify_sig('b7b4ee1454af66f017ef672cce681f37bafaee57ab1b899acc40176b2b537816', '562ba36da0dd47b202e6c95c4aad2ba12997b8f86b2d353b08b4f0d59d179985', '1de8a6099df2d60aa7ed3471031a36fb97b7f091ef6c57b11f4346888d209902cb882274c0d448cd12c4f587eac65feae23c80bc27ea1530decae365cef7371c')
