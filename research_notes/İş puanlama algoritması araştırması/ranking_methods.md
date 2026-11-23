# Decision methods and real-world systems for ranking job opportunities (candidate side)

Scope note: research run of about 17 tool calls (Nov 2026). Several classic papers were reachable only through abstracts and bibliographic records; where a claim rests on a secondary summary, that is flagged. Formulas marked "(standard definition)" are textbook forms of the named method, given for implementation. They are not quoted from the cited page.

## 1. MCDA for job choice: SAW vs WPM vs TOPSIS vs AHP vs MAUT; compensatory vs non-compensatory rules; how people actually choose

### Takeaway
For a candidate-side job score, the defensible structure is **non-compensatory screening first, then a compensatory score inside the surviving set**. People shift to elimination heuristics as the option set grows (Payne 1976), and EBA formalises this (Tversky 1972). Inside the surviving set, a weighted sum (SAW) is the most transparent choice and is immune to the rank reversal that TOPSIS shows when jobs are added or removed. A weighted product (geometric) form is the multiplicative-utility alternative: it penalises a single very weak dimension, which is a property worth having for fit × chance × value.

### Cited Findings
- **Methods compared in the standard reference.** Triantaphyllou's *Multi-Criteria Decision Making Methods: A Comparative Study* (Kluwer, 2000) treats WSM/SAW, WPM, AHP, ELECTRE and TOPSIS, including rank-reversal "ranking abnormalities". His original ranking-reversal study with S.H. Mann dates from 1989 — [Triantaphyllou book index](https://www.csc.lsu.edu/trianta/Books/DecisionMaking1/Sbj_Indx.htm); [Preface](https://www.csc.lsu.edu/trianta/Books/DecisionMaking1/Preface1.htm)
- **Formulas (standard definitions)** for job j, criterion i, normalised rating r_ij ∈ [0,1] and weights w_i with Σw_i = 1:
  - SAW/WSM: S_j = Σ_i w_i · r_ij
  - WPM (weighted geometric mean): P_j = Π_i r_ij^{w_i}. A zero on any criterion gives P_j = 0, so the method is partially non-compensatory.
  - TOPSIS: closeness C_j = d_j⁻ / (d_j⁺ + d_j⁻), where d⁺ and d⁻ are distances to the ideal and anti-ideal points of the *current* alternative set.
  - AHP derives the weights w_i from pairwise comparison matrices (principal eigenvector) and then aggregates additively.
- **TOPSIS shows rank reversal.** Adding or removing alternatives can change the relative order of the existing ones, because the distance metric is tied to the set's ideal and anti-ideal points. A 2024 *Informatica* paper studies fixes through distance metrics and normalisation — [Informatica 2024](https://informatica.vu.lt/journal/INFORMATICA/article/1356/text); [Wikipedia: Rank reversals in decision-making](https://wikipedia.com/wiki/Rank_reversals_in_decision-making)
- **SAW is not affected by this reversal.** A 2023 *Annals of OR* paper says TOPSIS suffers rank reversal "which does not affect SAW approaches (García-Cascales & Lamata, 2012)" — [Annals of Operations Research 2023 (White Rose eprint)](https://eprints.whiterose.ac.uk/199927/1/s10479-023-05339-w.pdf)
- **Sources disagree on the WPM.** One Wikipedia page says it does not show add/remove-alternative reversals because of its multiplicative formula, though its rankings can differ from the WSM's. Another lists it among methods that do show the paradox. The status depends on how reversal is defined. — [Wikipedia: Rank reversals](https://wikipedia.com/wiki/Rank_reversals_in_decision-making); [Wikipedia: Decision-making paradox](https://EN.wikipedia.com/wiki/Decision-making_paradox)
- **MAUT (Keeney & Raiffa, *Decisions with Multiple Objectives*, Wiley 1976; CUP reprint 1993).** Keeney (1974, *Operations Research* 22(1):22–34) gives sufficient conditions for a multiattribute utility to be multiplicative or additive. The additive form needs **additive independence**, which is stronger than mutual utility independence. Under mutual utility independence the multiplicative form holds: 1 + k·U(x) = Π_i (1 + k·k_i·u_i(x_i)), with scaling constants k_i ∈ (0,1). The additive form is the special case Σk_i = 1 — [Keeney 1974, IDEAS/RePEc](https://ideas.repec.org/a/inm/oropre/v22y1974i1p22-34.html); [Purdue MAUT slides](https://engineering.purdue.edu/DELP/education/decision_making_slides/Module_07___Multi_attribute_Utility_Theory.pdf); [Wikipedia: Multi-attribute utility](https://www.Wikipedia.org/wiki/Multi-attribute_utility)
- **Elimination-by-aspects (Tversky 1972).** *Psychological Review* 79(4):281–299, doi 10.1037/h0032955. The decision maker treats options as bundles of aspects, picks one aspect at a time (probabilistically, in proportion to its weight) and eliminates every option lacking it, until one option remains. Tversky argued it is easy to apply and easy to justify. Unlike satisficing, it works when all options are available at once — [BehavioralEconomics.com: EBA](https://www.behavioraleconomics.com/resources/mini-encyclopedia-of-be/elimination-by-aspects/); [SciSpace record](https://scispace.com/papers/elimination-by-aspects-a-theory-of-choice-2tjr9ohr69)
- **People switch to non-compensatory rules as alternatives grow.** Payne (1976), *Organizational Behavior and Human Performance* 16(2):366–387, varied the number of alternatives and dimensions in apartment choices. As complexity rose, subjects used strategies "designed to eliminate some of the available alternatives as quickly as possible". This is the standard citation for more simplifying heuristics when there are more options — [Duke Scholars record](https://scholars.duke.edu/publication/792478); [Cambridge: Contingencies in decision making](https://www.cambridge.org/core/books/adaptive-decision-maker/contingencies-in-decision-making/6979CA4CF3D120401BB42CC0879515A7)
- **Adaptive decision maker (Payne, Bettman & Johnson, CUP 1993).** Strategy selection trades decision accuracy against cognitive effort. Their 1988 simulation found heuristics that "approximate the accuracy of normative procedures while saving substantial effort", and process-tracing showed people adapt to how the alternatives are structured and to time pressure — [Cambridge: Deciding how to decide](https://www.cambridge.org/core/books/adaptive-decision-maker/deciding-how-to-decide-an-effortaccuracy-framework/F7CCC202F7F6A3369C9352DDE0F4A8C3); [Duke Scholars 1988 article](https://scholars.duke.edu/publication/1057197)

### Inferences
- A two-stage pipeline maps directly onto Payne's (1976) observed behaviour and onto the EBA/conjunctive literature:
  1. **Hard constraints** (work authorisation, location/remote, language, seniority floor, salary floor, excluded employers) act as conjunctive filters: pass or fail, never scored.
  2. **Soft scoring** of the survivors.
  The app does the effortful compensatory part the user would otherwise skip, which is the effort–accuracy trade-off resolved in the user's favour.
- Avoid TOPSIS for a feed that changes daily. Each scrape adds or removes jobs, which moves the ideal and anti-ideal points and can reorder jobs whose own data has not changed. SAW and WPM scores depend only on the job's own attributes, so they stay stable.
- WPM / geometric mean vs SAW:
  - Use a **geometric form for the top-level combination** of fit, chance and value. A job with zero chance or zero value should not be rescued by a high score elsewhere, which matches the expected-utility logic in section 2.
  - Use **SAW within each sub-score**, for example the fit sub-components skills, title and seniority, where trade-offs are acceptable.
- A "soft" constraint can be modelled as a multiplicative penalty factor in [0,1] rather than a binary filter. One example is salary slightly under target, giving factor = 0.7.

### Gaps
- No full text was retrieved for Triantaphyllou's head-to-head WSM/WPM/AHP/TOPSIS accuracy experiments, so there are no quantitative comparison figures.
- No study was found that applies MCDA specifically to job-offer choice by individual job seekers. The cited evidence is general decision research, and the apartment task in Payne 1976 is the closest analogue.

## 2. Expected value / expected utility framing: McCall, sequential search, portfolio (simultaneous) search; P(offer) × utility vs other forms

### Takeaway
The economics literature supports ranking by **expected surplus**: success probability × (utility − reservation utility), not utility alone and not probability alone. The strongest and most directly applicable source is a 2026 field-experimental paper with the French public employment service (Bied, Caillou, Crépon, Gaillac, Pérennes & Sebag). It derives the welfare-optimal ranking index Γ(p,U) and shows in RCTs that combining "job I like" with "job I can get" beats either alone. For choosing a *set* of applications, Chade & Smith (2006) show that the optimal portfolio is not simply the top-k by expected value.

### Cited Findings
- **McCall (1970)**, "Economics of Information and Job Search", *QJE* 84(1):113–126. Optimal-stopping job search: the searcher accepts any offer at or above a **reservation wage** and rejects the rest. Extensions add discounting, job duration and Bayesian learning of the wage distribution — [Wikipedia: Search theory](https://Www.Wikipedia.org/wiki/Search_theory); [McCall 1970 PDF](https://christine-braun.github.io/Papers/McCall1970.pdf); [RAND memo version](https://www.rand.org/pubs/research_memoranda/RM5745.html)
- **Chade & Smith (2006)**, "Simultaneous Search", *Econometrica* 74(5):1293–1307, doi 10.1111/j.1468-0262.2006.00705.x. A static portfolio problem: choose several costly options at once (e.g. college applications), each succeeding with some probability, of which only the best success is used.
  - The objective is submodular and NP-hard in general.
  - For the binary-outcome case, a **marginal improvement algorithm** (greedy) finds the optimal set in a quadratic number of steps.
  - Optimal sets are less risky than Weitzman's (1979) sequential solution but riskier than picking the best single options.
  - The optimal set can contain **gaps**: some middle-ranked options are skipped.
  
  Sources: [Econometric Society page](https://econometricsociety.org/publications/econometrica/2006/09/01/simultaneous-search); [Deep Blue PDF](https://deepblue.lib.umich.edu/bitstream/handle/2027.42/75607/j.1468-0262.2006.00705.x.pdf); [Cowles DP 1556](https://cowles.yale.edu/sites/default/files/2022-08/d1556.pdf)
- **Bied, Caillou, Crépon, Gaillac, Pérennes & Sebag (arXiv 2603.21699, 23 Mar 2026)**, "A Job I Like or a Job I Can Get: Designing Job Recommender Systems Using Field Experiments". Two randomized field experiments with the French public employment service, registered with the AEA RCT Registry. Data covers more than 1.1M search sessions, 516,776 vacancies and 75,744 observed hires in the Rhône-Alpes region — [arXiv abstract](https://arxiv.org/abs/2603.21699); [arXiv HTML](https://arxiv.org/html/2603.21699)
  - **Model.** A seeker applies when the surplus is positive:
    - Δ(p,U) = U − U₀*(p)
    - reservation utility U₀*(p) = rV₀ − R̄ + (k̄ + R̄)/p, with R̄ = (r+q)R and k̄ = (r+q)k
    - k = application cost, R = rejection cost, q = job separation rate, r = discount rate
    - The reservation utility *rises as hiring probability p falls*: low-chance jobs must be much better to be worth applying to.
    - Application probability p_a = F(Δ/σ), with F logistic.
  - **Welfare-optimal ranking index (myopic benchmark):**
    - Γ(p,U) = p · σ · log(1 + exp(Δ(p,U)/σ)), a softplus of the surplus multiplied by the hiring probability
    - Equivalently Γ = p · p_a · m(p_a), with m(p_a) = −log(1 − p_a)/p_a
    - For small p_a, Γ ≈ p_h·(1 + p_a/2), where p_h = p·p_a is the unconditional hire probability
    - The authors state that ranking by utility alone, by hiring probability alone, or by observed applications is generically suboptimal.
  - **Hiring-probability estimation.** A content-based bilinear neural score S(X,Y) = Σ_b φ_b(X)ᵀ A_b ψ_b(Y) over blocks for geography, skills and other features, trained with a triplet margin loss on hires. It is then **mapped to a probability by a logistic regression of application success on the score**, which is effectively Platt scaling.
  - **Utility and hiring diverge sharply.** The vacancy with the top utility score ranks about 4,403rd by hiring score. The vacancy with the top hiring score ranks about 2,027th by utility. Median success probability is 0.02 for utility-ranked recommendations against 0.06 for hiring-ranked ones.
  - **Results (qualitative; the exact numbers were not in the portion read).** In Experiment 1, seekers responded better to recommendations combining utility and hiring prospects than to either alone. In Experiment 2, the welfare-approximating algorithm "substantially outperform[ed] existing approaches" and came close to the welfare-optimal benchmark.
- **Competition and congestion lower the effective chance.** Naya, Bied, Caillou, Crépon, Gaillac, Pérennes & Sebag (2021, IZA DATA conference paper "Designing labor market recommender systems") define a competition-adjusted matching probability that depends on how many other seekers receive the same vacancy. It is "substantially lower than the instantaneous matching probability" (per search snippet; the PDF could not be fetched) — [IZA conference paper](https://conference.iza.org/conference_files/DATA_2021/927.pdf)

### Inferences
- A practical, training-free top-level form that follows Bied et al. and Keeney's multiplicative MAUT:
  - **score = P(interview or offer | apply) × max(0, Value − ReservationValue)**, or the smoothed Γ form p·σ·softplus(Δ/σ), which never hits exactly zero.
  - In the heuristic phase, P comes from a chance model (seniority gap, skills overlap, applicant-count or congestion proxy, sponsorship needs) and Value from fit × job value (pay, company, growth).
  - The reservation term could be the user's median-quality job, or an explicit minimum.
- **P × U without a reservation term overweights long-shot dream jobs less than U alone does, but it still ignores application cost.** The U₀*(p) term above shows that cost and rejection cost scale with 1/p. For a seeker spending real effort per tailored application, this argues for a minimum chance threshold or an explicit cost term.
- Chade & Smith imply that the **"apply-to" shortlist should be built greedily**:
  - Add the job that most increases P(at least one good outcome) × value, given the jobs already chosen.
  - The top-k by individual expected value is not the right set, because it ignores correlation and diversification across reach, target and safety.
  - This argues for showing a balanced shortlist (a few reach jobs, mostly target jobs, a few safety jobs), not just a sorted list.

### Gaps
- The exact Experiment 1 and 2 effect sizes in Bied et al. (2026) were in the unread portion of the HTML, from character 100k onward.
- Weitzman's (1979) "Pandora's box" reservation-index rule was not fetched directly; it is referenced only through Chade & Smith.
- No source was found that estimates application-cost parameters (k, R) for white-collar seekers.

## 3. How job platforms rank and match (LinkedIn, Indeed, Eightfold, reciprocal recommenders, RecSys Challenge 2016/2017 XING)

### Takeaway
Production systems are learned response-prediction models (P(apply), P(recruiter positive action)) built on content similarity plus personalisation, not hand-built MCDA. They are explicitly **two-sided**: rank by what the seeker wants *and* what the recruiter is likely to accept. Academic work adds congestion awareness, so that the same few popular jobs are not pushed to everyone. In cold start, content-based similarity between profile and job wins.

### Cited Findings
- **LinkedIn GLMix (Zhang et al., KDD 2016)**, "GLMix: Generalized Linear Mixed Models for Large-Scale Response Prediction".
  - Structure: a global GLM plus per-member and per-job random-effect coefficients, i.e. score = global features·β + member-specific coefficients·x + job-specific coefficients·z, trained with parallel block-coordinate descent.
  - Deployed in LinkedIn's job recommender, where it produced **20–40% more job applications**.
  - Later extended to job search (SIGIR 2017) and combined with GBDT for talent search (2019).
  
  Sources: [AMiner record of GLMix](https://www.aminer.org/pub/57aa28de0a3ac518da989745/glmix-generalized-linear-mixed-models-for-large-scale-response-prediction); [LinkedIn job search SIGIR 2017](https://microsoft.com/en-us/research/wp-content/uploads/2017/07/JobSearch_SIGIR.pdf); [Entity Personalized Talent Search, arXiv 1902.09041](https://arxiv.org/pdf/1902.09041); [LinkedIn slides: Personalized Job Recommendation](https://www.slideshare.net/slideshow/personalized-job-recommendation-system-at-linkedin-practical-challenges-and-lessons-learned/79185642)
- **LinkedIn recruiter side (Feb 12, 2019 engineering blog, "Learning Hiring Preferences").**
  - Model: XGBoost with real-time online-learning "personalisation features" per hiring project, built from recruiter feedback such as messages, archives and skips.
  - Effect: 7 of the top 10 features were online-learning features, with a 49.61% lift in NDCG@1 and about 20% better performance in simulations of past hiring.
  - Two-sided: for passive candidates it boosts members with job-seeking intent signals such as Open Candidates.
  
  Source: [LinkedIn Engineering blog](https://www.linkedin.com/blog/engineering/learning/learning-hiring-preferences-the-ai-behind-linkedin-jobs)
- **LinkedIn's candidate-facing match UI.**
  - "Skills Match" shows "x of y skills match your profile", with explicit (listed) and implicit (inferred) skills — [LinkedIn Help: Skills Match](https://www.linkedin.com/help/linkedin/answer/a793433)
  - "How You Match" (May 2018) is a checklist on education, skills, years of experience and current title. Premium shows rank among applicants (e.g. top percentile) — [LinkedIn blog 2018](https://blog.linkedin.com/2018/may/14/introducing-how-you-match-on-linkedin-jobs)
  - Premium's "Top Applicant" flag marks jobs where the member is more likely to hear back. The algorithm is not published — [LinkedIn Help: job match](https://www.linkedin.com/help/linkedin/answer/a7120158); [LinkedIn Premium Top Applicant](https://premium.linkedin.com/careers/top-applicant)
- **RecSys Challenge 2017 (XING, cold-start job recommendation).**
  - The official site lists Deldjoo, Elahi and Kohlsdorf as winners, where the winner is defined as the top online team — [RecSys Challenge 2017](https://recsys.acm.org/recsys17/challenge/)
  - Volkovs, Yu & Poutanen (Layer6) report that content-based plus neighbour-based models won both the offline and online phases. The sources disagree on the "winner" label — [Volkovs et al. 2017](https://www.cs.toronto.edu/~guangweiyu/pdfs/recsys2017.pdf)
  - Lian et al. (Microsoft/USTC, 5th place) framed the task as binary classification with profile-similarity features (user↔job and user-history-jobs↔job) and a single boosted tree. Their negative-sampling scheme beat treating deleted or unclicked items as negatives — [Lian et al., "Practical lessons for job recommendations in the cold-start scenario"](https://microsoft.com/en-us/research/uploads/prod/2019/07/camrea_ready_paper.pdf)
  - The Politecnico di Milano team used a content-based multi-layer ensemble: 1st offline, 2nd final — [RecSys 2017 search result](https://re.public.polimi.it/handle/11311/1169464)
- **RecSys Challenge 2016 (XING).** One entry used a preselection of offers followed by gradient boosting — [arXiv 1612.00959](https://ar5iv.labs.arxiv.org/html/1612.00959)
- **Congestion-aware reciprocal recommenders.**
  - ReCon (Mashayekhi et al., arXiv 2308.09516, 2023; IEEE Access 2024) adds an optimal-transport term so that popular vacancies are not recommended to too many seekers. It improves congestion metrics while keeping NDCG — [arXiv 2308.09516](https://arxiv.org/pdf/2308.09516)
  - CAROT (Bied et al., 2021) couples optimal transport with a recommender — [CORE PDF](https://core.ac.uk/download/516444212.pdf)
  - A RecSysHR 2025 paper adds losses against congestion and "orphan jobs" — [CEUR RecSysHR2025](https://ceur-ws.org/Vol-4046/RecSysHR2025-paper_6.pdf)
- A 2024 paper proposes a "best-of-both" approach to match prediction and reciprocal recommendation for job search — [arXiv 2409.10992](https://arxiv.org/pdf/2409.10992)

### Inferences
- The platform pattern supports splitting the score into **interest/fit (seeker side)** and **chance (employer side)**. LinkedIn's two sub-models and Bied et al.'s U and p are the same split.
- A candidate-side tool cannot see applicant counts as LinkedIn does, but it can use crude congestion proxies such as posting age, "100+ applicants" text, or brand popularity to discount P(callback). This follows the competition-adjusted probability idea.
- In cold start, the RecSys 2017 evidence suggests content similarity between the profile and the job text (skills, title, seniority) is the right first-phase signal.
- GLMix's per-user random effects anticipate the calibration phase: start with global heuristic weights, then learn per-user deviations once the user has outcomes.

### Gaps
- **Indeed and Eightfold:** no primary technical sources were retrieved in this run (budget limit). Their matching algorithms are not documented here.
- The full GLMix paper's equations and offline metrics were not opened; the 20–40% figure comes from the abstract.

## 4. Calibration: from heuristic scores to probabilities; uncertainty; avoiding score compression

### Takeaway
- **Start:** use a monotone heuristic score.
- **Once outcome labels exist** (applied → interview → offer), fit **Platt scaling** P(y=1|s) = 1/(1 + exp(A·s + B)), a 2-parameter logistic. It is appropriate for small samples, and it is exactly what Bied et al. used to map their match score to hiring probability.
- **Switch to isotonic regression** only once data is plentiful.
- **Compression:** fix it by displaying within-pool percentile ranks rather than raw scores.

### Cited Findings
- **Platt scaling:** fit P(y=1 | s) = 1 / (1 + exp(A·s + B)) by maximum likelihood on a held-out set — [Wikipedia: Platt scaling](https://en.wikipedia.org/wiki/Platt_scaling)
- **Niculescu-Mizil & Caruana (ICML 2005)**, "Predicting Good Probabilities with Supervised Learning", pp. 625–632.
  - Max-margin methods such as boosted trees push predicted probabilities away from 0 and 1; Naive Bayes pushes them toward 0 and 1.
  - Both distortions are corrected by Platt scaling or isotonic regression.
  - The paper examines how much calibration data each method needs.
  
  Source: [mlanthology record](https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting)
- **Isotonic vs sigmoid by data size.** Isotonic regression (non-parametric, monotone step function) beats Platt when enough data is available — [Wikipedia: Platt scaling](https://en.wikipedia.org/wiki/Platt_scaling). The scikit-learn docs say sigmoid calibration is preferable when the calibration curve is sigmoid-shaped and calibration data is limited — [scikit-learn: Probability calibration](https://scikit-learn.org/0.22/modules/calibration.html)
- **A logistic map from score to success, applied in a job market.** Bied et al. (2026) map their neural match score to a hiring probability by logistic regression of application success on the score — [arXiv 2603.21699](https://arxiv.org/html/2603.21699)
- **Modern neural networks are often miscalibrated.** Temperature scaling, a one-parameter Platt variant, is a strong baseline — [Guo et al. 2017, arXiv 1706.04599](https://arxiv.org/html/1706.04599)
- **Percentile display.** LinkedIn Premium presents match as rank among applicants (e.g. "top percentile") rather than as a raw score — [LinkedIn blog 2018](https://blog.linkedin.com/2018/may/14/introducing-how-you-match-on-linkedin-jobs)

### Inferences
- **Staged calibration plan:**
  1. **Phase 0, no labels.** Keep the heuristic score; do not label it a probability. Show the percentile within the user's current pool and a qualitative band.
  2. **Phase 1, about 20–50 applications with outcomes.** Fit a 2-parameter Platt map from the score to P(callback or interview). Use a hierarchical or global prior if possible, e.g. a population-level A and B with per-user shrinkage in the GLMix style. Response rates in job search are low (Bied et al.'s median p is 0.02–0.06), so positives will be scarce and the logistic form's 2 parameters are the right capacity.
  3. **Phase 2, hundreds of labelled outcomes per segment.** Consider isotonic regression.
  4. **Chained probabilities:** P(offer) = P(interview|apply) × P(offer|interview). Calibrate each stage separately, since the later stages have very few labels.
- **Score compression.**
  - The cause: a SAW over many 0–1 sub-scores regresses toward the mean, so most jobs land at 55–75.
  - Remedies:
    - rank-transform into a percentile within the user's active pool;
    - a geometric (WPM) top-level combination, which spreads the low tail;
    - apply a z-score plus logistic stretch to the composite.
  - Percentiles are stable to monotone re-weighting and easy to read, but they are relative: a pool of bad jobs still produces a "top 10%". So show the absolute calibrated band alongside the percentile.
- **Uncertainty.** Present the chance as a range or band (e.g. "low / medium / high chance") until calibration exists. After calibration, show the probability with the sample-size caveat.

### Gaps
- No specific study was found on score compression in job-matching UIs, or on user comprehension of percentile vs absolute match scores. The remedies above are inferences.
- The exact data-size thresholds from Niculescu-Mizil & Caruana (where isotonic starts to beat Platt) were not retrieved from the full text.

## 5. Practical guidance on weights: equal vs elicited weights; sensitivity analysis

### Takeaway
Dawes (1979) is the anchor result: **unit (equal) weights on standardized, correctly signed predictors are robust** and often match or beat optimized weights out of sample, and beat intuitive judgment. For a heuristic job score with no training data, the defensible default is:
1. Standardize each criterion.
2. Use equal or near-equal weights within each block.
3. Allow user adjustment of only a few coarse weights.
4. Run a sensitivity check to make sure top-k rankings are not knife-edge.

### Cited Findings
- **Dawes (1979)**, "The Robust Beauty of Improper Linear Models in Decision Making", *American Psychologist* 34(7):571–582, doi 10.1037/0003-066X.34.7.571.
  - "Improper" models have non-optimized weights, such as unit weights. Unit weighting is "quite robust", and improper models still beat clinical (intuitive) judgment, building on Meehl (1954).
  - Example: equally weighting standardized GRE, GPA and a selectivity index gave a composite correlating .48 with later graduate performance (criterion per the paper).
  
  Sources: [CMU-hosted PDF](https://www.cmu.edu/dietrich/sds/docs/dawes/the-robust-beauty-of-improper-linear-models-in-decision-making.pdf); [PhilPapers record](https://www.philpapers.org/rec/DAWTRB)
- Equal-weight formulas are often superior because "they are not affected by accidents of sampling" (secondary summary of the Dawes/Kahneman line) — [Wikipedia: Unit-weighted regression](https://en.wikipedia.com/wiki/Unit-weighted_regression); [Wikipedia: Proper linear model](https://en.wikipedia.org/wiki/Proper_linear_model)
- **AHP elicits weights by pairwise comparison**, and MAUT elicits scaling constants k_i via trade-off and lottery questions (Keeney & Raiffa 1976). Both are more effortful than unit weights — [Purdue MAUT slides](https://engineering.purdue.edu/DELP/education/decision_making_slides/Module_07___Multi_attribute_Utility_Theory.pdf); [Triantaphyllou book](https://www.csc.lsu.edu/trianta/Books/DecisionMaking1/Preface1.htm)

### Inferences
- **Weight scheme for v1:**
  - Equal weights inside fit (skills, title, seniority, domain) and inside value (pay vs target, company, growth or remote).
  - At the top level, a multiplicative combination of chance and value, so no top-level weights are needed beyond an exponent such as chance^α × value^(1−α), with α ≈ 0.5 as the Dawes-style "equal" default.
  - Expose α to the user as a single "ambition vs safety" slider rather than eliciting many weights.
- **Sensitivity analysis (cheap, implementable).**
  - Perturb each weight by ±20–50%, or sample weights from a Dirichlet around the defaults, and recompute ranks.
  - Report, per job, the fraction of perturbations in which it stays in the top-k ("rank stability").
  - Jobs that are top-k under most weightings are robust picks; jobs whose rank depends on a particular weighting can be flagged as such.
- **Once outcome data exists,** fit weights by logistic regression on callback (proper model). Shrink toward the equal-weight prior (ridge toward unit weights) to keep Dawes-style robustness with small samples.

### Gaps
- No job-search-specific test of unit vs elicited weights was found.
- The full Dawes paper's cross-validation tables were not extracted; only the .48 example is cited.
