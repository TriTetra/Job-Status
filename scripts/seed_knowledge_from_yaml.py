"""Seed knowledge DB tables from YAML files.

One-time migration. After this, DB is source of truth.
YAML files remain as version-controlled backup.

Usage:
    python scripts/seed_knowledge_from_yaml.py
"""

import sys
from pathlib import Path


try:
    from dotenv import load_dotenv
    for _env in [Path(".env"), Path("services/hiring-agent/.env")]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass

import yaml

from core.db.connection import db
from core.db.models import Country, SalaryRange, Visa


def seed_countries() -> int:
    count = 0
    countries_dir = Path("infra/seeds/v1/countries")
    if not countries_dir.exists():
        print(f"  Directory not found: {countries_dir}")
        return 0

    with db.session_scope() as session:
        for yaml_file in sorted(countries_dir.glob("*.yaml")):
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue

            iso_code = (data.get("iso_code") or yaml_file.stem[:2]).upper()
            visa_data = data.get("visa", {})
            tax_data = data.get("tax", {})
            work_data = data.get("work_culture", {})

            country = Country(
                iso_code=iso_code,
                name=data.get("country", yaml_file.stem),
                capital=data.get("capital"),
                currency=data.get("currency", "USD"),
                language=data.get("language"),
                english_proficiency=data.get("english_proficiency", "high"),
                tech_hubs=data.get("tech_hubs", []),
                primary_visa=visa_data.get("primary"),
                salary_threshold_eur=visa_data.get("salary_threshold_eur"),
                shortage_occupations=visa_data.get("shortage_occupations", []),
                visa_details={k: v for k, v in visa_data.items()
                              if k not in ("primary", "salary_threshold_eur", "shortage_occupations")},
                tax_info=tax_data,
                work_culture=work_data,
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                salary_ranges=data.get("salary_ranges", {}),
                data_source=f"yaml:{yaml_file.name}",
            )
            session.merge(country)
            count += 1

    print(f"  Seeded {count} countries")
    return count


def seed_visas() -> int:
    count = 0
    visas_dir = Path("infra/seeds/v1/visa")
    if not visas_dir.exists():
        print(f"  Directory not found: {visas_dir}")
        return 0

    country_map = {
        "United States": "US", "United Kingdom": "GB",
        "Germany": "DE", "Netherlands": "NL", "Canada": "CA",
    }

    with db.session_scope() as session:
        for yaml_file in sorted(visas_dir.glob("*.yaml")):
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue

            overview = data.get("overview", {})
            country_iso = country_map.get(data.get("country", ""))

            visa = Visa(
                visa_type=data.get("visa_type", yaml_file.stem),
                country=country_iso,
                category=data.get("category", "work_permit"),
                description=overview.get("description"),
                duration=overview.get("duration"),
                path_to_pr=overview.get("path_to_pr"),
                family_reunification=overview.get("family_reunification", True),
                eligibility=data.get("eligibility", {}),
                application=data.get("application", {}),
                alternatives=data.get("alternatives", data.get("comparison", {})),
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                best_for=data.get("best_for", []),
                data_source=f"yaml:{yaml_file.name}",
            )
            session.merge(visa)
            count += 1

    print(f"  Seeded {count} visas")
    return count


def seed_salaries() -> int:
    count = 0
    salaries_dir = Path("infra/seeds/v1/salaries")
    if not salaries_dir.exists():
        print(f"  Directory not found: {salaries_dir}")
        return 0

    with db.session_scope() as session:
        for yaml_file in sorted(salaries_dir.glob("*.yaml")):
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue

            role_family = data.get("role_family", yaml_file.stem)
            currency = data.get("currency", "USD")
            data_year = data.get("data_year", 2026)
            source = data.get("source")

            regions = (
                data.get("by_country")
                or data.get("by_region")
                or data.get("by_location")
                or {}
            )

            for region_name, levels in regions.items():
                if not isinstance(levels, dict):
                    continue

                is_country = len(region_name) == 2 and region_name.isupper()
                country_iso = region_name if is_country else None
                region_str = region_name if not is_country else None

                for level, salary_data in levels.items():
                    if not isinstance(salary_data, dict) or "min" not in salary_data:
                        continue

                    min_s = salary_data.get("min", 0)
                    max_s = salary_data.get("max", 0)
                    median = salary_data.get("median", (min_s + max_s) // 2)

                    import sqlalchemy as sa
                    existing = session.execute(
                        sa.select(SalaryRange).where(
                            SalaryRange.role_family == role_family,
                            SalaryRange.country == country_iso,
                            SalaryRange.region == region_str,
                            SalaryRange.level == level,
                        )
                    ).scalar_one_or_none()

                    if existing:
                        existing.min_salary = min_s
                        existing.max_salary = max_s
                        existing.median_salary = median
                        existing.data_year = data_year
                        existing.source = source
                    else:
                        session.add(SalaryRange(
                            role_family=role_family,
                            country=country_iso,
                            region=region_str,
                            level=level,
                            min_salary=min_s,
                            max_salary=max_s,
                            median_salary=median,
                            currency=currency,
                            data_year=data_year,
                            source=source,
                            top_companies=salary_data.get("top_companies", {}),
                        ))
                    count += 1

    print(f"  Seeded {count} salary ranges")
    return count


def main():
    print("=" * 60)
    print("  Seed Knowledge from YAML")
    print("=" * 60)

    countries = seed_countries()
    visas = seed_visas()
    salaries = seed_salaries()

    print(f"\n  Total: {countries + visas + salaries} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
