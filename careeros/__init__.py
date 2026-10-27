"""CareerOS — one package, one folder per feature.

    shared/        config, LLM client, logging, background jobs, token crypto
    db/            Base, connection, model registry, migrations
    identity/      users, roles, preferences, GitHub account linking
    onboarding/    the sign-up wizard → Career Graph
    evidence/      proof behind skills (GitHub, CV, portfolio) in evidence_items
    jobs/          job sources, scoring, decisions, scan, opportunities
    applications/  application pipeline
    companies/     company profiles and interview memory
    market/        market signals (HN, TechCrunch) and refresh
    resume/        target-aware resume generation
    knowledge/     reference data: countries, visas, salaries, skill graph

A feature package holds its own models/, repositories/ and services; it may
import another feature's services or models, never its internals.
"""
