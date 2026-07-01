"""Tests for tutor analysis policy."""

from home_tutor.services.llm.tutor_analysis_policy import (
    DataSource,
    TutorAnalysisPolicy,
    resolve_data_source,
)


def test_resolve_mock_from_metadata() -> None:
    meta = {"metadata": {"data_source": "mock", "student_profile": "score53"}}
    assert resolve_data_source(meta) == DataSource.MOCK


def test_resolve_live_by_default() -> None:
    meta = {"session_id": "x", "questions": []}
    assert resolve_data_source(meta) == DataSource.LIVE


def test_mock_policy_is_manual_only() -> None:
    policy = TutorAnalysisPolicy(data_source=DataSource.MOCK, save_token_mode=False)
    assert policy.should_prefetch_on_select() is False
    assert policy.should_auto_analyze_on_view({"analysis_status": "missing"}) is False
    assert policy.to_api_dict()["manual_only"] is True


def test_live_save_token_policy() -> None:
    policy = TutorAnalysisPolicy(data_source=DataSource.LIVE, save_token_mode=True)
    assert policy.should_prefetch_on_select() is False
    assert policy.should_auto_analyze_on_view({"analysis_status": "missing"}) is False
    assert policy.should_auto_analyze_on_view({"analysis_status": "ready", "stale": True}) is True


def test_live_eager_policy() -> None:
    policy = TutorAnalysisPolicy(data_source=DataSource.LIVE, save_token_mode=False)
    assert policy.should_prefetch_on_select() is True
    assert policy.should_auto_analyze_on_view({"analysis_status": "missing"}) is True
