"""Onboarding — the wizard that turns a new sign-up into a Career Graph.

    profile.py       user record, identity (current role), goals, state machine
    resume_upload.py store the uploaded CV and run the extraction job
    career_graph.py  evidence_items → Career Graph (pure build + persistence job)

State machine: NOT_STARTED → IDENTITY → GOALS → EVIDENCE → CONNECTIONS → BUILDING → READY
"""

from careeros.shared.background import JobStore

# CV extraction and graph-building jobs, polled by the wizard
onboarding_jobs = JobStore()
