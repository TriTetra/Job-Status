"""Cross-cutting infrastructure used by every layer: settings, logging, LLM access.

Nothing in here knows about jobs, resumes or users — only how to talk to the
outside world and how the app is configured.
"""
