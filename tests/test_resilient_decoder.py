from receiver.decoder import ResilientH264Decoder


class FakeDecoder:
    def __init__(self, behavior):
        self.behavior = list(behavior)
        self.calls = []

    def decode(self, payload):
        self.calls.append(payload)
        result = self.behavior.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class Factory:
    def __init__(self, decoders):
        self.decoders = list(decoders)
        self.created = []

    def __call__(self):
        decoder = self.decoders.pop(0)
        self.created.append(decoder)
        return decoder


def test_decoder_drops_delta_frames_until_first_keyframe():
    decoder = FakeDecoder([["idr"]])
    factory = Factory([decoder])
    resilient = ResilientH264Decoder(factory)

    assert resilient.decode(b"p", is_keyframe=False) == []
    assert factory.created == []

    assert resilient.decode(b"idr", is_keyframe=True) == ["idr"]
    assert decoder.calls == [b"idr"]
    assert resilient.synced is True


def test_decoder_recovers_at_next_keyframe_after_invalid_data():
    broken = FakeDecoder([["idr"], ValueError("invalid data")])
    recovered = FakeDecoder([["fresh-idr"]])
    factory = Factory([broken, recovered])
    resilient = ResilientH264Decoder(factory)

    assert resilient.decode(b"idr-1", is_keyframe=True) == ["idr"]
    assert resilient.decode(b"bad-p", is_keyframe=False) == []
    assert resilient.synced is False
    assert resilient.decode(b"ignored-p", is_keyframe=False) == []
    assert resilient.decode(b"idr-2", is_keyframe=True) == ["fresh-idr"]
    assert resilient.recoveries == 1
