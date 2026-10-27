"""
Enrich evidence table with real GitHub metrics.

Usage:
    python scripts/enrich_github_evidence.py [--user USER_ID]
"""

import argparse



from core.db.connection import db
from core.db.repositories import EvidenceRepository
from plugins.enrichment.github.evidence_enricher import EvidenceEnricher
from plugins.enrichment.github.client import GitHubClient


def main():
    parser = argparse.ArgumentParser(description="Enrich evidence with GitHub metrics")
    parser.add_argument("--user", default="default", help="User ID")
    args = parser.parse_args()

    print("=" * 60)
    print("  GitHub Evidence Enrichment")
    print("=" * 60)

    # Show rate limit before
    try:
        client = GitHubClient()
        rate = client.check_rate_limit()
        print(f"\nGitHub API: {rate['remaining']}/{rate['limit']} calls remaining")
        print(f"Reset at: {rate['reset']}\n")
    except Exception as e:
        print(f"Warning: could not check rate limit: {e}\n")

    enricher = EvidenceEnricher(user_id=args.user)

    print(f"Enriching projects for user '{args.user}'...")
    enriched = enricher.enrich_all_projects()

    print(f"\nEnriched {enriched} projects.")

    # Show updated confidence scores
    print("\nUpdated skill confidence scores:")
    with db.session_scope() as session:
        repo = EvidenceRepository(session)
        summary = repo.skill_summary(args.user)
        for skill, stats in sorted(summary.items(), key=lambda x: x[1]["avg_confidence"], reverse=True)[:10]:
            bar = "#" * int(stats["avg_confidence"] * 20)
            print(f"  {skill:<25} {stats['avg_confidence']:.2f}  {bar}")

    print("\nDone. Regenerate CVs:")
    print("  python -m services.resume_intelligence.cli generate -c Google -t 'ML Engineer' -T ml_research")


if __name__ == "__main__":
    from shared.logging import configure_logging

    configure_logging()
    main()
