"""careeros.shared.background — job tracking used by scan, CV extraction and graph build."""

from datetime import datetime, timedelta

import pytest

from careeros.shared.background import JobForbidden, JobNotFound, JobStore


def test_create_and_poll_owned_job():
    store = JobStore()
    job = store.create("user_a", label="scan")
    assert store.get_owned(job.job_id, "user_a") is job


def test_other_users_cannot_poll():
    store = JobStore()
    job = store.create("user_a")
    with pytest.raises(JobForbidden):
        store.get_owned(job.job_id, "user_b")


def test_unknown_job():
    with pytest.raises(JobNotFound):
        JobStore().get("nope")


def test_wire_format_matches_what_the_web_polls():
    job = JobStore().create("user_a")
    job.update(status="scanning", progress=30)
    job.log("Scanning…")
    d = job.to_dict()
    assert set(d) == {"job_id", "status", "progress", "logs", "result", "error", "created_at"}
    assert d["status"] == "scanning" and d["progress"] == 30
    assert d["logs"][0]["message"] == "Scanning…" and d["logs"][0]["type"] == "info"
    assert "owner_id" not in d  # never echo the user id back


def test_fail_records_error_and_log():
    job = JobStore().create("user_a")
    job.fail(ValueError("boom"))
    assert job.status == "failed" and job.error == "boom"
    assert job.logs[-1]["type"] == "error"


def test_finished_jobs_are_pruned_after_max_age():
    store = JobStore(max_age=timedelta(minutes=5))
    old_done = store.create("u")
    old_done.update(status="completed", created_at=datetime.utcnow() - timedelta(hours=1))
    old_running = store.create("u")
    old_running.update(status="scanning", created_at=datetime.utcnow() - timedelta(hours=1))

    store.create("u")  # creating triggers pruning

    with pytest.raises(JobNotFound):
        store.get(old_done.job_id)
    assert store.get(old_running.job_id) is old_running  # still running → kept
