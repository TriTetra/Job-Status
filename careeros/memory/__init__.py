"""Person memory: one append-only log of what happened with the person, and why.

Every write path records an event (`events.record`) in the same transaction as its
own table change; modules read projections built from it. See docs/v1/PERSON_MEMORY.md.
"""
