"""Validation for inbound task envelopes exchanged with the coordination bridge."""

REQUIRED_FIELDS = ("id", "sender", "recipient", "prompt", "model", "effort")
VALID_EFFORTS = ("low", "medium", "high")


def validate_envelope(value, seen_ids=None):
    """Validate a task envelope and return a normalized copy.

    Raises ValueError identifying the failing field/rule.
    """
    if not isinstance(value, dict):
        raise ValueError("envelope must be a dict")

    actual_fields = set(value.keys())
    required_fields = set(REQUIRED_FIELDS)

    unexpected = actual_fields - required_fields
    if unexpected:
        raise ValueError(f"unexpected field: {sorted(unexpected)[0]}")

    missing = required_fields - actual_fields
    if missing:
        raise ValueError(f"missing required field: {sorted(missing)[0]}")

    envelope_id = value["id"]
    if not isinstance(envelope_id, str) or not envelope_id:
        raise ValueError("field 'id' must be a non-empty string")

    if seen_ids is not None and envelope_id in seen_ids:
        raise ValueError(f"duplicate id: {envelope_id}")

    sender = value["sender"]
    if sender != "Chuck":
        raise ValueError("field 'sender' must be exactly 'Chuck'")

    recipient = value["recipient"]
    if recipient != "Claude":
        raise ValueError("field 'recipient' must be exactly 'Claude'")

    prompt = value["prompt"]
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("field 'prompt' must be a non-empty string")

    model = value["model"]
    if not isinstance(model, str) or not model:
        raise ValueError("field 'model' must be a non-empty string")

    effort = value["effort"]
    if effort not in VALID_EFFORTS:
        raise ValueError("field 'effort' must be one of 'low', 'medium', 'high'")

    if seen_ids is not None:
        seen_ids.add(envelope_id)

    return {
        "id": envelope_id,
        "sender": sender,
        "recipient": recipient,
        "prompt": prompt,
        "model": model,
        "effort": effort,
    }
