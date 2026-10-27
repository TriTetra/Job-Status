"""Countries, visas and salary ranges from infra/seeds/v1/{countries,visa,salaries}/*.yaml.

Idempotent (merge / update-in-place). Run via `career-os seed reference`.
"""

import logging

import sqlalchemy as sa
import yaml

from careeros.db.connection import db
from careeros.shared.config import ROOT
from careeros.knowledge.models.country import Country
from careeros.knowledge.models.salary_range import SalaryRange
from careeros.knowledge.models.visa import Visa

logger = logging.getLogger(__name__)
SEEDS = ROOT / "infra" / "seeds" / "v1"


def seed_countries() -> int:
    count = 0
    countries_dir = SEEDS / "countries"
    if not countries_dir.exists():
        logger.warning("Seed directory not found: %s", countries_dir)
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

    logger.info("Seeded %d countries", count)
    return count


def seed_visas() -> int:
    count = 0
    visas_dir = SEEDS / "visa"
    if not visas_dir.exists():
        logger.warning("Seed directory not found: %s", visas_dir)
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

    logger.info("Seeded %d visas", count)
    return count


def seed_salaries() -> int:
    count = 0
    salaries_dir = SEEDS / "salaries"
    if not salaries_dir.exists():
        logger.warning("Seed directory not found: %s", salaries_dir)
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

    logger.info("Seeded %d salary ranges", count)
    return count
