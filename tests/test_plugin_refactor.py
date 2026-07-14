"""
Test: Plugin + Config-Driven Refactor

Checks:
  1. config/plugins.yaml loads correctly
  2. HiringAgentPlugin instantiates
  3. Plugin reads confidence formula from config (no hardcodes)
  4. list_available_parsers() works
  5. EvidenceBuilder accepts plugin (structural test, no DB write)
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(_ROOT))


def main() -> None:
    print("=" * 60)
    print("Plugin Refactor Test")
    print("=" * 60)

    # 1. Config loads
    from core.config import load_plugin_config
    cfg = load_plugin_config()
    assert "resume_parsers" in cfg, "Missing resume_parsers in plugins.yaml"
    assert "hiring-agent" in cfg["resume_parsers"], "Missing hiring-agent config"
    ha_cfg = cfg["resume_parsers"]["hiring-agent"]
    print("1. config/plugins.yaml OK")

    # 2. Confidence formula readable
    conf = ha_cfg["confidence_formula"]
    assert conf["base_divisor"] == 100
    assert conf["commit_bonus_max"] == 0.20
    assert conf["star_bonus_max"] == 0.10
    assert conf["production_weight"] == 0.20
    print(f"   confidence_formula: {conf}")
    print("2. Confidence formula from config OK")

    # 3. Enrichment keys readable
    keys = ha_cfg["enrichment_keys"]
    assert "total_score" in keys
    assert "github_repos" in keys
    print(f"   enrichment_keys ({len(keys)} keys) OK")
    print("3. Enrichment keys from config OK")

    # 4. Plugin instantiates
    from plugins.resume_parsers.hiring_agent import HiringAgentPlugin
    plugin = HiringAgentPlugin()
    meta = plugin.get_metadata()
    assert meta["name"] == "hiring-agent"
    print(f"4. HiringAgentPlugin OK — install_dir: {meta['install_dir']}")

    # 5. list_available_parsers
    from plugins.plugin_loader import list_available_parsers
    parsers = list_available_parsers()
    assert "hiring-agent" in parsers
    print(f"5. list_available_parsers OK — {list(parsers)}")

    # 6. load_parser_plugin factory
    from plugins.plugin_loader import load_parser_plugin
    p = load_parser_plugin("hiring-agent")
    assert p.get_metadata()["name"] == "hiring-agent"
    print("6. load_parser_plugin('hiring-agent') OK")

    # 7. EvidenceBuilder accepts plugin (no parse, no DB)
    from services.resume_intelligence.application.evidence_builder import EvidenceBuilder
    builder = EvidenceBuilder(plugin)
    assert builder._conf_cfg["base_divisor"] == 100
    print("7. EvidenceBuilder(plugin) OK — reads config, no hardcodes")

    # 8. ResumeData structure
    from plugins.plugin_interface import ResumeData
    dummy = ResumeData(
        open_source=0, self_projects=25, production=20, technical_skills=10,
        total=55, total_max=100, bonus_points=0, deductions=0,
        total_work_experience=1, total_education=1,
        total_skills=15, total_projects=4,
        github_repos=10, github_followers=5, github_following=10,
    )
    conf_val = builder._confidence(commits=50, stars=20, rd=dummy)
    expected = min(10/100 + min(50/100, 0.20) + min(20/50, 0.10) + (20/100)*0.20, 1.0)
    assert abs(conf_val - expected) < 1e-9, f"{conf_val} != {expected}"
    print(f"8. _confidence() formula correct: {conf_val:.4f}")

    print()
    print("=" * 60)
    print("All tests passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
