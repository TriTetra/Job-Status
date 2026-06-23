# 2-Month Action Plan: Land a Job Offer

A multi-channel, quality-focused strategy for a visa-needing ML engineer.

**Start:** 2026-06-22
**Goal:** 1+ job offer by 2026-08-22
**Method:** applications + cold email + networking, not applications alone

## Week-by-week breakdown

### Week 1 (June 23-29): Foundation + first wave

#### Monday (Day 1) - Portfolio boost

**Morning (2-3 hours):**
```
1. Add README.md to YOLOv8 project
   - Architecture diagram
   - Results: 92% mAP, 40ms latency
   - Live demo link (Hugging Face Spaces is free)
2. Sentropy Engine repo
   - Performance benchmarks
   - Architecture documentation
   - Rust + PyTorch integration details
3. Pin top 3 projects showcasing ML/CV skills
```

**Afternoon (2 hours):**
```
1. LinkedIn headline: "ML Engineer | Computer Vision | 92% mAP YOLOv8 in Production"
2. About section: STAR-format achievements
3. Featured section: add GitHub projects
4. Ask 3 connections for skill endorsements
```

**Evening (1 hour):**
```
python scripts/strategy/cold_email_generator.py
# Choose template: value_first
# Generate 10 emails
```

#### Tuesday (Day 2) - Research & target

**Morning (3 hours):**
```
Select top 10 jobs from the Excel export. Criteria:
- Score 8+
- Remote
- Startup (more flexible on visa)
- Posted within 7 days

For each job:
1. Research the company (blog, tech stack, recent news)
2. Find the hiring manager on LinkedIn
3. Tailor a cold email template
4. Log it in the tracker
```

**Afternoon (2 hours):**
```
Target: 10 new LinkedIn connections
1. Hiring managers at top 10 target companies
2. ML engineers at target companies
3. Turkish tech community members

Message template:
"Hi [Name], fellow ML engineer here - impressed by [Company]'s work
on [specific tech]. Would love to connect."
```

#### Wednesday (Day 3) - Apply + email

**Morning (2 hours):**
```
1. Apply to top 5 jobs (LinkedIn/Indeed)
2. Customize CV per job (highlight matching skills)
3. Use the cover letter template
4. Log in docs/tracking/APPLICATION_TRACKER.md
```

**Afternoon (2 hours):**
```
Send 5 cold emails. Timing: 9-11 AM in the recipient's timezone
(US West Coast: send 4-6 PM your time).
```

#### Thursday (Day 4) - More applications + skills

**Morning (2 hours):** Apply to 5 more jobs (10 total).

**Afternoon (3 hours):**
```
python scripts/strategy/skills_gap_analyzer.py

# Start Week 1 learning, e.g. AWS basics:
- Sign up for AWS Free Tier
- Complete the first tutorial
- Deploy a simple model to Lambda
```

#### Friday (Day 5) - LinkedIn follow-up + learning

**Morning (2 hours):**
```
1. Comment on 5 posts from target companies
2. Share your YOLOv8 project
3. Write a short post about something you learned this week
```

**Afternoon (3 hours):** Continue the AWS deployment; document the process
for a future blog post.

#### Saturday (Day 6) - Portfolio project

**All day (6-8 hours):**
```
Example: AWS deployment
1. Deploy YOLOv8 to AWS Lambda
2. Create an API Gateway in front of it
3. Test with live images
4. Document and write a README
5. Push to GitHub
6. Deploy a demo to Hugging Face Spaces
```

#### Sunday (Day 7) - Review & plan

**Morning (2 hours):**
```
1. Update docs/tracking/APPLICATION_TRACKER.md
2. Check cold email responses
3. Check LinkedIn connection acceptance rate
4. Plan Week 2 targets
```

**Afternoon (2 hours):**
```
1. Generate the next 10 cold emails
2. Select the next 10 jobs
3. Update the resume if a new skill was completed
```

### Week 2 (June 30 - July 6): Follow-up + second wave

**Daily tasks:**

Monday-Wednesday: follow-up emails (day 7 after the first send), apply to 10
more jobs, send 10 new cold emails, 15 LinkedIn connections.

Thursday-Friday: continue learning (week 2 of AWS), engage on LinkedIn,
research the next skill.

Weekend: polish the portfolio project, write a blog post about the AWS
deployment, share it on LinkedIn.

### Week 3-4: Network + interview prep

**Goals:** first phone screens (target: 1-2), 30 total applications, 50+
LinkedIn connections, AWS completed, start Kubernetes/Docker.

**Daily routine:**
```
Morning: check responses, send follow-ups, 2-3 new applications
Afternoon: LinkedIn networking (1h), learning (2h), interview prep (1h)
Evening: update tracker, respond to emails
```

### Week 5-6: Interview focus

**Goals:** 2-3 technical interviews, second skill completed (Kubernetes),
blog posts published, referrals activated.

**Interview prep (weekly):** 3 LeetCode-medium problems, 2 ML system design
practice sessions, 1 mock behavioral interview, review STAR stories.

**Topics:** computer vision architecture, ML model deployment, performance
optimization, real-time inference, PyTorch internals.

### Week 7-8: Final push

**Goals:** 3-4 final interviews, 1-2 offers, negotiation prep.

**Focus:** interview follow-ups, negotiation research, minimal new
applications, maximum LinkedIn engagement.

## Success metrics (realistic for a visa-needing candidate)

These are planning targets, not measured outcomes — there is no track record
yet to calibrate them against.

**Conservative:**
```
Week 2: 20 apps -> 1-2 email responses
Week 3: 30 apps -> 1 phone screen
Week 4: 40 apps -> 1-2 phone screens
Week 5: 50 apps -> 2 technical interviews
Week 6: 60 apps -> 2-3 technical interviews
Week 7: 70 apps -> 1 final interview
Week 8: 80 apps -> 1 offer
```

**Optimistic:**
```
Week 3: 1-2 phone screens
Week 4: 2-3 technical interviews
Week 5: 1 final interview
Week 6: 2 final interviews
Week 7: 1 offer
Week 8: 2 offers
```

## Daily routine (weeks 1-4)

**Morning (2 hours):** check messages (15m), respond (15m), research + apply
to 2 jobs (60m), send 2 cold emails (30m).

**Afternoon (3 hours):** LinkedIn networking - 5 connections, 3 meaningful
comments, 1 post/week (1h); learning - new skill practice, portfolio project,
blog writing (2h).

**Evening (1 hour):** interview prep - LeetCode or system design (30m);
tracking - update docs/tracking/APPLICATION_TRACKER.md, plan tomorrow, weekly git commit (30m).

## Critical success factors

**Quality over quantity.** 30 highly targeted applications plus cold email and
networking outperforms 100 generic applications.

**Multi-channel.** Don't rely on the Apply button alone — combine cold email,
LinkedIn connections, referrals, and a follow-up sequence.

**Visa strategy.** Mention sponsorship need in the second email, not the
first, or use the `sponsorship_upfront` template. Focus on remote roles and
startups, which tend to be more flexible. Lead with "available immediately,
remote experience."

**Portfolio over resume.** Live demos beat screenshots, GitHub code beats a
PDF, blog posts beat certificates, metrics beat buzzwords.

**Consistency over intensity.** 2-3 hours a day for 8 weeks beats 10 hours a
day for 2 weeks followed by burnout.

## Week 1 immediate actions

**Today:**
```
1. Generate cold emails (30 min): python scripts/strategy/cold_email_generator.py
2. Analyze skill gaps (15 min): python scripts/strategy/skills_gap_analyzer.py
3. Set up tracking (15 min): open docs/tracking/APPLICATION_TRACKER.md, create the Week 1 section
```

**Tomorrow:**
```
Morning: GitHub README for YOLOv8 (1h), LinkedIn headline update (30m),
research top 5 companies (1h)
Afternoon: find 5 hiring managers (1h), customize 5 cold emails (1h),
apply to 3 jobs (1h)
```

## Patterns to avoid

- Spray and pray: 100 generic applications
- No follow-up: send and forget
- Obviously templated, unpersonalized emails
- Skipping LinkedIn networking entirely
- Applying without addressing skill gaps
- Resume only, no portfolio proof
- Burning out: 80 hours in week 1, quitting by week 3

## Patterns to pursue

- Research before applying
- Multi-touch: apply + email + LinkedIn
- A 3-email follow-up sequence
- 100+ connections by week 8
- Learning in public: blog posts, GitHub updates
- Live, deployed demos
- 2-3 consistent hours daily

## Resources

**Job search:** LinkedIn, Indeed, the Excel report from `scripts/scan/run_full_scan.py`,
Hacker News "Who's Hiring," remote ML job boards.

**Cold email:** LinkedIn Sales Navigator (free trial), Apollo.io, Hunter.io.

**Learning:** AWS Free Tier, Kubernetes.io tutorials, Hugging Face Spaces,
Dev.to.

**Interview prep:** LeetCode (ML focus), Educative.io system design, Pramp,
Glassdoor interview questions.

## Success definition

Minimum: 1 job offer by week 8. Target: 2 offers. Stretch: 3+ offers with
negotiation leverage.

Even without an offer by week 8, the goal is to leave with: 100+ LinkedIn
connections, 2 new skills learned, an upgraded portfolio with live demos,
published blog posts, and a repeatable process for weeks 9-12.
