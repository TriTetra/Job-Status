#!/usr/bin/env python3
"""
Cold Email Generator
--------------------
Excel'den işleri okur ve her biri için kişiselleştirilmiş cold email oluşturur.

HR-tested templates!

Kullanım:
    python scripts/cold_email_generator.py
"""

import openpyxl
from pathlib import Path
from datetime import datetime
import json
import re


# ============================================================================
# CONFIG
# ============================================================================

REPORTS_DIR = Path(__file__).parent.parent / "reports"
OUTPUT_DIR = Path(__file__).parent.parent / "cold_emails"

YOUR_INFO = {
    'name': 'Abdullokh Abdukodirov',
    'email': 'abdullahabdulkadir0@gmail.com',
    'phone': '+905510581613',
    'linkedin': 'linkedin.com/in/abdullokhabdukodirov',
    'github': 'github.com/TriTetra',
    'location': 'Remote (UTC+5)',
}

# Key achievements (STAR format)
ACHIEVEMENTS = {
    'cv_yolo': {
        'situation': 'needed real-time object detection for autonomous aerial systems',
        'task': 'deploy ML model on resource-constrained hardware',
        'action': 'fine-tuned YOLOv8n on 30k+ images and optimized inference pipeline',
        'result': '92% mAP accuracy, 40ms latency, 20+ FPS on Raspberry Pi 5',
        'tech': ['YOLOv8', 'OpenCV', 'Python', 'Embedded ML']
    },
    'sentropy': {
        'situation': 'existing ML inference frameworks too slow for production',
        'task': 'build high-performance inference runtime',
        'action': 'architected Rust-based engine with async pipeline',
        'result': '40ms inference latency, 5x faster than baseline',
        'tech': ['Rust', 'PyTorch', 'Performance Optimization']
    },
    'boen_cv': {
        'situation': 'users needed seamless CV editing experience',
        'task': 'build real-time WYSIWYG editor with instant preview',
        'action': 'engineered React Context-based editor with custom hooks',
        'result': '30% FCP reduction, millisecond-level synchronization',
        'tech': ['Next.js 15', 'React 19', 'TypeScript']
    }
}


# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

def generate_subject_line(job_title, company, hook_type='achievement'):
    """Konu satırı oluştur"""

    hooks = {
        'achievement': f"ML Engineer with 92% mAP Computer Vision Experience",
        'specific': f"Re: {job_title} - Computer Vision Expertise",
        'question': f"Question about {company}'s ML Infrastructure",
        'value': f"Optimizing ML Inference for {company}",
        'mutual': f"Fellow ML Engineer interested in {company}",
    }

    return hooks.get(hook_type, hooks['achievement'])


def generate_email_body(job, template_type='value_first'):
    """Email body oluştur"""

    title = job.get('title', 'ML Engineer')
    company = job.get('company', 'your company')
    requirements = job.get('requirements', '')
    your_skills = job.get('your_skills', '')

    # Extract a specific requirement to reference
    specific_req = "real-time ML systems"
    if requirements:
        lines = requirements.split('\n')
        if len(lines) > 0:
            specific_req = lines[0].replace('•', '').strip()[:60]

    # Company-specific research prompt
    company_research = f"[Research {company}'s recent blog posts, tech stack, or challenges]"

    templates = {
        'value_first': f"""Hi [Hiring Manager Name],

I noticed {company}'s opening for {title} and was particularly excited by your focus on {specific_req}.

Quick context: I recently built a YOLOv8 object detection system achieving 92% mAP on edge devices—deployed in production on autonomous drones. When I saw your team's work on [specific company project/tech], it reminded me of the optimization challenges we solved reducing inference latency from 200ms to 40ms.

I'd love to learn more about how your team is approaching [specific technical challenge from job description]. Would you have 15 minutes for a quick call?

Best,
Abdullokh
{YOUR_INFO['github']} | {YOUR_INFO['linkedin']}""",

        'problem_solution': f"""Hi [Hiring Manager Name],

I came across your {title} opening while researching companies tackling [specific problem domain].

Your mention of {specific_req} caught my attention—at KOU STORM UAV, we faced a similar challenge: deploying ML models on resource-constrained hardware. We solved it by fine-tuning YOLOv8 and building a custom inference pipeline, achieving 92% mAP while maintaining 20+ FPS on edge devices.

I'm curious about {company}'s approach to [specific technical challenge]. Would you be open to a brief conversation?

Looking forward to connecting,
Abdullokh
{YOUR_INFO['email']} | {YOUR_INFO['github']}""",

        'mutual_interest': f"""Hi [Hiring Manager Name],

Fellow ML engineer here—I've been following {company}'s work on [specific technology/product] and was excited to see you're hiring for {title}.

I'm working on similar challenges in computer vision and real-time inference. Recently shipped a production system with:
• 92% mAP object detection on embedded devices
• 40ms inference latency (5x improvement)
• 30k+ image training pipeline

I'd love to learn more about your team's approach to {specific_req}. Open to a quick chat?

Best,
Abdullokh
{YOUR_INFO['linkedin']} | {YOUR_INFO['github']}""",

        'direct_value': f"""Hi [Hiring Manager Name],

I'm reaching out about the {title} role. I have direct experience with several items from your requirements:

{your_skills[:200]}

Most recently: Built production YOLOv8 system (92% mAP, 40ms latency) for autonomous aerial detection.

I'm interested in how {company} is approaching [specific technical challenge]. Would 15 minutes work for a quick call this week?

Best,
Abdullokh
{YOUR_INFO['email']} | Portfolio: {YOUR_INFO['github']}""",

        'sponsorship_upfront': f"""Hi [Hiring Manager Name],

I'm reaching out about the {title} position. Upfront: I'd need visa sponsorship, so wanted to check if {company} sponsors before diving into details.

If you do: I've built production ML systems with measurable impact:
• 92% mAP computer vision on edge devices
• 40ms real-time inference (5x speedup)
• Deployed on autonomous systems

Happy to share details on a quick call if there's a fit. Thanks for your time either way!

Best,
Abdullokh
{YOUR_INFO['github']} | {YOUR_INFO['linkedin']}"""
    }

    return templates.get(template_type, templates['value_first'])


def generate_follow_up_emails(job, sequence_number=1):
    """Follow-up email serisi"""

    title = job.get('title', 'ML Engineer')
    company = job.get('company', 'your company')

    follow_ups = {
        1: f"""Hi [Name],

Following up on my email from last week about the {title} role.

I wanted to add: I recently came across {company}'s work on [specific recent project/blog post] and it aligns well with my experience in [relevant area].

Still interested in a quick 15-minute chat if you have time this week.

Best,
Abdullokh""",

        2: f"""Hi [Name],

Last follow-up on the {title} position—I know you're busy!

Quick question: Is {company} currently sponsoring visas for strong ML engineering candidates? That would help me understand if it's worth both our time to continue the conversation.

Either way, appreciate your time.

Best,
Abdullokh""",

        'final': f"""Hi [Name],

I'll stop following up after this :)

Just wanted to say—if the {title} role doesn't work out, I'd still love to connect and learn about {company}'s ML infrastructure. Always interested in how teams are solving [specific technical challenge].

Best of luck with the search!

Abdullokh
{YOUR_INFO['linkedin']}"""
    }

    return follow_ups.get(sequence_number, follow_ups[1])


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def find_latest_excel():
    """En son Excel'i bul"""
    excel_files = list(REPORTS_DIR.rglob("applypilot_advanced_*.xlsx"))
    if not excel_files:
        return None
    return max(excel_files, key=lambda p: p.stat().st_mtime)


def extract_company_from_site(site):
    """Site adından şirket ismini çıkar"""
    # LinkedIn, Indeed gibi site adları değil, gerçek şirket adını bulmak için
    # Bu basit bir heuristic, gerçekte LinkedIn'den şirket adını çekmek lazım
    if site and site not in ['linkedin', 'indeed', 'glassdoor']:
        return site
    return "the company"


def generate_emails_from_excel(template_type='value_first', max_jobs=10):
    """Excel'den email'ler oluştur"""

    excel_path = find_latest_excel()
    if not excel_path:
        print("❌ Excel bulunamadı!")
        return

    print(f"📊 Reading: {excel_path.name}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Read Excel
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb["🎯 Perfect Match (8+)"]

    emails_generated = []

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
        if not row[1]:  # No title
            continue

        if idx > max_jobs:
            break

        job = {
            'title': row[1],
            'company': extract_company_from_site(row[3]),
            'location': row[4],
            'remote': row[5],
            'salary': row[6],
            'score': row[7],
            'requirements': row[9],
            'your_skills': row[10],
            'missing_skills': row[11],
            'match_pct': row[12],
            'apply_link': row[16],
        }

        # Generate email
        subject = generate_subject_line(job['title'], job['company'])
        body = generate_email_body(job, template_type)

        # Follow-ups
        follow_up_1 = generate_follow_up_emails(job, 1)
        follow_up_2 = generate_follow_up_emails(job, 2)
        follow_up_final = generate_follow_up_emails(job, 'final')

        email_data = {
            'job': job,
            'subject': subject,
            'body': body,
            'follow_ups': {
                'day_7': follow_up_1,
                'day_14': follow_up_2,
                'final': follow_up_final
            },
            'hiring_manager_research': {
                'linkedin_search': f'{job["company"]} {job["title"]} hiring manager',
                'apollo_io': f'https://app.apollo.io/#/people?titles={job["title"]}&organizationNames={job["company"]}',
                'tips': [
                    'LinkedIn: Search "[Company Name] hiring manager ML"',
                    'Check job posting for recruiter name',
                    'Look for Engineering Manager or VP Engineering',
                    'Fallback: jobs@company.com or careers@company.com'
                ]
            }
        }

        emails_generated.append(email_data)

        # Save individual email
        filename = OUTPUT_DIR / f"email_{idx:03d}_{job['title'][:30].replace('/', '_')}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"JOB: {job['title']} at {job['company']}\n")
            f.write(f"LINK: {job['apply_link']}\n")
            f.write(f"SCORE: {job['score']}/10\n")
            f.write("=" * 70 + "\n\n")

            f.write("TO: [Hiring Manager Name - RESEARCH ON LINKEDIN]\n")
            f.write(f"SUBJECT: {subject}\n\n")

            f.write("INITIAL EMAIL:\n")
            f.write("-" * 70 + "\n")
            f.write(body)
            f.write("\n\n")

            f.write("FOLLOW-UP #1 (Day 7):\n")
            f.write("-" * 70 + "\n")
            f.write(follow_up_1)
            f.write("\n\n")

            f.write("FOLLOW-UP #2 (Day 14):\n")
            f.write("-" * 70 + "\n")
            f.write(follow_up_2)
            f.write("\n\n")

            f.write("FINAL FOLLOW-UP (Day 21):\n")
            f.write("-" * 70 + "\n")
            f.write(follow_up_final)
            f.write("\n\n")

            f.write("=" * 70 + "\n")
            f.write("HIRING MANAGER RESEARCH:\n")
            f.write("-" * 70 + "\n")
            for tip in email_data['hiring_manager_research']['tips']:
                f.write(f"• {tip}\n")
            f.write("\n")
            f.write(f"LinkedIn Search: {email_data['hiring_manager_research']['linkedin_search']}\n")

        print(f"✅ {idx}. {job['title'][:50]}")

    wb.close()

    # Save master list
    master_file = OUTPUT_DIR / f"_MASTER_LIST_{datetime.now().strftime('%Y%m%d')}.json"
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(emails_generated, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print(f"✅ {len(emails_generated)} cold emails generated!")
    print(f"📁 Location: {OUTPUT_DIR}")
    print()
    print("📋 NEXT STEPS:")
    print("-" * 70)
    print("1. Open each email file in cold_emails/")
    print("2. Research hiring manager on LinkedIn")
    print("3. Customize [bracketed sections] with specific details")
    print("4. Copy-paste to Gmail/email client")
    print("5. Track responses in JOB_APPLICATIONS.md")
    print()
    print("💡 PRO TIPS:")
    print("-" * 70)
    print("• Send 5-10 emails per day (not all at once!)")
    print("• Best time: Tuesday-Thursday, 9-11 AM recipient timezone")
    print("• Personalize at least one sentence per email")
    print("• Follow up EXACTLY on day 7, 14, 21")
    print("• Track in spreadsheet: sent date, response, next action")
    print("=" * 70)


def show_template_comparison():
    """Template örneklerini göster"""

    sample_job = {
        'title': 'ML Engineer',
        'company': 'Acme AI',
        'requirements': '• Real-time ML systems\n• Computer vision\n• Production deployment',
        'your_skills': 'PyTorch, Computer Vision, YOLOv8, Production ML',
    }

    print("\n" + "=" * 70)
    print("  EMAIL TEMPLATE COMPARISON")
    print("=" * 70 + "\n")

    templates = ['value_first', 'problem_solution', 'mutual_interest', 'direct_value', 'sponsorship_upfront']

    for i, template in enumerate(templates, 1):
        print(f"\n{'='*70}")
        print(f"TEMPLATE #{i}: {template.upper().replace('_', ' ')}")
        print('='*70)

        subject = generate_subject_line(sample_job['title'], sample_job['company'])
        body = generate_email_body(sample_job, template)

        print(f"\nSUBJECT: {subject}\n")
        print(body)
        print()

    print("=" * 70)
    print("\n💡 Which template to use when:")
    print("-" * 70)
    print("• value_first: Default, best for most jobs")
    print("• problem_solution: When job mentions specific technical problem")
    print("• mutual_interest: For companies you genuinely follow")
    print("• direct_value: When you match requirements closely")
    print("• sponsorship_upfront: Saves time, filters early")
    print("=" * 70)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    print("\n" + "=" * 70)
    print("  🎯 COLD EMAIL GENERATOR")
    print("=" * 70 + "\n")

    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        show_template_comparison()
    else:
        print("Choose template style:")
        print("1. value_first (RECOMMENDED - shows achievements)")
        print("2. problem_solution (technical, problem-focused)")
        print("3. mutual_interest (for companies you follow)")
        print("4. direct_value (direct, brief)")
        print("5. sponsorship_upfront (honest, saves time)")
        print()

        choice = input("Enter number (1-5) [default: 1]: ").strip() or "1"

        templates = {
            '1': 'value_first',
            '2': 'problem_solution',
            '3': 'mutual_interest',
            '4': 'direct_value',
            '5': 'sponsorship_upfront'
        }

        template = templates.get(choice, 'value_first')

        max_jobs = input("\nHow many jobs? [default: 10]: ").strip() or "10"
        max_jobs = int(max_jobs)

        print(f"\n✅ Generating emails with '{template}' template...\n")

        generate_emails_from_excel(template, max_jobs)
