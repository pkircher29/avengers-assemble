import unittest

from message_protocol import validate_envelope


def make_envelope(**overrides):
    envelope = {
        "id": "task-1",
        "sender": "Chuck",
        "recipient": "Claude",
        "prompt": "Do the thing",
        "model": "claude-sonnet-5",
        "effort": "medium",
    }
    envelope.update(overrides)
    return envelope


class ValidEnvelopeTests(unittest.TestCase):
    def test_valid_envelope_returns_normalized_copy(self):
        envelope = make_envelope()
        result = validate_envelope(envelope)
        self.assertEqual(result, envelope)
        self.assertIsNot(result, envelope)


class MissingFieldTests(unittest.TestCase):
    def test_missing_id(self):
        envelope = make_envelope()
        del envelope["id"]
        with self.assertRaisesRegex(ValueError, "missing required field: id"):
            validate_envelope(envelope)

    def test_missing_sender(self):
        envelope = make_envelope()
        del envelope["sender"]
        with self.assertRaisesRegex(ValueError, "missing required field: sender"):
            validate_envelope(envelope)

    def test_missing_recipient(self):
        envelope = make_envelope()
        del envelope["recipient"]
        with self.assertRaisesRegex(ValueError, "missing required field: recipient"):
            validate_envelope(envelope)

    def test_missing_prompt(self):
        envelope = make_envelope()
        del envelope["prompt"]
        with self.assertRaisesRegex(ValueError, "missing required field: prompt"):
            validate_envelope(envelope)

    def test_missing_model(self):
        envelope = make_envelope()
        del envelope["model"]
        with self.assertRaisesRegex(ValueError, "missing required field: model"):
            validate_envelope(envelope)

    def test_missing_effort(self):
        envelope = make_envelope()
        del envelope["effort"]
        with self.assertRaisesRegex(ValueError, "missing required field: effort"):
            validate_envelope(envelope)


class InvalidFieldTests(unittest.TestCase):
    def test_not_a_dict(self):
        with self.assertRaisesRegex(ValueError, "envelope must be a dict"):
            validate_envelope("not-a-dict")

    def test_empty_id(self):
        envelope = make_envelope(id="")
        with self.assertRaisesRegex(ValueError, "field 'id' must be a non-empty string"):
            validate_envelope(envelope)

    def test_non_string_id(self):
        envelope = make_envelope(id=123)
        with self.assertRaisesRegex(ValueError, "field 'id' must be a non-empty string"):
            validate_envelope(envelope)

    def test_wrong_sender(self):
        envelope = make_envelope(sender="Paul")
        with self.assertRaisesRegex(ValueError, "field 'sender' must be exactly 'Chuck'"):
            validate_envelope(envelope)

    def test_wrong_recipient(self):
        envelope = make_envelope(recipient="Bridge")
        with self.assertRaisesRegex(ValueError, "field 'recipient' must be exactly 'Claude'"):
            validate_envelope(envelope)

    def test_empty_prompt(self):
        envelope = make_envelope(prompt="")
        with self.assertRaisesRegex(ValueError, "field 'prompt' must be a non-empty string"):
            validate_envelope(envelope)

    def test_empty_model(self):
        envelope = make_envelope(model="")
        with self.assertRaisesRegex(ValueError, "field 'model' must be a non-empty string"):
            validate_envelope(envelope)

    def test_invalid_effort(self):
        envelope = make_envelope(effort="extreme")
        with self.assertRaisesRegex(
            ValueError, "field 'effort' must be one of 'low', 'medium', 'high'"
        ):
            validate_envelope(envelope)


class UnexpectedFieldTests(unittest.TestCase):
    def test_unexpected_field_rejected(self):
        envelope = make_envelope(extra="not allowed")
        with self.assertRaisesRegex(ValueError, "unexpected field: extra"):
            validate_envelope(envelope)


class DuplicateIdTests(unittest.TestCase):
    def test_duplicate_id_rejected(self):
        seen_ids = set()
        first = make_envelope(id="dup-1")
        second = make_envelope(id="dup-1")
        validate_envelope(first, seen_ids=seen_ids)
        with self.assertRaisesRegex(ValueError, "duplicate id: dup-1"):
            validate_envelope(second, seen_ids=seen_ids)

    def test_distinct_ids_allowed(self):
        seen_ids = set()
        first = make_envelope(id="task-a")
        second = make_envelope(id="task-b")
        validate_envelope(first, seen_ids=seen_ids)
        validate_envelope(second, seen_ids=seen_ids)
        self.assertEqual(seen_ids, {"task-a", "task-b"})

    def test_no_seen_ids_allows_repeats(self):
        envelope = make_envelope(id="task-x")
        validate_envelope(envelope)
        validate_envelope(envelope)


if __name__ == "__main__":
    unittest.main()
