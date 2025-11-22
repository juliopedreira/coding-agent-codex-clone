from feature_impl import deliver_feature

FEATURE = "Add a login mechanism"

def test_status_message():
    result = deliver_feature(FEATURE)
    assert result["status"] == "done"
    assert FEATURE in result["message"]

def test_idempotent_and_notes():
    a = deliver_feature(FEATURE)
    b = deliver_feature(FEATURE)
    assert a == b
    assert "notes" in a and FEATURE in a["notes"]
