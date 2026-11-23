# How job recommenders learn one user's preferences and chances from feedback

Scope: how to add learning from Shortlist / Apply / Skip decisions and application outcomes to a career assistant. Today the assistant ranks jobs with a fixed model, P(interview) × value. Data is small: tens to hundreds of decisions per user.

Source-quality legend: **[P]** = primary source fetched and read in this session. **[S]** = secondary or press source, or a snippet only. **[K]** = a well-known result from the cited paper whose exact wording I could NOT re-read here, because the PDF text could not be extracted. Verify [K] items before quoting them as fact.

---

## Implicit vs explicit feedback: which signals carry how much information

### Takeaway
The best-documented job-domain weighting is XING's RecSys Challenge 2017 utility. It scores click = 1, bookmark = 5, apply/reply = 5 and recruiter interest = 20. A delete with no other signal scores −10. So a deliberate negative action is worth about 10 clicks, and a save or apply about 5 clicks. For a small-data app, map Shortlist ≈ bookmark, Apply ≈ reply and Skip ≈ delete, and treat employer callback as the strongest label. Impressions alone are weak negatives at best.

### Cited Findings
- **RecSys Challenge 2017 (XING) interaction codes:** 0 = impression ("XING showed this item to a user"), 1 = click, 2 = bookmark, 3 = reply or click on the application-form button, 4 = delete ("user deleted the recommendation"), 5 = recruiter interest (a recruiter from the item's company, e.g., clicked the user's profile). — [RecSys Challenge 2017 official page [P]](http://www.recsyschallenge.com/2017)
- **RecSys 2017 scoring ("user success" per user–item pair):**
  - +1 if clicked (repeat clicks on the same item do not add points)
  - +5 if bookmarked or replied
  - +20 if recruiter interest
  - −10 if the only interaction was a delete
  - The sum is multiplied by 2 for premium users.
  - "Item success" adds +50 (paid) or +25 (non-paid) if at least one user had positive success.
  - Maximum per user–item pair is 52 points, i.e. (1 + 5 + 20) × 2.
  - [RecSys Challenge 2017 page [P]](http://www.recsyschallenge.com/2017)
- **RecSys 2017 scale:**
  - 262 teams registered, 103 actively participated and together submitted more than 6,100 offline solutions.
  - 18 teams rolled out recommendations online to more than 900,000 XING users.
  - The task was cold-start: find users interested in, and suitable for, a new posting.
  - The online stage decided the winner.
  - [Abel, Deldjoo, Elahi, Kohlsdorf, RecSys 2017 pp. 372–373, via search snippet [S]](https://recsys.acm.org/recsys17/challenge/); [dblp record](https://dblp.org/rec/conf/recsys/AbelDEK17.html)
- **RecSys 2016 (XING)** used the same family of interaction types (click/bookmark/reply/delete plus impressions), and its winning approaches relied on gradient-boosted models over "preselected" candidate items. I could not extract the paper text, so the feature-importance numbers are not verified. — [arXiv 1612.00959 [S]](https://arxiv.org/pdf/1612.00959); [2016 dataset description](https://github.com/recsyschallenge/2016/blob/master/TrainingDataset.md)
- **LinkedIn JYMBII ("Jobs You May Be Interested In") in production:**
  - The model is a fixed-effect (global) model plus a per-member random-effect model plus a per-job random-effect model.
  - The per-member model uses job-description features (e.g., extracted skills, titles) so it can "better learn which jobs a highly-active member is interested in."
  - The optimized label is the job application.
  - [Incremental Learning for Personalized Recommender Systems (LinkedIn), arXiv 2108.13299 [S, snippet]](https://arxiv.org/pdf/2108.13299)
- **GLMix lift:** Early A/B tests of GLMix trained with Photon ML reportedly improved job applications from job recommendations by **15–30%**. This is a press quote of a LinkedIn engineer and is weakly sourced. The KDD 2016 paper reports a gain in total applications, but I did not retrieve the magnitude. — [eWeek on Photon ML [S]](https://www.eweek.com/database/linkedin-open-sources-spark-based-machine-learning-library/); [GLMix KDD 2016](https://dl.acm.org/ft_gateway.cfm?ftid=1775886&id=2939684)
- **LinkedIn job search:** GLMix with per-query random effects improved offline metrics and production application rates "significantly" over the global model. No number was given in the snippet. — [Saha et al., Generalized Mixed Effect Models for Personalizing Job Search, SIGIR 2017 [S]](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/07/JobSearch_SIGIR.pdf)

### Inferences
- **Suggested starting label weights:** Skip = −10, Shortlist = +5, Apply = +5 (or +8 if Apply after Shortlist is a stronger commitment), Callback/interview = +20, plain view/open = +1, impression only = 0.
  - These come directly from XING's designed utility, not from a fitted model.
  - Use them as sample weights or as ordinal labels in a per-user model.
- **Two models, two labels.** "Would I want it?" (preference) is learned from Shortlist/Apply/Skip. "Would they call me?" (chance) is learned from outcomes. XING kept "recruiter interest" separate from user actions and weighted it 4× an apply, which supports this split. The current chance × value product maps naturally onto it.
- Dwell time had no job-specific quantified evidence in what I retrieved. Treat it as a weak positive only above a threshold, e.g. opening the full description, and do not weight it heavily.

### Gaps
- I found no retrieved numbers on dwell-time informativeness in job recommendation.
- No Indeed, Seek or CareerBuilder paper with per-signal information value was retrieved.
- The GLMix per-member ablation magnitude was not found. The 15–30% figure is press-only.

---

## Critiquing / "not for me because X" reason capture

### Takeaway
Critiquing research (Chen & Pu) supports letting the user state the reason ("too junior", "on-site only") over system-generated compound critiques.
- **Evidence:** user-initiated critiquing reached decision accuracy with less cognitive effort. With system-proposed dynamic critiques, users made more critiques without gaining accuracy.
- **Design implication:** a small, fixed set of one-tap reason chips on Skip, mapped to model attributes, plus an optional free-text field.

### Cited Findings
- **Chen & Pu survey (UMUAI 2012, 22:125–150):** organizes critiquing recommenders into three branches: natural-language critiques, system-suggested critiques, and user-initiated critiques. It covers interface design and critique-generation algorithms. — [Chen & Pu, Critiquing-based recommenders: survey and emerging trends [S]](https://link.springer.com/article/10.1007/s11257-011-9108-6)
- **Chen & Pu AAAI 2006 user study:** compared user-motivated example critiquing with system-proposed dynamic critiquing.
  - The user-motivated approach "achieved decision accuracy with less cognitive effort consumed."
  - In the dynamic-critiquing interface users "made more critiques, but … did not succeed in obtaining higher decision accuracy."
  - [Chen & Pu, Evaluating Critiquing-based Recommender Agents, AAAI 2006 [S]](https://cdn.aaai.org/AAAI/2006/AAAI06-025.pdf)
- **Hybrid critiquing** (user critiques plus system-suggested critiques) scored high on participants' subjective decision measures compared with systems without critiquing. — [Chen & Pu survey/related, via snippet [S]](https://www.researchgate.net/publication/49457818_Interaction_design_guidelines_on_critiquing-based_recommender_systems)
- Conversational recommender systems (critiquing is one branch) are surveyed in Jannach et al., which is useful for UI patterns. — [A Survey on Conversational Recommender Systems, arXiv 2004.00646](https://arxiv.org/pdf/2004.00646)

### Inferences
- **Proposed job-domain reason taxonomy** (my design, not from a source). Keep each reason tied to a concrete attribute so it can update a weight or a hard filter:
  1. Seniority (too junior / too senior)
  2. Role or function mismatch
  3. Location / on-site / remote
  4. Salary too low
  5. Company: dislike, size, or industry
  6. Tech stack / skills mismatch
  7. Visa / language / eligibility
  8. Contract type
  9. Already applied / duplicate
  10. "Looks unlikely to call me back", which is a chance-side signal, not preference
- **Handling reasons:**
  - A hard constraint such as eligibility should become a filter after one or two occurrences.
  - A soft reason should act as a strong pseudo-observation on that attribute's weight. For example, add a Gaussian "observation" pushing the salary-floor or remote weight.
  - A reason-tagged Skip is far more informative than an untagged one, because it says which feature caused the negative.
- **Burden:** make reasons optional, offer at most about 6–8 chips, and pre-select the model's guess (the lowest-scoring factor). This keeps a Skip to one tap. Do not interrupt with questions on every action.

### Gaps
- I found no quantitative evidence on how much reason capture improves ranking in job recommendation specifically.
- No measured completion rates for optional reason prompts were found.
- Session-length reductions for dynamic/compound critiquing (McCarthy, Reilly et al.) were not retrieved.

---

## Preference learning with small data: Bayesian per-user weights, bandits, shrinkage, exploration

### Takeaway
The standard production pattern is LinkedIn's GLMix: a global model plus a per-member correction with a Gaussian prior. This is exactly "shrink toward a population or prior model." For a single user, implement the following:
- logit P(positive | job) = fixed research-based score + xᵀw_user, with w_user ~ N(0, σ²I).
- Fit it by Bayesian (Laplace-approximated) logistic regression.
- Rank by Thompson sampling, i.e. draw w from the posterior.

With σ² small, the app behaves like today's model. Personalization grows automatically as evidence accumulates.

### Cited Findings
- **GLMix structure in production:** global fixed effect plus per-member random effect plus per-job random effect, with the per-member coefficients regularized toward 0 (Gaussian prior). The application is the response being predicted. — [LinkedIn, arXiv 2108.13299 [S]](https://arxiv.org/pdf/2108.13299); [GLMix KDD 2016](https://dl.acm.org/ft_gateway.cfm?ftid=1775886&id=2939684); [GDMix (LinkedIn engineering)](https://www.linkedin.com/blog/engineering/member-customer-experience/gdmix-a-deep-ranking-personalization-framework)
- **Chapelle & Li, "An Empirical Evaluation of Thompson Sampling" (NeurIPS 2011):** Thompson sampling is "highly competitive" with UCB-style methods on simulated and real data, and simple enough to be a standard baseline. — [Abstract [P]](https://papers.nips.cc/paper/2011/hash/e53a0a2978c28872a4505bdb51db06dc-Abstract.html)
- **[K] Chapelle & Li's Algorithm 3** (Thompson sampling with regularized logistic regression and a Laplace/diagonal approximation). Unverified wording:
  - Keep a per-weight mean m_i and precision q_i, starting at m_i = 0 and q_i = λ.
  - After a batch, find w = argmin ½Σ q_i (w_i − m_i)² + Σ_j log(1 + exp(−y_j wᵀx_j)).
  - Then set m_i = w_i and q_i ← q_i + Σ_j x_ij² p_j(1 − p_j), with p_j = σ(wᵀx_j).
  - To act, sample w_i ~ N(m_i, q_i⁻¹).
  - The paper also reports that TS is more robust than UCB when feedback is delayed or batched, which is relevant because job outcomes arrive late.
  - Source: [Chapelle & Li 2011 PDF](https://papers.nips.cc/paper_files/paper/2011/file/e53a0a2978c28872a4505bdb51db06dc-Paper.pdf). The text could not be extracted in this session.
- **[K] LinUCB (Li, Chu, Langford, Schapire, WWW 2010):** contextual bandit with ridge-regression estimates. It scores each item as x_aᵀθ_a + α·sqrt(x_aᵀA_a⁻¹x_a), with A_a = I + Σ x xᵀ. It was evaluated on Yahoo! Front Page news with offline replay. Not fetched in this session.

### Inferences
- **Recommended model for this app:**
  1. **Features x:** about 10–20 interpretable attributes already in the fixed model (seniority gap, salary vs target, remote/location match, skills overlap, company trust, function match, recency). Standardize them.
  2. **Prior:**
     - **Option 1 (offset):** the fixed research score s₀ (as a logit) enters as an offset with coefficient fixed at 1, and w ~ N(0, σ²I).
     - **Option 2 (prior means):** set the prior means to the fixed model's weights, i.e. w ~ N(w_fixed, σ²I). This is the most literal "Bayesian updating of the research model."
     - **σ value:** a σ of about 0.3–0.5 per standardized feature means one standard-deviation change in a feature can shift odds by about e^0.5 ≈ 1.6× only after data supports it. This is a design choice, not a sourced value.
  3. **Update:** Laplace / iteratively reweighted least squares (IRLS) after each session. This is cheap at hundreds of points and can run in the browser or on the server.
  4. **Ranking:** sample w once per page load (Thompson) to get natural exploration. Alternatively use the posterior mean plus a small UCB bonus.
- **How many observations before personalization helps** (rule-of-thumb inference, no sourced threshold):
  - With a Gaussian prior, the posterior is a precision-weighted average. A feature's personal weight dominates its prior once Σ p(1 − p)x² exceeds 1/σ².
  - For σ = 0.5 that is a "Fisher information" of 4. At p ≈ 0.3 (p(1 − p) ≈ 0.21) and |x| ≈ 1, that takes about 20 informative decisions that vary on that feature.
  - Expect visible personalization on 2–4 dominant features after about 30–50 decisions, and on most features after a few hundred.
  - Because shrinkage is automatic, there is no need for a hard "switch on at N" threshold.
- **Filter-bubble control:**
  - Thompson sampling explores in proportion to uncertainty.
  - Also reserve a fixed exploration slot, e.g. 1 in 10 listed jobs drawn from high-uncertainty or high-prior-but-unseen regions, and label it ("A wildcard").
  - Never let learned preference weights hard-filter except for user-stated constraints.
  - Decay old observations, e.g. a 90–180-day half-life, because job-search goals drift.
- **Keep the value and chance models separate:** the user's preferences update value, and outcomes update chance (next section).

### Gaps
- I found no published per-user sample-size threshold for job recommenders. The numbers above are derived from Bayesian arithmetic.
- The Chapelle & Li update equations and the delayed-feedback table could not be re-read verbatim (PDF text extraction failed). Verify them against the PDF.

---

## Reciprocal recommendation and calibrating P(callback) with few, delayed outcomes

### Takeaway
Treat P(callback) as a calibrated probability with a base-rate prior of about 3–5% per application. This is the band Huntr's 2025 data shows for most boards, with 11% at the top (Google Jobs) and 0.35% at the bottom (Dice). Update it with a Beta-Binomial or logit-offset model, not isotonic regression. Isotonic overfits when data is scarce, and Platt's 2-parameter sigmoid is the small-data choice. With only tens of outcomes, recalibrate just an intercept, optionally plus a slope, on top of the research model.

### Cited Findings
- **Huntr 2025 Annual Job Search Trends Report** (Job Tracker, Jan–Dec 2025: 1.78M job entries from more than 57,000 job seekers):
  - **Response rate per application, by source** (598,627 applications): Google Jobs 11.3%, GovernmentJobs 8.7%, Wellfound 6.0%, Glassdoor 5.5%, Handshake 5.1%, Welcome to the Jungle 4.5%, Indeed 4.5%, LinkedIn 3.1%, ZipRecruiter 2.8%, Dice 0.35%.
  - "Response" means the user moved the job to Interview stage or later. It is self-reported.
  - [Huntr 2025 Annual Report [P]](https://huntr.co/research/2025-annual-job-search-trends-report)
  - Secondary coverage cites Google Jobs at 9.3% and LinkedIn at 3.3%. These differ from the 11.3% and 3.1% on the report page, so treat about ±2 percentage points as noise between versions. — [search snippet [S]](https://huntr.co/research/2025-annual-job-search-trends-report)
- **Huntr 2025, tailored vs untailored resumes:** 5.8% vs 3.73% positive outcomes (interview/offer/hire). Samples were 65,088 tailored and more than 1M untailored. — [Huntr 2025 Annual [P]](https://huntr.co/research/2025-annual-job-search-trends-report)
- **Huntr 2025, interview rate by resume length:** 1 page 3.06%, 2 pages 3.24%, 3 pages 2.6%, 4+ pages 2.12%. — [Huntr 2025 Annual [P]](https://huntr.co/research/2025-annual-job-search-trends-report)
- **Huntr 2025, applications vs offers:** about 7% of users with fewer than 10 applications got an offer, about 16% with 11–20, and about 18% with more than 100. About 38% of successful users got an offer within 30 applications. — [Huntr 2025 Annual [P]](https://huntr.co/research/2025-annual-job-search-trends-report)
- **[K] Niculescu-Mizil & Caruana (ICML 2005):** compared Platt scaling with isotonic regression for calibration. Isotonic regression "is more prone to overfitting, and thus performs worse than Platt Scaling, when data is scarce."
  - The often-quoted "under about 1,000 calibration cases, prefer Platt" threshold could not be confirmed verbatim. Treat it as a rule of thumb.
  - [ICML 2005 listing [S]](https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting); [Platt scaling (overview)](https://en.wikipedia.org/wiki/Platt_scaling); [scikit-learn calibration docs](https://scikit-learn.org/0.22/modules/calibration.html)
- **[K] Guo et al. 2017, "On Calibration of Modern Neural Networks":** temperature scaling, a one-parameter version of Platt, is a simple, strong calibrator. Fewer parameters means it is safer with little data. — [arXiv 1706.04599](https://arxiv.org/html/1706.04599)
- **Reciprocal framing:** XING's 2017 challenge explicitly targeted users who are both interested in and suitable for a job. It rewarded recruiter interest (the employer-side signal) at 20 points vs 5 for a user's apply. — [RecSys Challenge 2017 [P]](http://www.recsyschallenge.com/2017)

### Inferences
- **Recommended calibration for tiny data (from the evidence above):**
  - **Stage A (0 to about 20 outcomes): Beta-Binomial on the base rate.**
    - Prior Beta(a, b) with mean equal to the research model's average predicted callback (or about 4% if unknown) and pseudo-count n₀ = a + b ≈ 20–50.
    - After k callbacks in n resolved applications, the posterior mean is (a + k)/(a + b + n).
    - Multiply each job's research P(callback) by the ratio posterior mean / prior mean. This is a per-user intercept shift.
  - **Stage B (about 20–100 outcomes): logit recalibration.**
    - logit p = β₀ + β₁ · logit p_research, with priors β₀ ~ N(0, 0.5²) and β₁ ~ N(1, 0.25²). This is Bayesian Platt scaling shrunk toward "the research model is right."
    - Optionally add 1–3 feature offsets, e.g. seniority gap and source board.
  - **Stage C (hundreds of outcomes):** a full per-user logistic model as in the previous section. Isotonic only if the user has more than about 1,000 outcomes, which is unrealistic for one person.
  - [K] **Platt's original smoothing:** use targets (N₊ + 1)/(N₊ + 2) for positives and 1/(N₋ + 2) for negatives to avoid overconfidence with few examples (Platt 1999). Not re-verified here.
- **Board as a prior feature:** use the source board as a feature in the callback prior, since Huntr shows about a 30× spread from Dice (0.35%) to Google Jobs (11.3%). Selection effects mean this is not causal.
- **Evaluate calibration with Brier score and log-loss** on resolved applications. With fewer than about 50 outcomes, show the callback estimate as a range (the Beta posterior's 80% interval), not a point value.

### Gaps
- I found no peer-reviewed callback-rate figures (e.g., correspondence/audit-study base rates) in this session. Huntr's figures are self-reported tracker data from a self-selected user base.
- No Indeed Hiring Lab callback statistics were retrieved.
- No public paper retrieved here describes how LinkedIn or Indeed calibrate the employer-side probability.

---

## Delayed / censored outcomes: when does "no reply" mean rejection?

### Takeaway
Most employer responses that will ever come arrive within about 2–6 weeks. Huntr's Q1 2025 data shows a median of 6 days, 75% within 15 days and 90% within 38 days. Its full-year 2025 report gives a much longer tail (median 23 days, 90th percentile more than 4 months). Ghosting is common: 61% of job seekers report being ghosted after an interview (Greenhouse 2024), and 53% have ever been ghosted (iHire 2025). So use a survival-style soft label rather than a hard cutoff.

### Cited Findings
- **Huntr Q1 2025:** "The median time from application to interview is 6 days, with 75% hearing back within 15 days, and 90% hearing back within 38 days." — [Huntr Q1 2025 report, via search snippet [S]](https://huntr.co/research/job-search-trends-q1-2025?preview=true)
- **Huntr 2025 Annual:**
  - Median time from application to first interview is 23 days. The 75th percentile is more than 2 months and the 90th more than 4 months.
  - The page also states an average of about 5.6 days. An average below the median is unusual and suggests different subsets or a reporting error, so treat it as suspect.
  - Median time from interview to offer is 12 days.
  - Median time to first offer rose from 57 days (Q1) to 63 (Q2), 67 (Q3) and 83 (Q4).
  - [Huntr 2025 Annual [P]](https://huntr.co/research/2025-annual-job-search-trends-report)
  - The Q1 and annual figures conflict, likely because of different cohorts or definitions.
- **Huntr 2025 survey:** "nearly 90%" of job seekers report no closure after interviews (survey of 1,049 respondents, Dec 2025). — [Huntr 2025 Annual [P, highlights only]](https://huntr.co/research/2025-annual-job-search-trends-report)
- **Greenhouse 2024 State of Job Hunting:**
  - 61% of job seekers have been ghosted after a job interview, up 9 percentage points since April 2024.
  - Ghosting by stage: 24% after the initial recruiter conversation, 23% after a hiring-manager interview, 12% after a take-home assignment, 12% after the final round.
  - Sample is reported as 2,500 workers, or 1,200 US workers in some coverage, which is inconsistent.
  - A 2025 wave reportedly shows 63% [S].
  - [Greenhouse blog [S]](https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report)
- **iHire (Oct 2025, n = 1,024):** 53% have ever been ghosted by an employer. — [iHire [S]](https://www.ihire.com/resourcecenter/employer/pages/53-percent-of-job-seekers-have-been-ghosted-by-a-potential-employer)
- **[K] Chapelle & Li 2011:** Thompson sampling degrades less than UCB under delayed or batched feedback. — [paper](https://papers.nips.cc/paper_files/paper/2011/file/e53a0a2978c28872a4505bdb51db06dc-Paper.pdf)

### Inferences
- **Survival-adjusted soft label (recommended).** Let p be the model's eventual callback probability and F(t) the response-time CDF, i.e. the fraction of eventual responses arriving by day t. For an application with no reply after t days:
  - P(eventual callback | silent at t) = p·(1 − F(t)) / (1 − p·F(t)).
  - Use this as a fractional label, or equivalently use a censored likelihood: a silent-at-t application contributes log(1 − p·F(t)) instead of log(1 − p).
  - This is the standard delayed-feedback treatment, in the spirit of Chapelle 2014 "Modeling delayed feedback in display advertising". That paper was not fetched here [K].
- **Parametrize F from Huntr Q1 2025** (log-normal fit through median 6 d, 75th percentile 15 d, 90th percentile 38 d): F(15 d) ≈ 0.75, F(38 d) ≈ 0.90. With p = 5%, an application silent for 38 days keeps about 0.5% residual callback probability. In practice that is a rejection.
- **Practical conventions:**
  - Mark "probably ghosted" at 21 days and "closed / no response" at 45 days, but keep the soft label so late callbacks still count.
  - Let the user override.
  - Re-fit F to the user's own resolved applications once there are about 15 or more responses.
  - Because the annual report shows a longer tail, consider a 60-day close for senior or government roles. That is an inference, not a sourced figure.
- **Do not wait for outcomes to learn preferences.** Shortlist/Apply/Skip are immediate. Only the chance model has to cope with delay.

### Gaps
- I found no peer-reviewed data on the employer response-time distribution. Huntr is self-reported tracker data, and the Q1 and annual figures conflict.
- Indeed Hiring Lab response-time figures were not found.
- Chapelle (2014) delayed-feedback model details were not retrieved.

---

## Position bias / exposure bias when learning from what was shown

### Takeaway
Clicks and decisions on ranked lists are biased by position. Treating them as unbiased labels yields sub-optimal rankers. The fix is inverse-propensity weighting (Joachims, Swaminathan & Schnabel, WSDM 2017 Best Paper), with propensities estimated by small randomized interventions. In a small app, the bigger problem is exposure bias: the model only learns about jobs it chose to show. So log every impression with its rank and keep some randomized exploration.

### Cited Findings
- **Position bias:** directly using click data as a training signal in learning-to-rank yields sub-optimal results.
  - The authors propose a counterfactual inverse-propensity-weighted empirical-risk-minimization framework (Propensity SVM-Rank), with click models acting as propensity estimators.
  - It works even when queries do not repeat, and is robust to noise and propensity misspecification.
  - It won the WSDM 2017 Best Paper award.
  - [Joachims, Swaminathan, Schnabel, Unbiased Learning-to-Rank with Biased Feedback [S]](https://www.cs.cornell.edu/~schnabts/downloads/joachims2017ltr.pdf); [IJCAI 2018 version](https://www.ijcai.org/proceedings/2018/738); [arXiv 1608.04468](https://ar5iv.labs.arxiv.org/html/1608.04468)
- **Propensity estimation through result randomization/intervention** is the standard approach cited by follow-up work. — [Cornell CS7792 lecture notes [S]](https://www.cs.cornell.edu/courses/cs7792/2020sp/lectures/03-unbiasedLTR.pdf)
- **XING logged impressions** (interaction type 0) separately from clicks and other actions. This is the logging needed for exposure-aware learning. — [RecSys 2017 page [P]](http://www.recsyschallenge.com/2017)

### Inferences
- **Log for every shown job:** shown_at, rank position, page/section (e.g., Shortlist view vs Search), the score and the sampled Thompson weights. Without impressions, a missing action cannot be told apart from never having been seen.
- **Positive labels:** an explicit Shortlist or Apply is far less position-dependent than a click, because the user read the job. Weight explicit actions without IPS.
- **Negatives:** only use "shown but ignored" as a weak negative, about −1, when the job was in the top ~5 and the session lasted long enough. Apply IPS weight 1/P(examined | rank).
- **Propensity curve:** with a single user, estimate P(examined | rank) cheaply by occasionally swapping adjacent positions (randomized pair swaps, the "intervention harvesting" idea). Alternatively, start with a 1/rank curve as a prior (inference, not sourced).
- **Explicit Skip:** treat a Skip as unbiased negative evidence, since the user looked at the job.
- **Exploration:** the exploration slot and Thompson sampling from the small-data section double as exposure-bias mitigation, because they give every region of job space a chance to be shown and labelled.

### Gaps
- I found no job-domain-specific measured position-bias curves.
- The Joachims 2017 propensity-estimation procedure details were not re-read verbatim.
