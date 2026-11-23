# Skill growth, learning tracking, career-path prediction, CV tailoring and application outcomes

Scope: evidence base for a career assistant's "Learning" and "Resume" modules, linked to job matching. The user is one person in Turkey targeting software/AI roles in the EU or remote.

Evidence labels used below:
- **[PEER]**: peer-reviewed journal or top conference.
- **[WP]**: academic working paper (NBER, arXiv, SSRN), not yet peer-reviewed.
- **[INDUSTRY]**: vendor or industry data, often self-selected samples and commercial interest.
- **[WEAK]**: methodology not disclosed, single source, or commercial claim that was not verified.

---

## 1. Skill gap analysis against target jobs, and how to prioritise what to learn

### Takeaway
Most products and research models describe a job as a set of skills, using a taxonomy such as ESCO or a vendor skills graph. The gap is the set difference between the skills the target postings ask for and the skills the person has. A skill's value is not fixed: it depends heavily on which other skills it is combined with. Ranking should therefore weigh how often a skill appears in the person's own target postings, how much it adds alongside the skills they already have, and how much it costs to learn, rather than using one flat "hot skills" list.

### Cited Findings
- LinkedIn's "skills-based talent pool" finds candidates who held *different job titles but have similar skills*. LinkedIn links a skill to a job only when a very high share of people in that job list the skill [INDUSTRY]. — [LinkedIn Economic Graph, Skills-based hiring, March 2025](https://economicgraph.linkedin.com/content/dam/me/economicgraph/en-us/PDF/skills-based-hiring-march-2025.pdf)
- LinkedIn reports that workers matched on skills rather than titles qualify for over 3x as many roles. A separate skills-first report estimates that a skills-first approach in the US would grow eligible talent pools by about 20x, and by up to 22x in some industries. These are modeled pool sizes, not measured hires, and the 3x and 20x figures measure different things [INDUSTRY]. — [LinkedIn Skills Signal report 2025](https://economicgraph.linkedin.com/content/dam/me/business/en-us/talent-solutions/resources/pdfs/the-skills-signal-report-2025.pdf); [LinkedIn Skills-First report 2023](https://economicgraphchallenge.linkedin.com:443/content/dam/me/economicgraph/en-us/PDF/skills-first-report-2023.pdf)
- LinkedIn's "Career Explorer" suggests possible job transitions from skills similarity between occupations [INDUSTRY]. — [LinkedIn Economic Graph skills resources](https://economicgraph.linkedin.com/research/skills-based-resources)
- **Complementarity drives a skill's price.** Stephany & Teutloff studied 962 skills in online freelance projects. A skill's value depends mostly on how well it combines with other skills, and on average AI skills raise wages by about 21% [PEER, Research Policy 2024]. — [arXiv 2210.01535](https://arxiv.org/abs/2210.01535v4)
- Oxford's coverage of the same study reports skill-level premiums of about +40% for machine learning and +38% for TensorFlow, with deep learning, NLP and data science lower. The data covers freelance platforms only, and reported sample sizes differ between sources (about 25k workers vs. about 50k projects). — [Oxford news release, Oct 2023](https://www.ox.ac.uk/news/2023-10-24-artificial-intelligence-skills-can-increase-salaries-much-40)
- Lightcast analysed more than 1.3 billion job postings. Postings that ask for AI skills advertise about 28% higher salaries, roughly $18,000 a year. In 2024, more than half of postings asking for AI skills were outside IT and computer science. A 43% premium for two or more AI skills appears only in secondary press coverage [INDUSTRY; advertised pay, not realised pay]. — [Lightcast press release, July 2025](https://lightcast.io/resources/blog/beyond-the-buzz-press-release-2025-07-23); [Lightcast report page](https://lightcast.io/resources/research/beyond-the-buzz-developing-the-ai-skills-employers-actually-need); [Fortune coverage](https://fortune.com/2025/07/27/artificial-intelligence-skills-18000-salaries-28-percent/)
- Huntr user data shows **postings that name an AI skill had a lower per-application interview rate**: 4.3% vs. 5.5% for other postings. Demand for a skill is not the same as an easy route to interviews, because popular postings draw more competition [INDUSTRY]. — [Huntr Q3 2026 report](https://huntr.co/research/job-search-trends-q3-2026)
- Research on resume-to-occupation matching uses ESCO. CareerBERT places resumes and ESCO jobs in a shared embedding space for job recommendation [WP]. — [arXiv 2503.02056](https://arxiv.org/html/2503.02056v1)

### Inferences
- **Recommended prioritisation score** for each candidate skill *s*, computed over the user's own target postings (saved or high-match jobs), not the whole market:
  `priority(s) = demand(s) × Δmatch(s) × premium_or_trust(s) / cost(s)`
  - `demand(s)` is the share of target postings that mention *s*. Weight "required" mentions above "nice to have", and weight recent postings more heavily.
  - `Δmatch(s)` is how much the user's match score would rise across the target set if *s* were added. Simulate it by re-running the existing job-matching scorer with *s* added. This captures complementarity, which Stephany & Teutloff show is the main driver of a skill's value.
  - `premium_or_trust(s)` is optional. Use a market premium where one exists (Lightcast or the Oxford estimates), but cap its weight, because these are advertised-pay or freelance figures.
  - `cost(s)` is estimated learning hours. Discount it when the user already has an adjacent skill: for example, PyTorch is cheaper for someone who already knows TensorFlow.
- Work at the ESCO skill or skill-group level so that synonyms collapse ("LLM fine-tuning" and "fine-tuning transformers" count as one skill). Map the user's skills into the same taxonomy before taking the difference.
- Because complementarity matters, the module should prefer the **next skill that unlocks the most target postings given what the user already has**, which is a greedy set-cover over postings. A globally "hot" skill should not win on popularity alone.

### Gaps
- The exact algorithms behind LinkedIn's skills-gap or Skills Path features and Coursera's skill-to-job mapping are not published. I found no peer-reviewed validation that those product gap scores predict hiring.
- I did not verify ESCO's current counts of occupations and skills (roughly 3k occupations and 13.9k skills in v1.1 from memory). Check them on esco.ec.europa.eu before quoting.
- I found no study that validates the specific "demand × gain × cost" formula against outcomes. It is a design recommendation, not a tested method.

---

## 2. Learning-path recommendation, knowledge tracing and measuring progress credibly

### Takeaway
Knowledge-tracing models such as BKT and DKT were built for tutoring systems with thousands of graded exercise attempts per learner, and that data does not exist for a single adult professional. Two pieces of learning science do transfer well: spacing, with reviews timed as a fraction of how long the user needs to remember the material, and evidence-based mastery, meaning graded assessments, shipped projects and verified credentials rather than self-report. Shallow, interpretable models do as well as deep ones even in the domain where they were developed.

### Cited Findings
- **BKT** (Corbett & Anderson 1994) models each skill as a hidden binary "known / not known" state with four parameters: initial knowledge, learning (transition), guess and slip [PEER]. — [Corbett & Anderson 1994, UMUAI](https://doi.org/10.1007/BF01099821)
- **DKT** (Piech et al. 2015) uses an RNN over exercise sequences. It reported a large AUC gain over prior results on the ASSISTments benchmark (about a 25% gain, AUC of about 0.86) [PEER, NeurIPS]. — [Piech et al. 2015, arXiv 1506.05908](https://arxiv.org/abs/1506.05908); gain figure as summarised in [Khajah et al. 2016](https://arxiv.org/abs/1604.02416v2)
- **Khajah, Lindsey & Mozer (2016):** once BKT is extended with forgetting or recency, individual ability differences and inter-skill similarity, it performs **indistinguishably from DKT**. A secondary summary says enhanced BKT reached AUC of about 0.90 vs. 0.86 for DKT; I did not verify that figure in the PDF [PEER, EDM 2016]. — [arXiv 1604.02416](https://arxiv.org/abs/1604.02416v2)
- Wilson, Khajah, Lindsey & Mozer conclude that student proficiency assessment "does not appear to be a domain that benefits from 'depth'"; shallow models do as well and are easier to interpret [WP, NIPS 2016 workshop]. — [Wilson et al. 2016](https://home.cs.colorado.edu/~mozer/Research/Selected%20Publications/reprints/Wilsonetal2016.pdf)
- **Spacing (Cepeda et al. 2008):** more than 1,350 participants, with study gaps of up to 3.5 months and final tests up to 1 year later. **The best gap between study sessions is about 20–40% of the retention interval for a 1-week test, falling to about 5–10% for a 1-year test.** Gaps that are too short or too long both reduce retention [PEER, Psychological Science]. — [PubMed 19076480](https://pubmed.ncbi.nlm.nih.gov/19076480/)
- **FSRS vs. SM-2:** the open-spaced-repetition benchmark scores algorithms by log loss on real Anki review histories. Secondary sources report that FSRS beats an adapted SM-2 on about 97–99.6% of collections. The exact figures differ across FSRS versions and sources, so check them in the repository [INDUSTRY / open-source benchmark, not peer-reviewed]. — [Expertium benchmark](https://expertium.github.io/Benchmark.html); [srs-benchmark repo](https://github.com/open-spaced-repetition/srs-benchmark)
- **Practice hours alone explain little in professional work.** In a meta-analysis of 11,135 participants, deliberate practice explained 26% of performance variance in games, 21% in music, 18% in sports, 4% in education and **less than 1% in professions** [PEER, Psychological Science 2014]. A reanalysis with stricter inclusion criteria found far more variance explained, so this is contested. — [Macnamara, Hambrick & Oswald 2014](https://pubmed.ncbi.nlm.nih.gov/24986855/); critique discussed in [PMC6824411](https://pmc.ncbi.nlm.nih.gov/articles/PMC6824411)
- **Verified signals beat claimed ones in hiring markets.** On an online freelance platform, workers' earnings rose after they earned platform-verified microcredentials. The mechanism was **less employer uncertainty, not higher productivity**, and the gain came from winning higher-value jobs rather than more jobs. Microcredentials and other verified information are partial substitutes [PEER, Journal of Human Resources 2024]. — [Kässi & Lehdonvirta, OECD/CESifo working paper](https://www.oecd.org/en/publications/do-digital-skill-certificates-help-new-workers-enter-the-market_3388385e-en.html); [JHR version](https://jhr.uwpress.org/content/early/2022/03/01/jhr.0519-10226R3)
- On the same platform, workers who complete more skill tests are negatively selected (on average more disadvantaged in the market). Certificates helped people with some work experience more than complete newcomers. The authors suggest stricter tests would make certificates more useful to newcomers. — [Kässi & Lehdonvirta, CESifo WP 7810](https://cesifo.org/DocDL/cesifo1_wp7810.pdf)
- **Verified performance information has large effects for newcomers.** Pallais hired 952 randomly selected inexperienced workers on oDesk and gave them either detailed or coarse public evaluations. Both being hired and receiving a detailed evaluation substantially improved later employment [PEER, AER 2014]. — [Pallais, NBER w18917](https://www.nber.org/papers/w18917)

### Inferences
- **Recommended progress model.** Use a per-skill mastery estimate in the BKT style, one interpretable probability per skill, updated from *evidence events* rather than exercise clicks. Weight each event by how verifiable it is:
  1. Third-party verified: proctored or graded assessment, platform certificate with an exam, a merged PR in a known open-source repository, or a paid client or employer deliverable.
  2. Public artifact: a GitHub repository with tests, commits over time, and a README or demo; a published write-up.
  3. Course completion with graded work.
  4. Self-rating, which carries the lowest weight and should only set a prior.
  Add a forgetting decay, as in BKT with forgetting, so that skills not used for months lose confidence.
- Do not build DKT for one user. There is not enough data, and Khajah et al. show the depth adds nothing even when data is plentiful.
- Use spacing for *conceptual* knowledge, such as system design facts or ML theory for interviews. Schedule reviews with FSRS, or with Cepeda's rule of thumb: a gap of about 10–20% of the time until the expected interview. For *procedural* skills, track shipped projects instead of flashcards.
- Show the user that **visible, verified evidence is what moves hiring outcomes** (Kässi & Lehdonvirta; Pallais; Athey & Palikot in section 3). The Learning module should end each learning goal with a portfolio artifact that can go on the CV.

### Gaps
- I found no peer-reviewed knowledge-tracing work aimed at adult professionals learning job skills outside tutoring systems or MOOCs.
- IRT (Item Response Theory) was not researched in depth here. It is standard for calibrating assessment difficulty, but I collected no specific source.
- I found no validated method that scores skill level from GitHub activity. Any such scoring is heuristic.

---

## 3. Time to learn, and whether learning or credentials raise callbacks or pay

### Takeaway
The best causal evidence that online credentials help is modest and depends on the person: making a credential visible raised new-job rates by about 6% on average and about 12% for the least employable third, with near-zero effect for strong profiles (Athey & Palikot, an RCT with 800k learners). Credential prestige matters, as shown in callback audits. Skill premiums from postings or freelance data (21–28%) are correlations in advertised or contract pay, not causal effects of learning. I found no rigorous time-to-learn estimates.

### Cited Findings
- **Athey & Palikot (2024):** a randomized experiment with more than 800,000 certificate earners from developing countries without college degrees encouraged them to share credentials on LinkedIn. Among 40,000 learners whose employment was tracked, new employment rose by **+6% (1.0 percentage point)** and jobs related to the certificate by **+9% (1.2 pp)**. The **bottom tercile of baseline employability gained about +12%; the top tercile saw negligible effects**. The complier LATE was **11 pp**. In a counterfactual LLM-based resume-scoring exercise, credentials raised perceived quality by **8.5 points out of 100** on average, by **15–20 points for weak resumes**, and by about zero for strong ones [WP, arXiv]. — [arXiv 2405.00247](https://arxiv.org/abs/2405.00247)
- **Deming et al. (2016) resume audit:** a business BA from a for-profit online institution drew about **22% fewer callbacks** than one from a non-selective public institution. For health jobs that do not require a certificate, for-profit certificates drew **57% fewer** callbacks than community-college certificates. Where a licence was required, there was no difference, because employers relied on the external quality signal [PEER, AER 106(3)]. — [NBER w20528](https://www.nber.org/papers/w20528); [Harvard Kennedy School summary](https://www.hks.harvard.edu/publications/value-postsecondary-credentials-labor-market-experimental-study)
- **Kässi & Lehdonvirta:** platform microcredentials raise earnings by reducing employer uncertainty, and help most when the worker has some experience [PEER, JHR]. — [OECD WP](https://www.oecd.org/en/publications/do-digital-skill-certificates-help-new-workers-enter-the-market_3388385e-en.html)
- Stanford MediaX funded a resume-audit field experiment on how MOOC credentials affect employability, starting with software development jobs in Silicon Valley. I found no published callback figures for it. — [Stanford MediaX project page](https://mediax.stanford.edu/?p=7415)
- **Coursera 2025 Learner Outcomes Report** (with The Harris Poll, more than 52,000 learners in 179 countries): 91% reported at least one positive career outcome and 46% a salary increase since enrolling. The figure was 94% in emerging economies vs. 84% in advanced economies. The 2023 edition reported 77% career benefit [INDUSTRY, self-reported, survivorship bias; definitions change between editions]. — [Coursera blog, 2025 report](https://blog.coursera.org/introducing-courseras-2025-learner-outcomes-report-global-findings-show-measurable-career-impact-for-online-learners); [2023 report](https://blog.coursera.org/coursera-2023-learner-outcomes-report)
- AI skill premiums: +21% on average on freelance platforms, with +40% for ML and +38% for TensorFlow (Stephany & Teutloff, [PEER]); +28% in advertised posting salaries (Lightcast, [INDUSTRY]). — [arXiv 2210.01535](https://arxiv.org/abs/2210.01535v4); [Lightcast](https://lightcast.io/resources/blog/beyond-the-buzz-press-release-2025-07-23)
- **Unemployment length lowers callbacks.** Kroft, Lange & Notowidigdo sent about 12,000 fictitious resumes to about 3,000 postings across 100 US metro areas. Callback probability **falls significantly with unemployment duration, mostly in the first 8 months**, and the effect is stronger in tight labor markets. A later NBER paper calibrated to this audit puts the gap at about 50% fewer interviews for the long-term unemployed. The audit covered sales, customer service, administrative and clerical jobs, not tech [PEER, QJE 2013]. — [NBER w18387](https://www.nber.org/papers/w18387); [NBER Digest](https://www.nber.org/digest/mar13/duration-dependence-and-labor-market-conditions); [NBER w24200](https://nber.org/system/files/working_papers/w24200/w24200.pdf)
- Contrast: a Russell Sage study of older workers found **no** relationship between unemployment duration and callbacks. — [Russell Sage / Project MUSE](https://muse.jhu.edu/article/659929)

### Inferences
- In the UI, describe a learned skill's benefit as "raises your match to N more of your target jobs", using `Δmatch` from section 1, rather than promising a salary gain. Causal evidence on pay from learning is weak.
- Credentials help most when the profile is otherwise weak or thin (Athey & Palikot; Kässi & Lehdonvirta). For a career switcher or junior applicant, recommending a recognised, exam-backed credential is better supported than for a senior candidate.
- Credential **source quality** matters (Deming et al.). Prefer certificates from recognised vendors or institutions with graded exams, such as cloud provider certifications, over completion badges.
- Because of duration dependence (Kroft et al.), gaps should be framed as active periods (projects, freelance work, courses) on the CV. The evidence comes from non-tech US jobs, so the size of the effect for EU tech roles is unknown.

### Gaps
- **No reliable time-to-learn data** turned up for specific tech skills, such as hours to job-ready proficiency in PyTorch, Kubernetes or LLM application development. Vendor course lengths (for example "X hours to complete") exist, but they are course durations, not measured time to competence. Best option: let users log hours, and calibrate per-user estimates from their own completion history.
- I did not locate a published Hadavand, Gooding & Leek MOOC callback experiment under that name; it may be unpublished or mis-attributed. The Stanford MediaX audit has no published numbers that I found.
- Lightcast also publishes skill-level premiums per skill (for example for Kubernetes or PyTorch), but they are behind its analyst platform. I found no public per-skill figures for EU or Turkey.
- Agrawal, Lacetera & Lyons (2016, J. International Economics) studied whether standardized, verified work information on oDesk disproportionately helps applicants from less developed countries. It is highly relevant for a Turkey-based applicant, but I did not verify its figures in this session.

---

## 4. Career trajectory and next-role prediction

### Takeaway
Research models predict the next title, company or ESCO occupation from career sequences with modest accuracy: the best published ESCO-based result is about 43% recall@10, meaning the true next occupation is in the top 10 suggestions less than half the time. These models are useful for generating a **shortlist of plausible next roles** ranked by skill overlap, not for single-answer predictions.

### Cited Findings
- **NEMO** (Li, Jing, Tong, Yang, He & Chen) predicts the next company and title with contextual LSTMs over LinkedIn career paths. It was published at **WWW 2017 (Companion), not KDD**, and it significantly outperforms baselines on a large LinkedIn dataset. Evaluation used Accuracy@k and MRR for company and title prediction; exact numbers were not retrieved [PEER]. — [NSF PAR copy](https://par.nsf.gov/biblio/10062452); [WWW 2017 listing](https://ir.webis.de/anthology/2017.wwwconf_conference-2017c.63)
- **Meng et al. (KDD 2019):** a hierarchical, career-path-aware network with attention models moves within and between firms. It predicts **both the next employer and the time until the move** [PEER]. Accuracy figures were not retrieved. — [Authors' PDF](https://qingxin-meng.github.io/KDD2019.pdf); [dblp record](https://dblp.dagstuhl.de/rec/bibtex/conf/kdd/MengZXZX19)
- **Decorte et al. (RecSys HR 2023):** 2,164 anonymised career histories annotated with ESCO occupations. Predicting the held-out next ESCO occupation gave **35.24% recall@10 (skill-based), 39.61% (text-based) and 43.01% (hybrid)** [PEER workshop]. — [arXiv 2310.15636](https://arxiv.org/pdf/2310.15636); [CEUR RecSysHR 2023](https://ceur-ws.org/Vol-3490/RecSysHR2023-paper_1.pdf)
- **JobHop** is a larger, LLM-extracted, ESCO-coded resume dataset released as a career-path-prediction benchmark [WP]. — [arXiv 2505.07653](https://arxiv.org/pdf/2505.07653v2)
- **CAPER** (temporal knowledge graph) reports substantially outperforming earlier career-trajectory methods, including NEMO [WP]. — [arXiv 2408.15620](https://arxiv.org/html/2408.15620v2)
- A 2023 survey of AI for talent analytics covers job-mobility and career-path models. — [arXiv 2307.03195](https://arxiv.org/pdf/2307.03195)
- LinkedIn Career Explorer and skills-based pools find transitions through skills similarity between occupations [INDUSTRY]. — [LinkedIn Economic Graph](https://economicgraph.linkedin.com/research/skills-based-resources)

### Inferences
- **Recommended "next step" method for one user**, since no individual sequence model can be trained:
  1. Map the user's current and past roles to ESCO occupations.
  2. Create candidate next roles from occupations related in ESCO or O*NET, plus occupations that frequently appear as next roles in public transition data.
  3. Rank candidates by (a) skill overlap with the user's evidence-weighted skill profile, (b) the number of open target-market postings (EU or remote) from the job pipeline, (c) the learning cost of the missing skills from section 1, and (d) the user's own stated preferences.
  4. Show 3–5 options with the skill gap for each one. Never present a single "predicted" role: about 43% recall@10 means the model is wrong far more often than right at top-1.
- Treat the trajectory model as a *candidate generator*. The skill-gap and posting-availability signals are what should decide the ranking.

### Gaps
- I did not retrieve exact top-k accuracy figures for NEMO or Meng et al.; they are in the papers' results tables.
- I did not research the O*NET "Related Occupations" methodology or its validation in this session.
- I found no study measuring whether next-role *recommendations* change real outcomes (job changes, pay) for users.

---

## 5. CV tailoring, cover letters, CV length and format

### Takeaway
The strongest causal evidence is that **better-written resumes raise hiring**: algorithmic writing help increased hires by about 8% in a large field experiment, with most of the gain for weaker resumes. Tailored cover letters helped in one industry audit (16.4% callbacks vs. 10.7% with no letter), but since generative AI arrived, the signal value of tailored text has collapsed on at least one platform. The "75% of resumes rejected by ATS" claim has no credible source. Length has little measurable effect; clarity and job titles do.

### Cited Findings
- **Wiles (van Inwegen), Munyikwa & Horton:** in a field experiment on a large online labor market, jobseekers randomly given algorithmic writing assistance on their resumes were **hired about 8% more often** and received about 7.8% more offers. Treated resumes had fewer errors and were easier to read. **Gains were concentrated among weaker resumes**, and already excellent resumes benefited little [PEER, Management Science 71(12), 2025]. — [NBER w30886](https://www.nber.org/papers/w30886); [Management Science](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2024.04528); [MIT Sloan coverage](https://mitsloan.mit.edu/ideas-made-to-matter/job-seekers-ai-boosted-resumes-more-likely-to-be-hired)
- **Galdin & Silbert, "Making Talk Cheap" (2025):** Freelancer.com launched an "AI Bid Writer" in April 2023 that drafts tailored cover letters. Before it, how closely a cover letter matched the job post was a hiring signal. Afterwards, the **signal value of written applications largely collapsed**, and hiring became less meritocratic: low-ability workers gained and high-ability workers lost [WP, job market paper]. — [arXiv 2511.08785](https://arxiv.org/abs/2511.08785); [Tuck summary](https://tuck.dartmouth.edu/news/articles/what-happens-to-hiring-when-ai-writes-job-applications)
- **Cui, Dias & Ye, same platform:** after the AI tool arrived, the correlation between how well a cover letter aligned with the job post and callbacks **fell by 51%**. The tool raised tailoring, and its callback effect was a 51% increase over a 7.02% pre-rollout callback rate, significant only at the 10% level [WP]. — [arXiv 2509.25054](https://arxiv.org/html/2509.25054v2)
- **ResumeGo cover-letter audit:** 7,287 fictitious applications on ZipRecruiter, Glassdoor and Indeed, July 2019 to January 2020. Callbacks were **10.7% with no letter, 12.5% with a generic letter and 16.4% with a tailored letter**, about 53% higher than no letter. 81% of 236 surveyed recruiters valued tailored letters over generic ones [INDUSTRY/WEAK: run by a resume-writing seller, not peer-reviewed or replicated, and before the rise of LLMs]. — [ResumeGo study](https://resumego.net/research/cover-letters)
- **The ATS "75% auto-rejected" claim:** it traces to an unverified 2012 estimate attributed to Preptel, a resume-service company that no longer exists (named in a single source). In Enhancv's recruiter survey, **92% of recruiters said their ATS does not auto-reject resumes for formatting, content or design**. Filtering in practice comes from knockout questions, keyword search by recruiters and sheer volume [INDUSTRY]. — [Enhancv](https://enhancv.com/blog/does-ats-reject-resumes/); [IT Brief coverage](https://itbrief.co.uk/story/study-reveals-ats-rarely-auto-rejects-cvs-debunks-75-myth); [dev.to on the Preptel origin](https://dev.to/ankjhsz/does-an-ats-reject-your-cv-before-a-human-sees-it-what-the-data-actually-shows-1k3c)
- **Jobscan-type keyword-match claims:** I found no independent or peer-reviewed validation of specific keyword-match targets (for example "aim for 75–80% match"). Treat them as [WEAK].
- **Ladders eye-tracking (2018):** recruiters' initial screen averaged **7.4 seconds**, up from about 6 seconds in the earlier study. Recruiters looked longest at **job titles**. Simple layouts with clear section headings held attention; multiple columns, clutter and long sentences did worse. An engaged recruiter reads a second page as closely as the first [INDUSTRY]. — [Ladders study PDF](https://www.bu.edu/com/files/2018/10/TheLadders-EyeTracking-StudyC2.pdf); [HR Dive](https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/)
- **Huntr Q3 2026 data on resume length and tailoring:** across 23,055 tailored resumes linked to jobs, the median length was 705 words, up from 585 a year earlier. **There was no clear link between resume length and interview rate at any career stage**; rates varied by 1.3 points or less. For 10+ years of experience, 2-page resumes had a 6.4% interview rate vs. 5.8% for 1 page. In the survey, 64% tailor most or all applications, 79% prefer 20 tailored applications over 100 with one resume, and **63% of AI users said AI added something untrue** to their resume [INDUSTRY, self-selected users]. — [Huntr Q3 2026](https://huntr.co/research/job-search-trends-q3-2026)

### Inferences
- **Recommended Resume module design:**
  - Keep one master CV, with every claim tied to an evidence item from the Learning module, and produce **role-family variants** (for example "ML engineer", "AI application or backend engineer", "data scientist") rather than a new CV for every posting. In each variant, reorder and select bullets, mirror the posting's skill terms *only where the user has evidence*, and align the title line with the target role, since recruiters look at titles most.
  - Run a **truthfulness guard**: never add a skill that has no evidence item. 63% of AI-assisted users report untrue additions, and hiring signals now punish cheap text.
  - Use AI for clarity and error correction, where the causal evidence is strong (about +8% hires). Be cautious about relying on tailored cover-letter text as a differentiator, since its signal value collapsed after LLMs. Write cover letters only when the employer asks, or when there is a specific, verifiable hook such as a referral, a relevant project or a link to an artifact.
  - Format: single column, clear headings, plain text-parsable. Length is secondary: 1 page for junior candidates, 2 is fine for experienced ones.
- **Feedback loop: choosing a CV variant from outcomes.** Each application logs `variant_id`, role family, channel, posting features and outcome (no response, rejection, screen, interview, offer). For each role family, treat the choice of variant as a **Beta-Bernoulli Thompson sampling bandit** on "reached screen or interview". Use priors centred near the user's baseline interview rate, about 4–6% (section 6). With rates this low, one person cannot detect differences reliably: telling 4% from 8% at conventional significance takes roughly 300+ applications per arm. So (a) pool across closely related variants hierarchically, (b) attribute outcomes partly to channel and posting quality, since the channel effect (for example career site vs. LinkedIn) is larger than plausible CV effects, and (c) show the user the uncertainty instead of declaring a winner after 10 applications.

### Gaps
- I found no peer-reviewed correspondence experiment that directly randomises *tailored vs. generic resumes* (as opposed to cover letters or writing quality) for software or AI roles.
- I found no EU- or Turkey-specific evidence on CV format norms beyond general guidance; Europass usage effects are unknown.
- I did not verify Jobscan's own claims about match rates directly.

---

## 6. Application outcome tracking: funnel benchmarks

### Takeaway
Typical logged per-application interview rates are now about **3–6%**. They are lower through LinkedIn and Indeed (about 3.5%) and for remote-only postings (3.4%), and higher on employer career sites (about 6%) and through former employers or referrals (13–18%). Interviewers handle more candidates per hire than five years ago. A software/AI job seeker should benchmark against these figures, broken down by channel.

### Cited Findings
- **Huntr Q3 2026** (84,753 logged applications, 4,796 users; about 32% of jobs with an industry were in internet software and services; findings are most reliable for US tech and professional roles) [INDUSTRY]. — [Huntr Q3 2026](https://huntr.co/research/job-search-trends-q3-2026)
  - Interview rate per application by channel: employer career sites **6.0%**, ATS pages **4.8%**, job boards **3.4%**. Over the trailing 12 months: Google job search **9.9%**, LinkedIn **3.6%**, Indeed **3.6%**. By ATS: BambooHR 6.8%, Greenhouse and Workday 4.2%, Lever 4.0%.
  - **Remote-only postings: 3.4% vs. 5.3%** for hybrid-only and onsite-only postings (same-person comparison: 3.4% vs. 5.5%).
  - Entry-level titles 3.9%; senior titles 6.4%.
  - Former employers 17.6% vs. 8.6% elsewhere (same-person comparison).
  - **Volume vs. quality:** users with 11–20 applications had an 8.0% interview rate (47.8% got at least one interview); users with 100+ had 2.4% (72.0% got at least one). Applying at 3x the user's usual pace cut the rate from 9.5% to 5.6%, but raised interviews per month from 0.7 to 2.9.
  - Repeat applications to one company: 5.9% for a single application, 2.4% per application at 8 or more, while the cumulative chance of an interview rose to 17.7%.
  - **Timing:** median 5 days from application to interview, 7 days from interview to offer, 52 days to first interview and **102 days to first offer** (up from 91 in Q2 2026).
  - Of seekers who applied at least 11 times, **65% got an offer within 50 applications**; the largest group (29.3%) got one after 11–20.
  - Ghosting (survey, n=271): 37% say employers often or very often stop responding after an interview.
- **Huntr Q2 2025:** Google Jobs had a 9.3% response rate vs. 3.3% on LinkedIn, and median time to first offer rose 22% to 68.5 days [INDUSTRY]. — [Huntr Q2 2025](https://huntr.co/research/job-search-trends-q2-2025)
- **Ashby employer-side data:** applications per hire rose from **121 (Q1 2021) to 291 (Q1 2026)**, after averaging above 300 per quarter in 2025. Candidates are about half as likely to get an interview as five years ago. For technical roles, candidates interviewed per hire rose from about 11.6 to 17.6 (from a secondary write-up). In 2025, product management needed the most interviews per hire among technical roles (20.6) and design the fewest (15.3) [INDUSTRY]. — [Ashby Recruiting Operations Benchmarks 2026](https://www.ashbyhq.com/talent-trends-report/reports/recruiting-operations-benchmarks-talent-trends); [Ashby Recruiter Productivity](https://www.ashbyhq.com/talent-trends-report/reports/2023-recruiter-productivity-trends-report?); [secondary write-up](https://techintelpro.com/news/hr/talent-acquisition/ashby-reveals-five-year-hiring-evolution-at-ashby-one-2026)
- Implied from Ashby (my calculation): about 17.6 interviewed per technical hire ÷ about 291 applications per hire ≈ **6%** of applications reaching an interview. This is rough, because it mixes technical-role and all-role figures. — derived from the sources above.
- **Kroft et al.:** callbacks decline with time spent unemployed, mostly in the first 8 months [PEER]. — [NBER w18387](https://www.nber.org/papers/w18387)

### Inferences
- **Benchmarks for the user's dashboard** (industry data, mostly US; adjust as the user's own data comes in):
  - Application → any human response or screen: compare against roughly 4–8%. Most applications get no reply, so record "no response after 21 days" as its own state.
  - Application → interview: about 3.5% on LinkedIn or Indeed, about 6% on company career sites, about 3.4% for remote-only roles, and 13–18% via referral or former employer.
  - Interview → offer: no reliable public per-interview figure was found. Use ~50 applications to an offer as a loose median from Huntr (65% got an offer within 50 applications, among those who applied at least 11 times).
  - Time: about 3.5 months median to first offer. Alert the user if no interview after about 40–50 applications, then check whether the target set or the CV variant is the problem.
- **For a Turkey-based applicant aiming at EU or remote roles**, expect rates below these benchmarks. Remote-only roles already convert worse (3.4%), and work-authorisation or visa screening knocks applicants out early. This is my inference; I found no direct data. The module should segment outcomes by "requires EU work authorisation", "visa sponsorship offered" and "global remote", and prefer channels with higher conversion: company career sites, referrals and Google-indexed postings.
- Track funnel metrics by **channel × role family × CV variant × seniority**, because the channel and seniority effects (2–3x) are larger than any plausible CV effect, and attributing outcomes to the CV alone would mislead.

### Gaps
- I found no published funnel benchmarks specific to software or AI roles in the EU, or to applicants from Turkey. Huntr and Ashby are US-weighted.
- Greenhouse, Teal and Indeed Hiring Lab funnel figures were not retrieved in this session.
- I found no reliable public interview-to-offer conversion rate for software engineering. Employer-side figures (interviews per hire) mix all candidates.
