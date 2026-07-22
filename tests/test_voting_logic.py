from models.records import VoteSummary


def test_majority_accepts():
    summary = VoteSummary(approve=4, reject=3, abstain=1, participants=8, eligible=10, required_for_quorum=5, quorum_reached=True)
    assert summary.accepted is True
    assert summary.is_tie is False


def test_tie_requires_founder():
    summary = VoteSummary(approve=3, reject=3, abstain=0, participants=6, eligible=8, required_for_quorum=4, quorum_reached=True)
    assert summary.is_tie is True


def test_no_quorum():
    summary = VoteSummary(approve=2, reject=1, abstain=0, participants=3, eligible=10, required_for_quorum=5, quorum_reached=False)
    assert summary.quorum_reached is False
