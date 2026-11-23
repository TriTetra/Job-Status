# Job Quality, Career Value and Employer Stability (the "value" component of candidate-side job scoring)

Research date: 2026-11-23. Method: web search + fetch (about 20 tool calls). Several primary pages (Glassdoor blog, McKinsey MGI) returned 403/timeout; where a figure comes from a search-result summary instead of the primary page, it is flagged "(secondary)". Vendor data (Carta, layoffs.fyi, Crunchbase, LinkedIn, Glassdoor, Gallup, Work Institute, Revelio) is flagged as such.

## 1. Job quality frameworks: OECD, Eurofound, ILO — dimensions and measurement

### Takeaway
The OECD framework has three measurable dimensions — earnings quality (level and distribution), labour market security (risk and cost of unemployment), and quality of the working environment (job strain = high demands + low resources). Eurofound splits job quality into seven separate indices and deliberately does not collapse them into one score because of trade-offs. Both imply that a job "value" score should be multi-dimensional with partial compensation between dimensions, not a single pay number.

### Cited Findings
- OECD Job Quality Framework (Cazes, Hijzen & Saint-Martin, OECD Social, Employment and Migration Working Paper No. 174, 2015) defines three dimensions: earnings quality, labour market security, quality of the working environment — [OECD](https://www.oecd.org/en/publications/measuring-and-assessing-job-quality_5jrp02kjw1mr-en.html); [VoxEU/CEPR column](https://cepr.org/voxeu/columns/measuring-quality-jobs-oecd-countries)
- Earnings quality captures both average earnings and their distribution (inequality-adjusted). Example: the US has about the same earnings quality as Ireland despite higher average earnings, because of much higher earnings inequality — [VoxEU/CEPR](https://cepr.org/voxeu/columns/measuring-quality-jobs-oecd-countries)
- Labour market insecurity is measured as the risk of unemployment times its expected cost, expressed as a share of previous earnings (i.e., expected earnings loss) — [VoxEU/CEPR](https://cepr.org/voxeu/columns/measuring-quality-jobs-oecd-countries)
- Working-environment quality is summarised by the incidence of job strain: high demands (time pressure, unhealthy conditions) combined with low resources (limited autonomy, limited training/learning opportunities) — [VoxEU/CEPR](https://cepr.org/voxeu/columns/measuring-quality-jobs-oecd-countries); [OECD job quality topic page](https://www.oecd.org/en/topics/job-quality.html)
- Eurofound's framework has seven dimensions: physical work environment, work intensity, working time (quality), social environment, skills and discretion, (career) prospects, earnings. The indices were built from aspects of work that independently influence health and well-being, first reported from the 2015 European Working Conditions Survey (EWCS) — [Eurofound job quality topic](https://www.eurofound.europa.eu/topic/job-quality)
- Eurofound explicitly does not produce a single composite job quality index "as clearly there are trade-offs between these different dimensions" — [Eurofound blog](https://www.eurofound.europa.eu/en/blog/2023/job-quality-pivotal-addressing-todays-workplace-and-societal-challenges)
- The 2021 telephone survey (EWCTS) used a six-dimension variant; the EWCS 2024 overview report (listed for 2026) reports men have higher job quality than women on five of seven dimensions — [Eurofound EWCS 2024 overview](https://www.eurofound.europa.eu/publications/all/european-working-conditions-survey-2024-overview-report) (secondary; full text not verified)

### Inferences
- For a candidate-side scorer, map dimensions to what's observable in a posting: earnings quality → stated pay vs market; labour-market security → contract type (permanent/fixed-term), employer stability signals; working environment → remote/hybrid, working hours/on-call, seniority/autonomy cues, learning/training mentions; Eurofound "skills and discretion" and "prospects" → learning/career-growth component.
- Eurofound's refusal to aggregate suggests using a weighted sum with floor penalties (a very bad dimension, e.g., insecure contract or extreme hours, should cap the score) rather than pure compensatory averaging.

### Gaps
- ILO Decent Work Agenda indicators were not retrieved in this run (commonly cited 10 substantive elements incl. adequate earnings, decent hours, stability/security, safe environment, social security, social dialogue) — needs a primary ILO source before citing.
- Exact OECD operational indicator definitions (survey items behind job strain) not retrieved; see the working paper DOI 10.1787/5jrp02kjw1mr-en.

## 2. What predicts satisfaction and retention; relative weight of pay vs other factors

### Takeaway
Across Glassdoor, MIT Sloan/Revelio, and Work Institute data, culture/values, senior leadership, and career opportunities consistently outrank compensation as predictors of overall satisfaction and attrition. Toxic culture was 10.4x more powerful than compensation in predicting company-level attrition (2021). Pay matters, but mostly as a threshold/hygiene factor; in a scorer, pay should be a large but not dominant weight, with culture/growth signals carrying comparable weight when available.

### Cited Findings
- Glassdoor US 2023 relative-importance breakdown of drivers of overall rating: culture & values 18.4%, senior leadership 17.6%, career opportunities 15.8%; compensation & benefits ~11% (among the lowest) — [Glassdoor blog: "What makes or breaks employee satisfaction remains intact"](https://www.glassdoor.com/blog/satisfaction-drivers-remain-intact/) (secondary — page returned 403 to fetch; numbers from search summary, verify)
- Glassdoor's multi-country research (5 countries) finds culture & values the top predictor of overall satisfaction; senior leadership is the strongest predictor of CEO approval — [Glassdoor employee-satisfaction drivers](https://api.glassdoor.com/blog/employee-satisfaction-drivers/); [Glassdoor CEO factors](https://static-pc.glassdoor.de/blog/top-ceo-factors-2019/) (secondary; vendor)
- Revelio Labs (vendor): culture & values is the most powerful driver of overall ratings; in a booming labour market (Great Resignation) career opportunities and senior leadership mattered most — i.e., weights shift with the labour-market cycle — [Revelio Labs](https://www.reveliolabs.com/news/business/company-culture-matters-most-in-a-cooling-labor-market/)
- MIT Sloan Management Review (Sull, Sull & Zweig, Jan 2022): a toxic corporate culture is 10.4 times more powerful than compensation in predicting a company's attrition rate relative to its industry. Data: ~600 companies, 172 culture metrics from Glassdoor reviews, attrition Apr–Sep 2021 from Revelio Labs, measured in SD from industry mean — [MIT SMR](https://sloanreview.mit.edu/article/toxic-culture-is-driving-the-great-resignation/)
- "Toxic Five" culture attributes: disrespectful, noninclusive, unethical, cutthroat, abusive — [MIT SMR](https://sloanreview.mit.edu/?p=98890)
- Work Institute 2025 Retention Report (2024 US exit data, vendor): career-related reasons (lack of growth, progression, development) are the leading cause of voluntary turnover, cited by 18.9% of quitters; career, work-life balance and management issues together = 63% of exits, deemed preventable; management-related turnover 9.7% in 2024 vs 7.4% in 2022 — [SHRM](https://www.shrm.org/topics-tools/news/talent-acquisition/career-development-gaps-frequently-drive-employee-turnover); [Work Institute 2025 report PDF](https://info.workinstitute.com/hubfs/2025%20Retention%20Report/2025%20Retention%20Report%20-%20Employee%20Retention%20Truths%20in%20Todays%20Workplace.pdf)
- Work Institute 2024 edition: career development has been the most-cited reason for leaving every year since tracking began in 2010; only 14% of leaders strongly agree they provide effective career development — [Work Institute 2024 report](https://info.workinstitute.com/hubfs/2024%20Retention%20Report/Work%20Institute%202024%20Retention%20Report.pdf); [SHRM](https://shrm.org/topics-tools/news/talent-acquisition/workers-are-quitting-because-work-life-balance-career-development)
- Gallup (vendor): global employee engagement 23% (2023) → 21% (2024) → 20% (2025); manager engagement 30% → 27% → 22% (2025); low engagement estimated to cost ~$10 trillion (≈9% of global GDP) in the 2026 release — [Gallup State of the Global Workplace](https://www.gallup.com/workplace/349484/state-of-the-global-workplace.aspx); [Gallup 2026 press release](https://www.gallup.com/file/workplace/712607/SOGW_Global-Press-Release-2026-04.pdf); [Gallup managers](https://www.gallup.com/workplace/659279/global-engagement-falters-managers-under-strain.aspx)

### Inferences
- Implied relative weights (from Glassdoor ~2023 decomposition, normalised): culture+leadership ≈ 36%, career opportunities ≈ 16%, comp ≈ 11%, remainder WLB/diversity etc. But a posting-based scorer cannot see culture directly; comp is observable and decisive at the acceptance stage. Practical blend: pay 30–40%, growth/learning 20–25%, stability/security 15–20%, working arrangements (remote/hours) 10–15%, culture/reputation proxy 10–15% when data exists (else redistribute).
- Because management/manager quality is a strong driver and is mostly invisible in a posting, the scorer should express lower confidence rather than assume average.

### Gaps
- No peer-reviewed estimate of pay vs culture weights at the individual offer-acceptance level was retrieved; Glassdoor decompositions are vendor relative-importance analyses of review sub-ratings, not causal.
- Glassdoor percentages could not be verified on the primary page (403).

## 3. Pay: level vs market and vs previous pay; diminishing returns; pay transparency

### Takeaway
Well-being rises roughly linearly in log(income) for most people with no plateau up to high incomes (Killingsworth, Kahneman & Mellers, PNAS 2023), which supports a log/ratio functional form: score pay by log(offered/reference) where reference = candidate's current pay or market median. Pay-transparency laws raise posted pay (+3.6% Colorado) and posting rates (+30pp), and the EU directive (deadline 7 June 2026) makes pay ranges near-universal in the EU, so missing pay is increasingly an informative (negative) signal.

### Cited Findings
- Killingsworth, Kahneman & Mellers (PNAS 2023, "Income and emotional well-being: A conflict resolved", US experience-sampling): for most people happiness rises linearly with log(income) with no plateau; for the happiest group it accelerates above ~$100k; a plateau (~$100k) exists only for the least-happy minority (~20%) — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10068796/); [ADS abstract](https://ui.adsabs.harvard.edu/abs/2023PNAS..12008661K); group share from [IZA DP 17841](https://docs.iza.org/dp17841.pdf) (secondary)
- Earlier Kahneman & Deaton (2010) found emotional well-being flattening around $60k–$90k (often quoted $75k); the 2023 paper reconciles this — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10068796/)
- Arnold, Quach & Taska (NBER WP 34480, 2025): Colorado's 2021 pay-transparency-in-postings law increased posted salaries by 3.6% and actual earned salaries by ~1.3%; no effect on number of postings; employers did not widen ranges; transparency laws raise the share of postings with ranges by ~30 percentage points, though many high-paying listings still omit pay. Earlier draft versions reported larger posted-pay effects (~7.3%) — [NBER](https://www.nber.org/papers/w34480); [manuscript](https://darnold199.github.io/aq_manuscript.pdf)
- Contrasting estimate: Feng (2023) finds Colorado raised posted wages ~5% but no significant effect on realized wages — [IZA conference paper](https://conference.iza.org/DATA_2023/feng_k34013.pdf)
- EU Pay Transparency Directive (2023/970): applicants have the right to the initial pay or pay range before interview; employers cannot ask about pay history; transposition deadline 7 June 2026. Some states (Italy, Ireland, Lithuania, Latvia drafts) require the range in the job advert itself; the Dutch draft only requires pre-interview disclosure. Greece, Italy, Lithuania, Malta, Slovakia finalised around the deadline; Ireland signalled it would miss it; Belgium partial — [Ogletree](https://ogletree.com/insights-resources/blog-posts/pay-transparency-compliance-underway-across-the-eu/); [Littler](https://www.littler.com/news-analysis/asap/eu-pay-transparency-directive-early-transposition-trends-watch); [Forvis Mazars](https://www.forvismazars.com/pl/en/insights/articles-opinions/pay-transparency-in-the-eu) (law-firm commentary, 2026)

### Inferences
- Functional form: pay_score = clamp(a + b·ln(offer_mid / reference_pay)), with reference = max(current pay, market median for role/location). A +10% raise ≈ ln(1.1)=0.095; +30% ≈ 0.26; doubling ≈ 0.69 — concave, consistent with log utility. Add a loss-aversion kink: below-reference offers penalised more steeply (e.g., slope ×2) — this is a modelling assumption from reference-dependent preferences, not directly tested here.
- Use range midpoint (or lower-third, since Colorado evidence shows realized pay rises far less than posted) as the expected offer; a very wide range lowers confidence.
- In jurisdictions where ranges are mandatory (Colorado, NY, CA, WA, EU states post-transposition), absence of pay is a compliance/quality red flag; elsewhere absence should be neutral-to-mildly-negative.

### Gaps
- No direct evidence retrieved on offer-acceptance elasticity relative to previous pay (e.g., typical job-switch raise demanded). Atlanta Fed Wage Growth Tracker switcher premia not retrieved.
- Kahneman–Mellers thresholds/group shares from secondary summaries; confirm against PNAS DOI 10.1073/pnas.2208661120.

## 4. Learning and growth: retention and later earnings; optimal stretch

### Takeaway
Career-growth deficits are the #1 stated reason for quitting (Work Institute, every year since 2010), and LinkedIn reports learning opportunity is the top retention lever employers use. Early-career employer quality has lasting effects: starting at a larger firm raises lifetime earnings even after leaving (Arellano-Bover, JOLE 2024). Robust quantitative evidence on an "optimal" number of new skills (stretch) was not found.

### Cited Findings
- LinkedIn Workplace Learning Report 2024 (vendor): companies with strong learning cultures show higher retention, more internal mobility, and healthier management pipelines; 90% of organisations are concerned about retention and providing learning opportunities is the No. 1 retention strategy; 33% of employers have internal mobility programs but only 1 in 5 employees is confident about making an internal move (UK 27%) — [LinkedIn WLR 2024](https://learning.linkedin.com/resources/workplace-learning-report-2024); [UK edition](https://learning.linkedin.com/resources/workplace-learning-report-uk-2024)
- A "+57% retention" figure for strong learning cultures appears in a copy of the 2024 PDF, but what it compares is unclear — [third-party-hosted PDF](https://stratoplan-school.com/wp-content/uploads/2024/11/LinkedIn-Workplace-Learning-Report-2024.pdf) (unverified; do not cite as precise)
- Arellano-Bover, "Career Consequences of Firm Heterogeneity for Young Workers: First Job and Firm Size" (Journal of Labor Economics 2024, Spanish social security data, IV design using labour-demand mix at entry): starting at a large firm leads to higher lifetime earnings that persist after moving on, via higher daily wages and more employment; mechanisms include better skill development/training and better subsequent job-search outcomes — [IZA DP 12969](https://docs.iza.org/dp12969.pdf); [IZA newsroom](https://newsroom.iza.org/en/archive/research/does-it-pay-to-start-your-career-with-a-job-at-a-larger-firm); [RePEc/JOLE](https://econpapers.repec.org/RePEc:ucp:jlabec:doi:10.1086/723500)
- Glassdoor/finance evidence: improvements in employee ratings of Career Opportunities (and senior management) are what drive the link between rating changes and future stock returns — [Green et al., JFE 2019 (Georgetown PDF)](https://faculty.georgetown.edu/qw50/EmpReviews.pdf)
- Large transitions into higher-skill jobs can boost wage growth but are rare (dissertation chapter) — [Duke](https://dukespace.lib.duke.edu/server/api/core/bitstreams/fd2429eb-c14c-4ad2-b536-3a39bb407eda/content) (working material)
- NBER work uses skill distance between occupations to identify feasible transitions to higher-wage work; bachelor's degree holders have much better access to occupations whose skill requirements exceed their observed skills — [NBER w26844](https://www.nber.org/system/files/working_papers/w26844/w26844.pdf) (working paper)

### Inferences
- For early-career candidates, weight employer quality/size and learning signals higher (they compound); for senior candidates, weight pay and scope higher.
- Stretch heuristic (assumption, not evidence-based): treat a job requiring 1–3 new core skills on top of a strong overlap (~60–80% skill match) as the growth "sweet spot"; very high overlap = little growth, very low overlap = low hire probability and higher failure risk. This should be tuned on outcome data, not presented as research-backed.

### Gaps
- No rigorous source found for an "optimal stretch" number of new skills. McKinsey Global Institute "Human capital at work" (2022) on the value of experience and "bold moves" is relevant but the page timed out — [MGI](https://www.mckinsey.com/mgi/media-center/if-you-want-to-grow-in-your-career) — figures not verified.
- No numeric effect size retrieved from Arellano-Bover (full text paywalled).

## 5. Company stability and startup risk

### Takeaway
VC-backed startup risk is high and rose in 2023–2025: Carta counted 966 shutdowns in 2024 (+25.6% vs 769 in 2023), and only ~13–17% of 2022 seed cohorts reached Series A within two years vs ~26–31% for 2018. Tech layoffs remained large (layoffs.fyi: ~151k in 2024; ~90k by Sept 2025). For a candidate, stage (pre-seed/seed vs Series B+ vs public) is the strongest observable stability proxy.

### Cited Findings
- Carta (vendor, platform-based): 966 startup shutdowns in 2024 vs 769 in 2023 (+25.6%); Carta's head of insights believes this undercounts. Q1 2024: 254 closures, +58% YoY; Q1'23→Q1'24 closures +102% at seed, +61% Series A, +133% Series B; enterprise SaaS 32% of shutdowns, consumer 11% — [TechCrunch](https://techcrunch.com/2025/01/26/2025-will-likely-be-another-brutal-year-of-failed-startups-data-suggests); [Carta Q1 2024](https://carta.com/data/startup-shutdowns-q1-2024/)
- AngelList: 364 wind-downs in 2024 vs 233 in 2023 (publicly reported only, underestimate); layoffs.fyi tracked 85 tech shutdowns in 2024, 109 in 2023, 58 in 2022 — [TechCrunch](https://techcrunch.com/2025/01/26/2025-will-likely-be-another-brutal-year-of-failed-startups-data-suggests)
- Carta seed→Series A graduation within 2 years: Q1 2018 cohort 30.6% (priced seed Q2 2018: 25.9%; 37% within 3 years); 2022 cohorts ~13–17% (Q1 2022: 15.4%); 2022 cohorts still maturing; 2024 cohorts showing slightly better graduation — [Carta](https://carta.com/data/linkedin-seed-2022-only-24-percent-reach-series-a/); [Carta](https://carta.com/data/linkedin-seed-to-series-a-harder-update/); [Carta](https://carta.com/data/linkedin-seed-2024-graduation-improving-slowly/)
- Tech layoffs (layoffs.fyi via NerdWallet): 2024 ≈151,484 employees at 542 companies; 2025 ≈89,964 at 204 companies as of 26 Sep 2025; Q1 2023 peak of 585 companies in a quarter — [NerdWallet](https://www.nerdwallet.com/article/finance/tech-layoffs?lv=true)
- Crunchbase (different method, US-based tech): ≥127,000 laid off in 2025; >191,000 in 2023 — [Crunchbase tracker](https://news.crunchbase.com/startups/tech-layoffs/)

### Inferences
- Approximate 2-year "survive and raise next round" odds from Carta: seed ≈ 15–30% depending on vintage; so a seed-stage job carries a materially higher chance of the employer failing or doing layoffs within two years than Series B+/public firms. A stability sub-score could be stage-based: pre-seed/seed low, A medium-low, B–C medium, late/public/established high, adjusted by recent layoff events and hiring momentum (number of open postings trend).
- Candidate risk tolerance should modulate the weight (an equity-hungry candidate may accept startup risk).

### Gaps
- Startup Genome "~90% of startups fail" and CB Insights failure-reason data not retrieved in this run.
- Full-year 2025 Carta shutdown count and layoffs.fyi full-year 2025/2026 totals not found.
- No study retrieved validating job-posting volume growth as a predictor of firm health (plausible but unverified).

## 6. Remote/hybrid work and satisfaction/retention

### Takeaway
The strongest causal evidence (Bloom, Han & Liang, Nature 2024 RCT, 1,612 Trip.com employees, China, 2021–22) shows two WFH days per week cut quit rates by one-third with no damage to performance or promotion; flexibility should carry positive value in scoring.

### Cited Findings
- RCT: hybrid (2 days WFH/week) reduced attrition by one-third, increased job satisfaction, and did not damage performance or promotions over up to two years of review — [Nature/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11208135/); [Stanford News](https://news.stanford.edu/stories/2024/06/hybrid-work-is-a-win-win-win-for-companies-workers); [Fortune](https://fortune.com/2024/06/18/stanford-nick-bloom-hybrid-work-cuts-attrition-no-negative-impact-promoted/)
- Conflict of interest: co-author James Liang is Trip.com co-founder/chairman — [NBER version](https://conference.nber.org/conf_papers/f175145/f175145.pdf)

### Inferences
- A one-third reduction in quits is a large effect relative to typical pay elasticities; remote/hybrid should be a meaningful sub-score (e.g., 10–15% of value) and should be matched to the candidate's stated preference (full remote vs hybrid vs onsite), with preference mismatch as a penalty.

### Gaps
- Willingness-to-pay estimates for WFH (e.g., WFH Research/SWAA "~8% of pay") not retrieved in this run.
- Effects for fully remote (vs hybrid) on promotion/learning not covered.

## 7. Employer review site signals (Glassdoor, Kununu): predictive value and access restrictions

### Takeaway
Changes in Glassdoor ratings predicted stock outperformance and earnings surprises (Green et al., JFE 2019), driven by career-opportunities and senior-management ratings, but later work questions robustness. Glassdoor's terms prohibit automated scraping without written consent; no official Kununu API was found — so review data should be optional/user-supplied, not scraped.

### Cited Findings
- Green, Huang, Wen & Zhou (JFE 2019, "Crowdsourced employer reviews and stock returns"): firms with improving Glassdoor ratings significantly outperform firms with declines; effect tied to Career Opportunities and senior management sub-ratings, unrelated to work-life balance; rating changes forecast next-quarter earnings surprises — [Georgetown PDF](https://faculty.georgetown.edu/qw50/EmpReviews.pdf); [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:134:y:2019:i:1:p:236-251); [CFA Institute digest](https://rpc.cfainstitute.org/research/cfa-digest/2020/05/dig-v50-n5-3)
- Becker, Cardazzi & McGurk (2022) argue the rating–return relationship disappears once data issues are addressed for Russell 3000 firms, recommending review text instead — [App State paper](https://economics.appstate.edu/sites/default/files/zachary_mcgurk_-_paper.pdf) (working paper)
- Glassdoor "Best Places to Work"/Top CEO lists show higher raw returns but not statistically significant on raw or risk-adjusted basis — [Penn State](https://pure.psu.edu/en/publications/glassdoor-best-places-to-work-how-do-they-work-for-shareholders/)
- MIT SMR toxic-culture metric (from Glassdoor review text) predicted industry-relative attrition (10.4x compensation) — [MIT SMR](https://sloanreview.mit.edu/article/toxic-culture-is-driving-the-great-resignation/)
- Glassdoor Terms of Use prohibit automated collection (robots, spiders, data mining) and commercial use without prior written consent — [Glassdoor Terms](https://glassdoor.com/about/terms.htm); [ConductAtlas excerpt](https://conductatlas.com/platform/glassdoor/glassdoor-terms-of-use/prohibition-on-scraping-and-commercial-use/) (secondary excerpt)
- Kununu: no official public API found; third-party scraper listings note review pagination beyond page 1 is disallowed in kununu.com robots.txt — [Apify listing](https://apify.com/studio-amba/kununu-scraper) (third-party, unverified)

### Inferences
- Rating level is a noisy proxy; rating trend and the career-opportunities/leadership sub-ratings carry the signal. Small-n ratings need shrinkage toward a prior (e.g., Bayesian average with ~20–50 pseudo-reviews) — modelling assumption.
- Given ToS restrictions, use review data only via licensed APIs, user-provided input, or manual lookup links; design the scorer to work without it (redistribute weight, reduce confidence).

### Gaps
- Kununu's own Terms of Service not retrieved; legal status of scraping in the EU (database rights, GDPR on reviewer data) not researched.
- No peer-reviewed study found linking a company's review rating to an individual new hire's subsequent satisfaction/tenure (the evidence is firm-level).
