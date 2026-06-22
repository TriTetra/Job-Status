#!/usr/bin/env python3
"""
Skills Gap Analyzer
-------------------
Excel'den "Missing Skills" toplar ve öğrenme planı oluşturur.

Kullanım:
    python scripts/skills_gap_analyzer.py
"""

import openpyxl
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta
import json


# ============================================================================
# CONFIG
# ============================================================================

REPORTS_DIR = Path(__file__).parent.parent / "reports"
OUTPUT_DIR = Path(__file__).parent.parent / "learning_plan"

# Your current skills (from config.yaml)
YOUR_SKILLS = {
    'Machine Learning', 'Deep Learning', 'Computer Vision', 'PyTorch',
    'YOLOv8', 'OpenCV', 'NLP', 'LLM', 'Python', 'Rust', 'Java', 'Go',
    'Spring Boot', 'gRPC', 'REST API', 'Next.js', 'React', 'TypeScript'
}

# Learning resources for common skills
LEARNING_RESOURCES = {
    'AWS': {
        'priority': 'HIGH',
        'time_to_learn': '2-3 weeks',
        'free_resources': [
            'AWS Free Tier (hands-on)',
            'AWS Skill Builder (free courses)',
            'freeCodeCamp AWS tutorial (YouTube)',
            'Deploy ML model to AWS Lambda (project)'
        ],
        'quick_win': 'Deploy your YOLOv8 model to AWS Lambda + API Gateway',
        'portfolio_project': 'Real-time object detection API on AWS',
    },
    'Kubernetes': {
        'priority': 'HIGH',
        'time_to_learn': '2-3 weeks',
        'free_resources': [
            'Kubernetes.io tutorials',
            'Play with Kubernetes (free playground)',
            'TechWorld with Nana (YouTube)',
            'Minikube local setup'
        ],
        'quick_win': 'Deploy containerized ML model to local Kubernetes',
        'portfolio_project': 'Kubernetes deployment for inference service',
    },
    'Docker': {
        'priority': 'HIGH',
        'time_to_learn': '1 week',
        'free_resources': [
            'Docker official tutorial',
            'Docker for beginners (freeCodeCamp)',
            'Containerize existing project'
        ],
        'quick_win': 'Dockerize your YOLOv8 project',
        'portfolio_project': 'Multi-stage Docker build for ML app',
    },
    'Spark': {
        'priority': 'MEDIUM',
        'time_to_learn': '2 weeks',
        'free_resources': [
            'Databricks Community Edition',
            'PySpark tutorial (Kaggle)',
            'Process large dataset project'
        ],
        'quick_win': 'Data preprocessing pipeline with PySpark',
        'portfolio_project': 'Large-scale data processing for ML',
    },
    'Scala': {
        'priority': 'LOW',
        'time_to_learn': '3-4 weeks',
        'free_resources': [
            'Scala official docs',
            'Rock the JVM (YouTube)',
            'Simple Scala project'
        ],
        'quick_win': 'Basic Scala + Spark integration',
        'portfolio_project': 'Scala-based data pipeline',
    },
    'TensorFlow': {
        'priority': 'MEDIUM',
        'time_to_learn': '1-2 weeks',
        'free_resources': [
            'TensorFlow official tutorials',
            'Convert PyTorch model to TensorFlow',
            'TensorFlow Lite for mobile'
        ],
        'quick_win': 'Port existing PyTorch model to TensorFlow',
        'portfolio_project': 'TensorFlow deployment comparison',
    },
    'GCP': {
        'priority': 'MEDIUM',
        'time_to_learn': '2 weeks',
        'free_resources': [
            'GCP Free Tier',
            'Google Cloud Skills Boost',
            'Deploy to Cloud Run'
        ],
        'quick_win': 'Deploy ML API to Google Cloud Run',
        'portfolio_project': 'Multi-cloud deployment (AWS + GCP)',
    },
    'Azure': {
        'priority': 'MEDIUM',
        'time_to_learn': '2 weeks',
        'free_resources': [
            'Azure Free Tier',
            'Microsoft Learn',
            'Azure ML Studio basics'
        ],
        'quick_win': 'Deploy model to Azure Functions',
        'portfolio_project': 'Azure ML pipeline',
    },
}


# ============================================================================
# FUNCTIONS
# ============================================================================

def find_latest_excel():
    """En son Excel'i bul"""
    excel_files = list(REPORTS_DIR.rglob("applypilot_advanced_*.xlsx"))
    if not excel_files:
        return None
    return max(excel_files, key=lambda p: p.stat().st_mtime)


def extract_missing_skills():
    """Excel'den missing skills topla"""

    excel_path = find_latest_excel()
    if not excel_path:
        print("❌ Excel bulunamadı!")
        return None, None

    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb["🎯 Perfect Match (8+)"]

    all_missing = []
    all_requirements = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1]:  # No title
            continue

        missing_skills = row[11]  # Missing Skills column
        requirements = row[9]  # Requirements column

        if missing_skills:
            # Split by comma
            skills = [s.strip() for s in missing_skills.split(',')]
            all_missing.extend(skills)

        if requirements:
            all_requirements.append(requirements)

    wb.close()

    return all_missing, all_requirements


def analyze_skills_gap():
    """Skills gap analizi yap"""

    print("\n" + "=" * 70)
    print("  📊 SKILLS GAP ANALYSIS")
    print("=" * 70 + "\n")

    missing_skills, requirements = extract_missing_skills()

    if not missing_skills:
        print("❌ No missing skills found!")
        return

    # Count frequencies
    skill_freq = Counter(missing_skills)

    # Filter out noise (empty, "none", very rare)
    skill_freq = {k: v for k, v in skill_freq.items()
                  if k.lower() not in ['none', '', 'n/a'] and v >= 2}

    if not skill_freq:
        print("✅ No significant skill gaps!")
        return

    # Sort by frequency
    sorted_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)

    print("🎯 MOST REQUESTED MISSING SKILLS:")
    print("-" * 70)

    top_skills = []

    for i, (skill, count) in enumerate(sorted_skills[:15], 1):
        pct = count / 30 * 100  # Out of 30 perfect match jobs

        priority = "🔥 HIGH" if count >= 10 else "⭐ MED" if count >= 5 else "💡 LOW"

        print(f"{i:2}. {skill:30} | {count:2} jobs ({pct:4.1f}%) | {priority}")

        if count >= 5:  # Focus on skills requested in 5+ jobs
            top_skills.append((skill, count))

    print()
    print("=" * 70)
    print()

    # Generate learning plan
    generate_learning_plan(top_skills)

    # Save to file
    save_analysis(sorted_skills, requirements)


def generate_learning_plan(top_skills):
    """8-haftalık öğrenme planı oluştur"""

    print("📚 8-WEEK LEARNING PLAN:")
    print("-" * 70)

    if not top_skills:
        print("✅ No major gaps - focus on deepening existing skills!")
        return

    # Prioritize
    high_priority = [s for s in top_skills if s[1] >= 10]
    medium_priority = [s for s in top_skills if 5 <= s[1] < 10]

    week = 1
    plan = {}

    # Week 1-2: Highest priority
    for skill, count in high_priority[:1]:  # Top 1
        skill_name = skill.strip()

        resources = LEARNING_RESOURCES.get(skill_name, {
            'priority': 'HIGH',
            'time_to_learn': '2 weeks',
            'free_resources': [f'Search: "{skill_name} tutorial free"'],
            'quick_win': f'Build small {skill_name} project',
            'portfolio_project': f'{skill_name} integration demo'
        })

        plan[f'Week {week}-{week+1}'] = {
            'skill': skill_name,
            'frequency': count,
            'goal': resources.get('quick_win'),
            'resources': resources.get('free_resources'),
            'output': resources.get('portfolio_project')
        }

        print(f"\n{'🔥' if resources.get('priority') == 'HIGH' else '⭐'} Week {week}-{week+1}: {skill_name.upper()}")
        print(f"   Requested by: {count} jobs")
        print(f"   Time needed: {resources.get('time_to_learn')}")
        print(f"   Quick win: {resources.get('quick_win')}")
        print(f"   Portfolio project: {resources.get('portfolio_project')}")

        week += 2

    # Week 3-4: Second priority
    if week <= 8 and len(high_priority) > 1:
        skill, count = high_priority[1]
        skill_name = skill.strip()

        resources = LEARNING_RESOURCES.get(skill_name, {
            'time_to_learn': '2 weeks',
            'quick_win': f'Build {skill_name} project',
            'portfolio_project': f'{skill_name} demo'
        })

        plan[f'Week {week}-{week+1}'] = {
            'skill': skill_name,
            'frequency': count,
            'goal': resources.get('quick_win'),
        }

        print(f"\n⭐ Week {week}-{week+1}: {skill_name.upper()}")
        print(f"   Requested by: {count} jobs")
        print(f"   Quick win: {resources.get('quick_win')}")

        week += 2

    # Week 5-6: Medium priority or deepen existing
    if week <= 8:
        if medium_priority:
            skill, count = medium_priority[0]
            skill_name = skill.strip()

            plan[f'Week {week}-{week+1}'] = {
                'skill': skill_name,
                'frequency': count,
                'goal': f'Learn {skill_name} basics',
            }

            print(f"\n💡 Week {week}-{week+1}: {skill_name.upper()}")
            print(f"   Requested by: {count} jobs")
            print(f"   Goal: Get familiar, add to resume")
        else:
            print(f"\n✨ Week {week}-{week+1}: DEEPEN EXISTING SKILLS")
            print(f"   Advanced PyTorch techniques")
            print(f"   Computer Vision papers implementation")
            print(f"   Blog post: Technical deep dive")

        week += 2

    # Week 7-8: Portfolio polish
    if week <= 8:
        print(f"\n🎨 Week {week}-{week+1}: PORTFOLIO POLISH")
        print(f"   - Add new skills to resume")
        print(f"   - Update LinkedIn with projects")
        print(f"   - Write blog posts")
        print(f"   - GitHub README updates")
        print(f"   - Deploy live demos")

    print()
    print("=" * 70)
    print()

    return plan


def save_analysis(sorted_skills, requirements):
    """Analizi dosyaya kaydet"""

    OUTPUT_DIR.mkdir(exist_ok=True)

    # JSON format
    analysis = {
        'generated_at': datetime.now().isoformat(),
        'missing_skills': [
            {'skill': skill, 'frequency': count, 'percentage': count / 30 * 100}
            for skill, count in sorted_skills
        ],
        'recommendations': []
    }

    # Add recommendations
    for skill, count in sorted_skills[:5]:
        if skill.strip() in LEARNING_RESOURCES:
            analysis['recommendations'].append({
                'skill': skill.strip(),
                'priority': LEARNING_RESOURCES[skill.strip()].get('priority'),
                'resources': LEARNING_RESOURCES[skill.strip()].get('free_resources'),
                'quick_win': LEARNING_RESOURCES[skill.strip()].get('quick_win'),
            })

    json_file = OUTPUT_DIR / f"skills_gap_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # Human-readable format
    txt_file = OUTPUT_DIR / f"learning_plan_{datetime.now().strftime('%Y%m%d')}.txt"

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  SKILLS GAP ANALYSIS & LEARNING PLAN\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("MISSING SKILLS (by frequency):\n")
        f.write("-" * 70 + "\n")

        for i, (skill, count) in enumerate(sorted_skills[:15], 1):
            pct = count / 30 * 100
            f.write(f"{i:2}. {skill:30} | {count:2} jobs ({pct:4.1f}%)\n")

        f.write("\n\n")
        f.write("TOP 5 TO LEARN:\n")
        f.write("-" * 70 + "\n\n")

        for skill, count in sorted_skills[:5]:
            skill_name = skill.strip()

            if skill_name in LEARNING_RESOURCES:
                res = LEARNING_RESOURCES[skill_name]

                f.write(f"📚 {skill_name.upper()}\n")
                f.write(f"   Priority: {res.get('priority')}\n")
                f.write(f"   Time: {res.get('time_to_learn')}\n")
                f.write(f"   Requested by: {count} jobs\n")
                f.write(f"   Quick Win: {res.get('quick_win')}\n\n")

                f.write("   Resources:\n")
                for resource in res.get('free_resources', []):
                    f.write(f"   • {resource}\n")

                f.write(f"\n   Portfolio Project: {res.get('portfolio_project')}\n")
                f.write("\n" + "-" * 70 + "\n\n")

    print(f"💾 Analysis saved:")
    print(f"   {json_file}")
    print(f"   {txt_file}")
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    analyze_skills_gap()

    print("🎯 ACTION ITEMS:")
    print("-" * 70)
    print("1. Review learning_plan/ folder")
    print("2. Pick Week 1-2 skill (highest priority)")
    print("3. Block 5-10 hours this week for learning")
    print("4. Build portfolio project")
    print("5. Update resume + LinkedIn")
    print("6. Apply to MORE jobs with new skill!")
    print()
    print("💡 Remember: Employers value PROJECT > certificate")
    print("   Build something real, deploy it, share the link!")
    print("=" * 70)
