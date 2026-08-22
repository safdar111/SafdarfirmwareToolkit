from core.analyzer import Analyzer


def test_classify_health_ok():
    result = Analyzer.classify_health(
        {"ifd_health": {"status": "OK"}},
        {"version": "16.1.0.0", "status_text": "Clean / configured", "is_clean": True},
    )
    assert result["overall_status"] == "HEALTHY / STRUCTURE VALID"
    assert result["archive_ready"] is True
    assert result["repair_required"] is False


def test_classify_health_dirty():
    result = Analyzer.classify_health(
        {"ifd_health": {"status": "OK"}},
        {"version": "16.1.0.0", "status_text": "Dirty / initialized", "is_clean": False},
    )
    assert result["overall_status"] == "DIRTY / REPAIR RECOMMENDED"
    assert result["archive_ready"] is False
    assert result["repair_required"] is True
