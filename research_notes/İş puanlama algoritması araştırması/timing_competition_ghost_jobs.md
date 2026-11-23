# Application Timing, Applicant Competition and Stale/Ghost Postings — Fact Base for a Candidate-Side Job Scoring Algorithm

Research date: 2026-11-23. Numbers come from web searches and fetched pages. Provenance flags:
- **[PRIMARY]**: platform or vendor's own published data page
- **[SECONDARY]**: press or aggregator summary of someone else's data
- **[WEAK]**: vendor marketing, small or undisclosed sample, old, or unverifiable

---

## Q1. Application timing: does applying early raise interview odds, how fast do chances decay, and what is the typical time-to-fill?

### Takeaway
Applications cluster heavily in a posting's first week; Ashby measures week-one volume at about 2 to 3 times later weeks. The only quantified "decay curve" for interview odds is TalentWorks' old and weakly sourced finding: about 8x better odds inside the first 96 hours and about −28% per day after that. Median time from job opening to first hire is roughly 2 to 2.5 months (Ashby: 56 days for business roles, 76 for technical), so a posting stays "live" well beyond the period when early applicants hold the advantage.

### Cited Findings
**Posting-age effect on interview odds**
- TalentWorks (US, about 2017–2018): applying in the first 96 hours ("Golden Hours") gave up to 8x higher interview-invite chances than applying later. Chances fell about 28% for each day after that. Sample was roughly 4,000 to 6,000 applications. **[WEAK]**: vendor analysis, small sample, old; no primary report was found, only secondary write-ups. — [paulvanderlaken.com summary of TalentWorks](https://paulvanderlaken.com/2017/10/24/talent-works-data-science-to-improve-job-application-chances/); [CSUN career center blog (Dec 2024) repeating the "8x" claim](https://nazariancareers.csun.edu/blog/2024/12/24/when-should-you-apply-for-a-job-heres-how-to-8x-your-odds/)
- Popular claims such as "90% of interviews go to people who apply in the first 24 hours" or "applications after 4 PM have a 5% chance of being read" have no traceable dataset. **[WEAK]**, do not use. — [mypivot Substack](https://mypivot.substack.com/p/90-of-interviews-go-to-people-who); [Fairygodboss](https://fairygodboss.com/career-topics/best-time-to-send-a-job-application)

**When applications arrive (volume curve; competitive-pressure proxy)**
- Ashby (about 13M applications, Jan 2021 to Apr 2023, mostly US tech and startup customers): the first week after posting draws the most applications, about 2x the following weeks (another Ashby PDF says 2.5–3x). Volume then settles into a steady state. Ashby attributes the spike to visibility at the top of job boards and search results, plus novelty and deadline urgency. Ashby suggests using the first-4-week average as a planning proxy. **[PRIMARY, vendor]** — [Ashby 2023 Applications per Job report (blog)](https://www.ashbyhq.com/blog/recruiting/2023-trends-report-applications-per-job); [Ashby PDF "Trends in Application per Job"](https://sales.ashbyhq.com/hubfs/Ashby%20-%20Trends%20in%20Application%20per%20Job.pdf); [Ashby "Operationalizing the 2023 Application Per Job Report"](https://ashbyhq.com/blog/recruiting/operationalizing-2023-application-per-job-report)
- Ashby does **not** publish conversion (application to interview) by days since posting. Its inbound report has no posting-age breakdown. — [Ashby Inbound report (Oct 2025)](https://www.ashbyhq.com/talent-trends-report/reports/inbound)

**Time-to-hire and time-to-fill**
- Ashby "time to first fill" (job opened to first hire), Q1 2026: median **56 days for business roles** and **76 days for technical roles**. **[SECONDARY]**: from compilations citing Ashby's Recruiting Operations Benchmarks; the Ashby page was not fetched directly. — [Ashby Recruiting Operations Benchmarks 2026](https://www.ashbyhq.com/talent-trends-report/reports/recruiting-operations-benchmarks-talent-trends?view=full); [herohunt.ai summary](https://www.herohunt.ai/blog/average-time-to-hire-2026-benchmarks-by-role-and-fixes/)
- Ashby "time to hire" (application to accepted offer): median about **30 days for business and 40 days for technical** roles (Q2–Q3 2025). A separate Ashby figure gives about **34 days in AMER and 35 days in EMEA** (year to June 2026). Startups (1,200+ VC-backed companies): global median about 38 days. **[SECONDARY]** — [herohunt.ai](https://www.herohunt.ai/blog/average-time-to-hire-2026-benchmarks-by-role-and-fixes/); [Ashby State of Startup Hiring 2026](https://www.ashbyhq.com/talent-trends-report/reports/startup-hiring); [Ashby One London 2026 Talent Trends](https://www.ashbyhq.com/ashby-one/2026/london/talent-trends)
- Indeed Hiring Lab: employers took **longer to fill postings in 2025 than in 2022**. No day figure was available in the snippet. **[SECONDARY]** — [Indeed Hiring Lab](https://hiringlab.indeed.com/?p=19776)
- Ashby: in 2024, teams interviewed **about 40% more candidates per hire** than in 2021, for both business and technical roles. Data: 31M applications and 95K jobs, Jan 2021 to Sep 2024. **[PRIMARY, vendor]** — [Ashby Recruiter Productivity report](https://www.ashbyhq.com/talent-trends-report/reports/2023-recruiter-productivity-trends-report?)

### Inferences
- A defensible model treats posting age as a **two-phase decay**: high value in days 0–4 (about 96 h), a steep decline through days 5–14 as the week-one application pile is screened, then a low plateau. TalentWorks' −28%/day compounds to about 0.72^7 ≈ 0.10 of baseline after one extra week. That is probably too aggressive to apply all the way out; cap it at a floor (for example 0.2–0.3x) because many roles take 56–76 days to fill and recruiters keep screening.
- Because time to first fill is about 2–2.5 months, a posting under about 30 days old is plausibly still active. Past about 60–76 days (technical) it exceeds the median fill time. That is a staleness signal, not proof that hiring has ended.
- Technical roles fill more slowly (76 vs 56 days), so the decay for technical roles should be somewhat slower than for business roles.

### Gaps
- No rigorous, recent (2022–2026) public dataset links applicant interview rate to posting age. TalentWorks is the only quantified curve, and it is weak.
- I found no LinkedIn Economic Graph publication on "first 96 hours" or "first 10 days" applicant advantage, despite common claims.
- Greenhouse and Lever time-to-fill figures were not located in primary form.
- No Europe-specific time-to-fill figures beyond Ashby's AMER-vs-EMEA time to hire (34 vs 35 days).

---

## Q2. Applicant volume: averages, remote vs on-site, big tech vs startups, and Easy Apply

### Takeaway
Applications per role roughly **tripled from 2021 to 2024**, to about 250–300+ per hire or role on modern ATSs. US **remote roles were about 8–10% of postings but drew about 46% of applications** (LinkedIn, Dec 2023), about 5x the competition of non-remote roles. Famous big-tech employers run acceptance rates around 0.2–0.5%, but that figure comes from 2014 and is weak.

### Cited Findings
**Average applicants per posting or hire**
- Ashby: applications per job roughly **tripled** from Jan 2021 to Jan 2024: about 3x for business roles and 2.6x for technical roles. **[PRIMARY, vendor]** — [Ashby 2023 Applications per Job report](https://www.ashbyhq.com/talent-trends-report/reports/2023-trends-report-applications-per-job)
- HR Dive (reporting Ashby): open roles now receive an average of **more than 300 applications**, and applications per hire have tripled since 2021. **[SECONDARY]** — [HR Dive](https://www.hrdive.com/news/recruiters-see-job-applications-triple-to-more-than-300-per-role/820096/)
- Aggregator citing Ashby: quarterly applications per hire stayed **above 300 throughout 2025**, then fell to **291 in Q1 2026**. Its annual table (2024: 223; 2025: 244) mixes Ashby and Greenhouse series. **[WEAK/SECONDARY]**: mixed sources — [FMC Group](https://fmcgroup.com/average-applications-per-hire-statistics/)
- Greenhouse: recruiter workload reached **588 applications per recruiter in Q3 2024**, up 26% from Q3 2023. **[SECONDARY]**: Fortune citing Greenhouse — [Fortune, Jan 2025](https://fortune.com/2025/01/16/job-market-rife-fake-listing-ghosting-hiring-managers/); [Greenhouse 2024 State of Job Hunting](https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report)
- Greenhouse 2024 survey (2,500 workers in the US, UK and Germany): **38% of job seekers mass-apply**; 57% attribute rising competition to AI. **[PRIMARY, survey]** — [Greenhouse 2024 State of Job Hunting report](https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report)
- JobScore (2025, employer benchmark): **32% of employers averaged more than 100 applications per job**, up 28% from 2024; **20% averaged more than 200**. **[WEAK]**: vendor, small-business ATS — [JobScore](https://www.jobscore.com/?p=18109)
- Korn Ferry cites a study putting a typical online corporate posting at about **250 applications**. **[WEAK]**: the underlying study is not identified — [Korn Ferry](https://www.kornferry.com/insights/this-week-in-leadership/the-application-avalanche)
- LinkedIn: about **11,000 applications submitted per minute**, up 45% in a year (NYT via eWeek, 2025). **[SECONDARY]** — [eWeek](https://www.eweek.com/de/news/ai-job-applications-linkedin/)
- LinkedIn/Censuswide survey (fieldwork Nov–Dec 2024, 17 markets, 22,010 workers and 8,035 HR professionals): **73% of HR pros say less than half of applications meet all listed criteria**; 37% of job seekers apply to more jobs but hear back less; 22% of recruiters spend 3–5 h/day screening applications. **[PRIMARY, survey]** — [LinkedIn press release, 15 Jan 2025](https://news.linkedin.com/2025/talent-campaign-b2b-press-release)
- Lever (older study; date not visible in the snippet): about **1 in 100 candidates is hired** overall. **[SECONDARY/older]** — [SHRM on Lever study](https://shrm.org/topics-tools/news/talent-acquisition/lever-study-shows-1-100-candidates-hired)

**Remote vs on-site**
- LinkedIn US, Dec 2023: remote jobs were **10% of postings but received 46% of applications**, making remote roles **about 5x as competitive** as non-remote roles. US remote postings fell 9% from Jan 2022 to Dec 2023. **[SECONDARY]**: Fortune reporting LinkedIn data — [Fortune, 29 Jan 2024](https://fortune.com/2024/01/29/remote-jobs-scarce-many-applications-labor-market-linkedin-report/)
- LinkedIn Global State of Remote and Hybrid Work (Sept 2024, July 2024 data): remote share of postings was **8.5% in the US** (hybrid 13.4%), **10.3% in the UK**, 5.9% in Germany, 2.7% in France and 10.0% in India. **[PRIMARY]** — [LinkedIn Economic Graph PDF, Sept 2024](https://economicgraph.linkedin.com/content/dam/me/economicgraph/en-us/PDF/global-state-of-remote-and-hybrid-work-sept-2024.pdf)
- Ireland, March 2024: remote was 8.3% of postings and drew **2.4x** its posting share in applications. **[SECONDARY]** — [RTÉ](https://www.rte.ie/news/business/2024/0425/1445704-ireland-ranks-second-for-remote-work-opportunities); [Fortune Europe, Mar 2024](https://fortune.com/europe/2024/03/21/remote-work-jobs-disappearing-gold-mine-talent-employers-return-to-office/)

**Big tech vs startups / company size**
- Google: about **3M applications a year and about 7,000 hires, or about 0.2%** (Laszlo Bock, 2014). Google does not publish this. Later estimates range from 0.2% to 0.5%, and some use 2M applicants (about 0.35%). **[WEAK]**: 2014 remark, unverified — [Quartz, 2014](https://qz.com/285001/heres-why-you-only-have-a-0-2-chance-of-getting-hired-at-google); [Educative](https://www.educative.io/blog/google-acceptance-rate)
- Ashby 2025 hiring (fixed cohort, 2024–2025): companies with **>1,000 employees grew hiring steadily**, reaching more than 100% above the Q1 2024 baseline. Companies with **<100 employees hired less** in every 2025 quarter, down as much as 25–35% versus baseline. AMER hiring was about 50% above baseline by Q4 2025, while EMEA was up only 2% year over year. **[PRIMARY, vendor]** — [Ashby 2025 Hiring report (Jan 2026)](https://www.ashbyhq.com/talent-trends-report/reports/2025-hiring)
- Ashby: inbound share of hires averages about 50% across company sizes but varies widely at small firms. About 10% of companies with 500–10,000 employees fill 70%+ of roles from inbound. **[PRIMARY, vendor]** — [Ashby Inbound report](https://www.ashbyhq.com/talent-trends-report/reports/inbound)

**Easy Apply**
- No dataset quantifying Easy Apply's effect on applicant counts or response rates was found. The Forage only notes that Easy Apply postings may get more applications. LinkedIn's displayed applicant count is often capped at "100+". **[WEAK]** — [The Forage](https://www.theforage.com/blog/basics/linkedin-easy-apply); [LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a512353)

### Inferences
- **Remote multiplier:** applications ÷ postings = 46/10 ≈ 4.6x the average competition per remote posting (US, 2023). Non-remote roles take 54% of applications across 90% of postings, about 0.6x average, so a remote role faces about 7–8x the applicants of an on-site or hybrid role. Fortune's "about 5x" is a looser framing. For Europe, the Ireland 2.4x ratio suggests a smaller but still large multiplier.
- A reasonable default baseline is about 250–300 applications per role or hire on modern ATSs (2024–2026), higher for remote roles, famous brands and Easy Apply/LinkedIn-sourced postings.
- Big brands combine huge volume with a low acceptance rate (0.2–0.5%). Smaller firms see lower volume but hired less in 2025, which leaves fewer openings with less competition each.

### Gaps
- No reliable 2023–2026 applicants-per-posting figure split by company size or brand fame. Google's 0.2% is from 2014.
- No Easy Apply vs external-apply applicant-volume or response-rate data.
- Glassdoor and Workday applicants-per-posting reports were not located.
- Remote application-share data after Dec 2023 (US) is not published in a comparable form.

---

## Q3. Ghost and stale jobs: prevalence, posting longevity and detection signals

### Takeaway
Credible estimates put **about 18–22% of postings** on a major ATS (Greenhouse, 2024) as no-intent-to-hire. About 40% of hiring managers in one survey say their company posted a fake listing (Resume Builder 2024, weak). Revelio finds **hires per posting fell from 0.75 (2018) to under 0.5 (2023)**. About a third of Indeed ads are **more than 30 days old** (Kickresume, Sept 2026: US 36%, UK 27%, tech 43%). Posting age over about 30 days is the most-used detection signal. Exact reposts are rare (about 0.1%).

### Cited Findings
**Prevalence**
- Greenhouse (platform data, 2024): **18–22% of jobs posted on Greenhouse in any given quarter were ghost jobs** ("positions advertised with no intent to hire"); **18.9% in Q2 2024**. About **70% of employers** on Greenhouse listed at least one in Q2 2024. Methodology not disclosed. **[PRIMARY, vendor; method opaque]** — [Greenhouse 2024 State of Job Hunting](https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report); [Entrepreneur](https://www.entrepreneur.com/business-news/ghost-job-listings-on-the-rise-how-to-spot-avoid-experts/485494)
- Greenhouse candidate survey (2,500 in the US, UK and Germany; Dec 2024): **60% suspect they have encountered a ghost job**; 29% of those applied anyway; **61% were ghosted after an interview**, up 9 pp since April 2024. **[PRIMARY, survey of perception]** — [Greenhouse 2024 report](https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report)
- Resume Builder (May 2024, US hiring managers): **40% of companies posted a fake job listing** that year; **30% were currently advertising** a role that is not real. Top reasons: to appear open to external talent and to look like the company was growing. Sample size is reported inconsistently: about 649–650 in CBS, Fortune and NBC coverage vs 1,641 on Resume Builder's page. This is a share of companies, not of listings. **[WEAK]** — [Resume Builder](https://www.resumebuilder.com/ghost-jobs/); [NBC](https://nbcnewyork.com/news/business/money-report/4-in-10-companies-say-theyve-posted-a-fake-job-this-year-what-that-actually-means/5546717)
- Resume Builder 2026 job-seeker survey: **86% report encountering a suspected ghost job**. This measures perception, not verified intent. **[WEAK]** — [ConsumerAffairs](https://www.consumeraffairs.com/news/ghost-jobs-leave-applicants-questioning-which-employers-are-actually-hiring-110226.html)
- Revelio Labs (US, posting-to-hire matching by company, role, seniority and state within 6 months): **hires-to-postings ratio fell from 0.75 in 2018 to under 0.5 in 2023**. The steepest 2018–2022 declines were in Administration & Support (−55.2%) and Construction (−54.9%). **[PRIMARY, data vendor]** — [Revelio Labs: Ghost job postings](https://www.reveliolabs.com/news/macro/ghost-job-postings/); [Revelio: When job postings don't mean hires](https://www.reveliolabs.com/news/macro/when-job-postings-dont-mean-hires/)
- Counterpoint: Indeed's career-trends expert said ghost jobs are "not a prevalent issue". Indeed Hiring Lab suggests cheap posting may drive long-lived, low-interaction "ghost postings". — [NPR, June 2024](https://www.npr.org/2024/06/07/1197965117/ghost-jobs); [Indeed Hiring Lab](https://hiringlab.indeed.com/?p=19776)
- Press synthesis (Nov 2025): "up to 1 in 3 job listings don't result in hires". **[SECONDARY]** — [CPA Practice Advisor](https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/)

**How long postings stay up**
- Clarify Capital 2022 (1,045 US hiring managers, Aug–Sep 2022): **27% admitted leaving postings up for more than 4 months**; 1 in 10 had a posting open for more than 6 months; 68% had postings active for more than 30 days. **[WEAK, survey]** — [Fortune, Mar 2023](https://fortune.com/2023/03/22/ghost-jobs-companies-posting-fake-listings/); [Clarify Capital 2022 survey](https://clarifycapital.com/job-seekers-beware-of-ghost-jobs-survey)
- Clarify Capital 2025 follow-up: **about 1 in 8 employers** left a job open for more than 4 months, and the share with postings active over 30 days was about half the 2022 rate. **[WEAK]** — [Clarify Capital Ghost Jobs 2025](https://clarifycapital.com/ghost-jobs)
- Clarify Capital Feb 2026 scrape (176,268 unique Indeed US listings across 49 industries and all states): **4% of posts were active 4 months or longer**. The study treats listings older than 30 days as potential ghost jobs. **[SECONDARY]**: from search snippet; the page returned 403 — [Clarify Capital Ghost Jobs 2026](https://clarifycapital.com/ghost-jobs-2026)
- Kickresume (96,902 Indeed ads, Sept 14–18, 2026; 77,681 US and 19,221 UK; six industries): **34% of ads were older than 30 days** (US 36%, UK 27%). By industry: technology 43%, healthcare 31%, business 30%; UK finance 37%. **Exact reposts were 0.1%** (recruitment 0.6%, US recruitment 0.7%). "Urgent hiring" with no closing date was 0.1%. The authors call these warning signs, not proof. **[PRIMARY, small vendor; one-time snapshot]** — [Kickresume ghost jobs study](https://www.kickresume.com/en/press/ghost-jobs-study/)

**Detection signals (platform mechanics)**
- Indeed: each real job should appear only once, and a duplicate filter blocks copies. Reposting a 30+ day-old ad as new resets its displayed age (anecdotal test). Indeed reportedly applies a 30-day visibility decay. **[SECONDARY/anecdotal]** — [Indeed duplicates policy](https://uk.indeed.com/help/employers/articles/job-posting-integrity-and-duplicates); [Haley Marketing](https://www.haleymarketing.com/?p=44644); [Workstream](https://www.workstream.us/blog/indeed-2026-job-visibility-changes-30-day-decay)
- Datapeople (job-ad analytics) flags "job post has been open too long" as a quality warning. — [Datapeople help](https://help.datapeople.io/article/236-job-post-has-been-open-too-long)

### Inferences
- **Prior:** treat about 15–25% of postings as no-intent-to-hire (Greenhouse 18–22%). In 2023, under 0.5 hires per posting means that at most about half of postings yield a matched hire within 6 months (Revelio).
- **Age is the strongest observable signal:** more than 30 days old is about the 66th percentile of live Indeed ads. More than 76 days exceeds Ashby's median technical time to first fill. More than 120 days old is rare (4%) and strongly suspicious. A stepped penalty fits the data: 0–14 days none; 15–30 days mild; 31–60 days moderate; 61–120 days strong; over 120 days very strong.
- **Reposts:** exact reposts are rare (0.1%), but "refreshed" postings that reset their age are common in practice. A candidate-side algorithm should track first-seen date per normalized job (company, title, location) instead of trusting the displayed posting date.
- **Other heuristic signals** (reasonable but not quantified by any source found): the same role continuously open or reposted across months; an employer with many open roles but flat or declining headcount (Revelio-style hiring-vs-postings gap); evergreen or "talent pool" wording; no salary or hiring manager; "urgent" with no closing date; a role posted on a job board but absent from the company's own ATS or careers page; the company's posting count far above its plausible hiring rate. Sectors with high ghost rates include admin/support, construction, recruiting, and tech (by age share).

### Gaps
- No direct JOLTS-based quantification of ghost postings was fetched. Bloomberg (Sept 2023) covered JOLTS-vs-hires gaps, but its figures were not verified here.
- Greenhouse's ghost-job classification methodology is undisclosed.
- No published data on the predictive accuracy of any single signal (salary missing, repost, etc.) for "no hire".
- No Europe-wide ghost-job prevalence beyond the UK Kickresume snapshot and the Greenhouse UK/Germany perception survey.

---

## Q4. Response and callback rates by application channel and company size

### Takeaway
Referrals convert roughly 4x to 10x better than cold applications. Lever's widely cited ratios are 1 in 16 hired for referrals vs 1 in 152 for careers-site or job-board applicants. Ashby: 40% of referred candidates reach an interview. Inbound applications still produce about 43–52% of hires because of sheer volume (Ashby 2021–2025). No reliable data was found splitting cold-apply callback rates by company size.

### Cited Findings
- Lever (older; publication year not visible): hire rate is **1 in 16 for referred** candidates, **1 in 22 for agency**, **1 in 72 for proactively sourced**, and **1 in 152 for careers-site or job-posting applicants**. **[SECONDARY]** — [SHRM on Lever study](https://www.shrm.org/resourcesandtools/hr-topics/talent-acquisition/pages/lever-study-candidates-hired.aspx)
- Ashby: **about 40% of referred candidates go from application to interview**. **[PRIMARY, vendor]** — [Ashby Referrals report](https://www.ashbyhq.com/talent-trends-report/reports/referrals)
- Ashby (about 250K hires, Jan 2021 to Jun 2025): **inbound = 43–52% of hires** (52% in Q2 2025), **referral about 17–18%**, **sourced about 16%**. Executive roles fill about 35% from inbound. Tech roles fill 24% from sourcing vs 18% for business roles. **[PRIMARY, vendor]** — [Ashby Inbound report](https://www.ashbyhq.com/talent-trends-report/reports/inbound)
- Jobvite (older): job boards and career sites supplied about **77% of applicants**, while referrals supplied **about 37% of hires**. Another framing: about 7% of applications come from referrals but about 40% of hires. **[WEAK/older]** — [SHRM: Employee referrals remain top source of hires](https://www.shrm.org/topics-tools/news/talent-acquisition/employee-referrals-remain-top-source-hires)
- Breezy HR: employee referrals convert at **8%, about 4x any major job board**. **[WEAK, vendor SMB]** — [Breezy Source of Hire report](https://breezy.hr/resources/hiring-reports/source-of-hire-report)
- Pinpoint: referrals are **"7x more likely to be hired"** than job-board candidates. **[WEAK, vendor]** — [Pinpoint](https://pinpointhq.com/insights/referrals-are-7x-more-likely-to-be-hired-than-job-board-candidates)

### Inferences
- From Lever's ratios, the baseline cold-apply hire probability is about 0.66% per application (1/152), and a referral raises it about 9.5x (to 1/16). Ashby's roughly 300 applications per hire, with inbound at about 50% of hires, implies an inbound hire rate per application below 1%, which is consistent with Lever.
- Company site vs job board: Lever pools careers site and job postings together, so no split was found. Applying via the company's own ATS at least avoids aggregator duplicates and ghost reposts. This is a heuristic.

### Gaps
- No 2022–2026 primary data on callback rates for company site vs LinkedIn Easy Apply vs Indeed.
- No callback or response rate by company size for cold applicants.
- The Lever and Jobvite study dates could not be confirmed from the snippets; they are likely pre-2020.
