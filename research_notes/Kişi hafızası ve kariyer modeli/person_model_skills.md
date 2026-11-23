# User Modeling of a Single Job Seeker: Representation, Skill Inference, Proficiency, Evidence Weighting, Decay, Adjacency, Cold Start

Scope note: the notes cover the "person model" for a career assistant that matches one job seeker (Turkey-based, targeting EU/remote software and AI roles) against postings. Research budget was limited to about 16 search/fetch calls. Items marked **[unverified / secondary]** were not confirmed against a primary source in this session. Items marked **[background, not fetched]** are well-known papers cited from prior knowledge. Their URLs are given, but their content was not re-read this session.

---

## Q1. How do production and research job recommenders represent a candidate? Standard node and edge types

### Takeaway
Production systems (LinkedIn) represent a candidate as a member node linked to a **canonical skill taxonomy**. The taxonomy is a DAG of skills with parent/child/sibling edges, aliases and skill groups, and every member-skill and job-skill edge carries a learned importance score. Public taxonomies (ESCO, O*NET) add an **occupation ↔ skill** layer: ESCO marks each skill as *essential* or *optional* for an occupation, and O*NET rates each skill by *importance* (1–5) and *level* (0–7). Research models use heterogeneous graphs over members, jobs, skills, companies and schools.

### Cited Findings
**LinkedIn Skills Graph (production)**
- LinkedIn's skills taxonomy had >39,000 skills across 26 languages, >374,000 aliases, and >200,000 links between skills (2022). The link framework is called "Structured Skills" and maps each skill's relationships to other skills. — [LinkedIn Engineering 2022, "Building LinkedIn's Skills Graph"](https://engineering.linkedin.com/blog/2022/building-linkedin-s-skills-graph-to-power-a-skills-first-world)
- Edge type example: a parent-child hierarchy, e.g. "Supply Chain Automation" → parent "Supply Chain Engineering" → parents "Engineering" and "Manufacturing". A skill can have multiple parents, so the structure is a DAG, not a tree. The taxonomy is curated by human taxonomists plus ML. — [LinkedIn Engineering 2023, "Building and maintaining the skills taxonomy"](https://engineering.linkedin.com/blog/2023/Building-maintaining-the-skills-taxonomy-that-powers-LinkedIns-Skills-Graph)
- The later (2023) extraction post cites ">41,000 skills". Extracted surface forms are normalized to canonical nodes (e.g., "data analytics" and "data analysis" become one node). — [LinkedIn Engineering, "Extracting skills from content to fuel the LinkedIn Skills Graph"](https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content)
- Skill-content edges are typed by relationship. Each content–skill pair is scored for **"mention/valid"**, **"required"** (explicitly required) and **"core"** (essential to the role even if unstated), and these are aggregated into a **skill importance score**. Expansion uses graph edges: **same skill group, parent, child, sibling**. — [LinkedIn Engineering, extraction post](https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content)
- The 2016 LinkedIn Knowledge Graph describes entity taxonomies (titles, skills, companies, schools, locations) with relationships between entities, plus "characteristic features" outside any taxonomy. — [LinkedIn Engineering 2016, "Building the LinkedIn Knowledge Graph"](https://engineering.linkedin.com/blog/2016/10/building-the-linkedin-knowledge-graph)

**ESCO (EU taxonomy, relevant because the target market is EU)**
- ESCO distinguishes **essential** skills/knowledge ("usually required when working in an occupation, independent of the work context or the employer") from **optional** ones ("may be required ... depending on the employer, on the working context or on the country"). — [ESCOpedia: Essential](https://esco.ec.europa.eu/en/escopedia/essential); [ESCOpedia: Optional](https://esco.ec.europa.eu/en/escopedia/optional)
- The ESCO Linked Open Data model defines occupation→skill properties "has essential skill" and "has optional skill" with inverses ("is essential skill for", "is optional skill for"). It also has `relatedEssentialSkill`, whose subject can be an occupation **or a skill**, so skill→skill relations exist. — [ESCO LOD model](https://ec.europa.eu/esco/lod/static/model.html)
- ESCO v1.2 (2024) was a major release focused on green and digital transitions: +35 occupations, +42 skills, +196 knowledge concepts. As a quality fix, the Commission identified and corrected 111 occupations with ≤5 essential skills and 25 occupations with ≥70 linked skills. v1.2.1 (Dec 2025) revised over-dense occupation-skill links. — [ESCO v1.2 major version (MSWG PDF)](https://esco.ec.europa.eu/system/files/2024-04/ESCO%20MSWG_ESCO%20v1.2.%20major%20version.pdf)

**O*NET (US taxonomy)**
- Each skill per occupation carries two ratings: **Importance** on a 1–5 scale and **Level** on a 0–7 scale. Level anchors are item-specific (e.g., Oral Comprehension Level 2 = "understand a television commercial", Level 6 = "lecture on advanced physics"). Scores are standardized to 0–100 via `S = (O − L)/(H − L) × 100`, so Importance 3 maps to 50. Anchor values were revised in October 2024. — [O*NET OnLine Help: Scales, Ratings, and Standardized Scores](https://onetonline.org/help/online/scales); [O*NET Level Scale Anchors (v30.0)](https://www.onetcenter.org/dictionary/30.0/excel/level_scale_anchors.html)
- O*NET's example: lawyers and paralegals both need Speaking, but lawyers need a higher Level. So importance and level are separate dimensions. — [O*NET Help](https://onetonline.org/help/online/scales)

**Research graph models**
- CSAGNN builds a Workplace Heterogeneous Information Network with node types **Member (M), Job (J), Skill (S), Company (C), School (H)**. It uses attention over professional connections to fill in missing profile information. — [arXiv 2401.00010](https://arxiv.org/html/2401.00010)
- DPGNN (Yang et al., RecSys 2022) models **directed, two-perspective** candidate↔job interactions (candidate applies vs recruiter selects) with GCNs, giving each candidate and job two representations: active and passive. — [RUCAIBox/DPGNN GitHub](https://github.com/RUCAIBox/DPGNN); [arXiv 2208.08612](https://arxiv.org/pdf/2208.08612)
- PJFCANN combines co-attention over resume and job text with a GNN over historical successful hires ("recruiter experience"). — [arXiv 2206.09116](https://arxiv.org/pdf/2206.09116)
- **[background, not fetched]** KGAT (Wang et al., KDD 2019) merges the user–item bipartite graph with an item knowledge graph into a "collaborative knowledge graph" and propagates attention over it. It is the generic template for KG-based recommenders. — [arXiv 1905.07854](https://arxiv.org/abs/1905.07854)
- **[background, not fetched]** Text-based person-job fit lineage: PJFNN (Zhu et al. 2018, joint CNN representation of resume and job) — [arXiv 1810.04040](https://arxiv.org/abs/1810.04040); APJFNN (Qin et al., SIGIR 2018, ability-aware attention over job requirements vs candidate experiences) — [arXiv 1812.08947](https://arxiv.org/abs/1812.08947); conSultantBERT (Lavi et al. 2021, fine-tuned Siamese BERT on resume-vacancy pairs) — [arXiv 2109.06501](https://arxiv.org/abs/2109.06501).
- The de Ruijt & Bhulai review covers job recommenders from 2011–2021. Most methods call themselves "hybrid", which "obscures what these methods entail". Click-data availability drives method choice. Fairness is rarely addressed, and many authors wrongly assume dropping the sensitive feature is enough. — [arXiv 2111.13576](https://arxiv.org/abs/2111.13576)

### Inferences
- A minimal standard schema for a single-user person model: **nodes** = Person, Skill (canonical, with aliases), SkillGroup/parent concept, Occupation/Role (ESCO/O*NET code), Evidence item (CV bullet, repo, project, certificate, assessment), Organization (employer, school), Job posting. **Edges** = Person–HAS_SKILL→Skill (attributes: proficiency, confidence, last_used, evidence_ids), Evidence–SUPPORTS→Skill, Skill–PARENT_OF/SIBLING/RELATED→Skill, Occupation–ESSENTIAL/OPTIONAL→Skill, Job–REQUIRES(required/core/mention, importance)→Skill, Person–WORKED_AT/STUDIED_AT→Org.
- Store importance and level separately, following O*NET: a job's requirement for a skill should carry both "how central" and "how advanced". The person side should carry "how well" plus "how sure we are".
- For EU roles, map skills to ESCO URIs. The essential/optional flags give a principled 2-tier weight for scoring missing skills against an occupation.

### Gaps
- No public figure on the number of LinkedIn edge *types* or the member-skill edge attributes beyond the three relationship scores.
- Exact total counts for ESCO v1.2 (skills/occupations) were not confirmed this session. Commonly cited figures (≈3,000 occupations, ≈13,900 skills) are **[unverified]**.
- No source was found for a public system called "JobGraph" specifically.

---

## Q2. How are skills and proficiency inferred from CVs, GitHub and projects? Extraction accuracy

### Takeaway
Span-level skill extraction remains hard. On SkillSpan, supervised models reach only about 56–64 span-F1, and humans agree at κ≈0.70–0.75. In-context LLMs (GPT-4) are far *worse* than supervised models on strict span matching (e.g., 27.8 vs 62.6 F1 on SkillSpan) but much better on relaxed matching. So LLMs find skills but miss exact boundaries. GitHub-based expertise inference is feasible for coarse roles (precision ≈0.88) but weak for fine proficiency levels (F-measure ≤0.56 for novice/intermediate/expert).

### Cited Findings
**CV / posting extraction accuracy**
- SkillSpan (Zhang, Jensen, Sonniks, Plank, NAACL 2022) has 391 postings, 14,538 sentences, 6,576 skill spans and 6,053 knowledge spans. Inter-annotator Fleiss κ was 0.70–0.75 (token and span) in the final rounds, and 0.59–0.62 earlier. — [ar5iv 2204.12811](https://ar5iv.labs.arxiv.org/html/2204.12811); [ACL Anthology](https://aclanthology.org/2022.naacl-main.366)
- SkillSpan test span-F1 (mean of 5 seeds):

  | Model | Skill | Knowledge | Combined |
  |---|---|---|---|
  | BERTbase | 54.34 | 62.43 | 58.16 |
  | JobBERT | 56.11 | 63.88 | 59.73 |
  | JobSpanBERT | 56.64 | 61.06 | 58.72 |

  Domain-adapted models do better, and single-task beat multi-task learning. — [ar5iv 2204.12811](https://ar5iv.labs.arxiv.org/html/2204.12811)
- Nguyen, Zhang, Montariol, Bosselut (2024) benchmarked LLM in-context extraction on 6 datasets against supervised SOTA (ESCOXLM-R). Strict F1 by dataset:

  | Dataset | Supervised SOTA | GPT-3.5 best | GPT-4 best | GPT-3.5 relaxed |
  |---|---|---|---|---|
  | Sayfullina | 92.2 | 39.0 | 40.5 | 57.7 |
  | SkillSpan | 62.6 | 25.0 | 27.8 | 46.2 |
  | Green | 51.2 | 32.0 | 30.6 | 74.0 |
  | Gnehm | 88.4 | 40.9 | 67.8 | 48.2 |
  | Fijo | 42.0 | 44.2 | 48.0 | 82.0 |
  | Kompetencer | 49.8 | 22.4 | 25.3 | 46.3 |

  GPT-4 was run on ≤350 samples per dataset. — [ar5iv 2402.03832](https://ar5iv.labs.arxiv.org/html/2402.03832)
- Error breakdown in the same paper (60 examined errors): ~36% skill-definition mismatch (career terms not annotated as skills), ~20% spurious extractions, ~14% conjoined skills split apart (16–22% of gold spans in 4 of 6 datasets are conjoined, e.g. "Java and Python development"), ~12% over-extended spans, ~8% bad gold labels. LLMs also "corrected" typos in the source, which broke span matching. Demonstrations (few-shot) greatly reduced format failures. — [ar5iv 2402.03832](https://ar5iv.labs.arxiv.org/html/2402.03832)
- A Turkish LLM skill-extraction pipeline reports F1 = 0.64 at the skill-identification stage. This is relevant because the user is Turkey-based and may have Turkish-language CV content. — [arXiv 2601.22885](https://arxiv.org/html/2601.22885) **[snippet only]**
- Skill-XL (an exhaustive sentence-level ESCO annotation benchmark) reports average inter-annotator F1 agreement of only 0.4395 for mapping to fine-grained ESCO skills. Even humans disagree heavily at the taxonomy-linking step. — [arXiv 2604.21525](https://arxiv.org/html/2604.21525) **[snippet only]**

**LinkedIn production pipeline (CV/profile → skills)**
- Stages:
  1. Segment text into sections (section placement is a signal: qualifications > company description).
  2. Tag skills in parallel with a **trie-based exact tagger** and a **semantic two-tower multilingual-BERT tagger** (e.g., "design of iOS application" → "Mobile Development").
  3. **Expand** via the graph (parent/child/sibling, same group).
  4. Score with a **multitask cross-domain model**: a shared contextual text encoder plus an entity encoder using skill/title/industry/location embeddings and co-occurrence features, with per-domain towers (jobs, profiles, feed).
- Results: nearline profile extraction at ~200 edits/s with <100 ms per message. Knowledge distillation cut model size 80% without quality loss. A/B lifts included +0.87% qualified applications and +0.24% predicted confirmed hires for job–member skill matching. — [LinkedIn Engineering, extraction post](https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content)

**GitHub / code-activity inference**
- Montandon, Silva, Valente (MSR 2019), "Identifying Experts in Software Libraries and Frameworks among GitHub Users": supervised classifiers (Random Forest, SVM) did poorly at 3-class novice/intermediate/expert labeling (max F-measure 0.56). Unsupervised clustering produced clusters where 74% (React), 65% (node-mongodb), and 75% (socket.io) of members were experts. — [arXiv 1903.08113](https://arxiv.org/abs/1903.08113v1)
- Montandon & Valente, "Mining the Technical Roles of GitHub Users" (IST 2021): classifiers identifying 6 roles (backend, frontend, full-stack, mobile, data science, DevOps) reached **precision 0.88, AUC 0.89**. — [SBC CTD thesis summary](https://sol.sbc.org.br/index.php/ctd/article/download/20776/20602) **[secondary/snippet; check the IST paper]**
- Dey, Karnauch, Mockus (ICSE 2021), "Representation of Developer Expertise in Open Source Software": builds a **Skill Space** where APIs, developers and projects share a Doc2Vec embedding trained on the APIs (imports/dependencies) of files each developer modified in each commit. It uses World of Code data across 17 languages. The embeddings predict which new APIs/projects developers adopt and whether their PRs get accepted, and were compared with developers' self-reported API expertise. — [arXiv 2005.10176](https://arxiv.org/abs/2005.10176v2); [ICSE 2021 listing](https://2021.icse-conferences.org/details/icse-2021-papers/88/Representation-of-Developer-Expertise-in-Open-Source-Software)
- Dev2vec (2022) is a separate approach that embeds developers' *domain* expertise. — [ar5iv 2207.05132](https://ar5iv.labs.arxiv.org/html/2207.05132) **[title only]**

### Inferences
- For a single-user product, rely on **LLM extraction + taxonomy normalization + user confirmation**, not raw LLM spans. LLM recall is decent (relaxed F1 is high), but boundaries and the "is this a skill?" definition are noisy. A confirm/edit step in the UI corrects the ~36% definition-mismatch errors cheaply.
- Split conjoined mentions ("React/Next.js", "Java and Python") explicitly. The datasets show this is a top error class.
- GitHub proficiency signals: use the **API/import level** (what libraries the user actually touched in commits, following Dey et al.) rather than repo language percentages alone. Treat GitHub-derived *level* estimates as weak (F ≤0.56 in the best published 3-class attempt) and GitHub-derived *role/stack* estimates as fairly strong (precision ≈0.88).
- Reasonable proficiency features per skill (inference, not validated): number of distinct commits/files touching the skill's APIs, number of distinct repos, span of months active, recency of last use, ownership (own repo vs fork), external validation (stars/forks/merged PRs to others' repos).

### Gaps
- No peer-reviewed accuracy figure found for commercial resume parsers (Affinda, Textkernel, Sovren/Textkernel, etc.). Vendor claims were not checked.
- ESCOXLM-R's own paper (Zhang et al., ACL 2023) was not fetched. Its numbers appear here only as the "supervised SOTA" column in Nguyen et al.
- No validated study found that maps GitHub metrics (commits, stars) onto calibrated proficiency levels (e.g., O*NET 0–7 or CEFR-like scales).

---

## Q3. How should evidence from different sources be weighted? Reliability of self-reported skills

### Takeaway
Self-assessed ability correlates only moderately with measured performance (mean r ≈ .29 across 22 meta-analyses). It is more accurate when the skill is **specific** and the task is **objective, familiar and simple**. Self-claims should therefore be a prior that demonstrated and third-party evidence update. Ask about specific, concrete skills, not broad ones.

### Cited Findings
- Zell & Krizan (2014, *Perspectives on Psychological Science*) is a metasynthesis of 22 meta-analyses (academic, intelligence, language, medical, sports, vocational). The mean correlation between ability self-evaluations and performance was **M = .29 (SD = .11)**, with a range of .09–.63. Correlations were stronger for **domain-specific** (vs broad) self-evaluations and for **objective, familiar, low-complexity** tasks. — [APS journal page](https://www.psychologicalscience.org/journals/perspectives/1745691613518075/); [PubMed 26173249](https://pubmed.ncbi.nlm.nih.gov/26173249/); [Iowa State news release](https://www.news.iastate.edu/news/2014/04/02/abilityevaluation)
- LinkedIn treats skill *mentions* differently from *required* and *core* relationships, and weights by section of the document. This is an implicit evidence-type weighting in production. — [LinkedIn Engineering, extraction post](https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content)
- Dey et al. validated code-derived embeddings against **self-reported** API expertise, treating demonstrated code activity and self-report as two separate views. — [arXiv 2005.10176](https://arxiv.org/abs/2005.10176v2)
- LinkedIn ran Skill Assessments as a separate verification signal. — [LinkedIn Engineering 2019, "The building blocks of LinkedIn Skill Assessments"](https://engineering.linkedin.com/blog/2019/the-building-blocks-of-linkedin-skill-assessments) **[title only, not fetched]**

### Inferences
Recommended functional form (design proposal, not an empirically validated weighting):
- Model each skill's proficiency as a **Bayesian belief** (e.g., Beta, or Gaussian on a 0–1 or O*NET-like 0–7 scale). Evidence items update it with source-specific reliability.
- Suggested relative reliability multipliers, ordered by the evidence above: self-claim only (low; r≈.29 implies weak signal) < CV bullet with concrete outcome < project/repo with code touching the skill (demonstrated) < third-party validated work (merged PR to an external repo, employer reference, accepted paper) ≈ proctored assessment or certification with a practical exam. For example, as starting log-likelihood weights: 0.3 / 0.5 / 0.8 / 1.0. **These are inference, to be tuned.**
- Certifications: weight multiple-choice certifications below practical/proctored ones. No source found quantifying certification validity for software skills (see Gaps).
- Per Zell & Krizan, make self-ratings **specific and anchored**: e.g., O*NET-style behavioral anchors ("built and deployed a production FastAPI service") rather than "rate your Python 1–10".

### Gaps
- No peer-reviewed study found that compares the predictive validity of self-claimed vs GitHub-demonstrated vs certified skills for software hiring outcomes.
- No source found on IT certification validity (e.g., AWS/Azure certifications predicting job performance).
- Classic sources not checked this session: Mabe & West (1982) self-evaluation meta-analysis, and Dunning-Kruger replications in programming.

---

## Q4. Skill recency and decay: how fast do unused skills decay? Verify "half-life" claims. Recommended decay functions

### Takeaway
The best quantitative evidence is a 2025 *Psychological Bulletin* meta-analysis of procedural skills: 1,344 effect sizes from 457 reports. Without use, **half of the initial acquisition gains are lost after ≈6.5 months (accuracy), ≈11 months (mixed), ≈13 months (speed)**, at roughly 0.06–0.08 SD per month. The popular "skill half-life ≈5 years, technical ≈2.5 years" figures are **not individual-forgetting data**. They are market-obsolescence claims with weak sourcing: the 5-year figure traces to a 2011 book, and the 2.5-year IBM attribution could not be located in an IBM primary document.

### Cited Findings
**Individual forgetting (learning science)**
- *Psychological Bulletin* 151(6), June 2025, pp. 696–736, "Procedural skill retention and decay: A meta-analytic review", doi:10.1037/bul0000481.
  - It treats the retention interval as a continuous moderator: 1,344 effect sizes, 457 reports.
  - Accuracy degrades **0.08 SD/month** of nonuse. Speed and mixed measures degrade **0.06 SD/month**.
  - Half of acquisition gains are lost after **~6.5 months (accuracy), ~13 months (speed), ~11 months (mixed)**.
  - Candidate moderators: task type, complexity, intermittent performance opportunities, instructions.
  - Open issues the authors flag: separating retention from relearning, and speed–accuracy trade-offs.

  — [NYU IFP summary of bul0000481](https://ifp.nyu.edu/2025/meta-analyses-systematic-reviews/bul0000481/); [PubMed 40455501](https://pubmed.ncbi.nlm.nih.gov/40455501/)
- A Georgia Tech dissertation (Tatel, 2023) rerunning the Arthur et al. approach for procedural skills found acquisition gains were lost **between 1 and 2.5 years**. It argues earlier work relied mostly on short retention intervals. — [Georgia Tech repository](https://repository.gatech.edu/entities/publication/5d7d666f-2ae7-4e3c-9ec9-729ffad16cda)
- Arthur, Bennett, Stanush & McNelly (1998), "Factors That Influence Skill Decay and Retention: A Quantitative Review and Analysis", *Human Performance* 11(1). It found that longer nonpractice intervals mean more decay. — [PDF (gwern mirror)](https://www.gwern.net/doc/psychology/spaced-repetition/1998-arthur.pdf). A **secondary** summary reports d ranging from ≈ −0.1 (<1 day) to ≈ −1.4 (>365 days of nonuse). — [Caplan, EconLib "Forgetting: The Basic Facts"](https://www.econlib.org/archives/2016/01/forgetting_the.html) **[unverified against the paper's tables; the PDF could not be parsed this session]**

**"Skill half-life" market claims**
- The ~5-year half-life figure became commonplace after the 2011 book *A New Culture of Learning* (Douglas Thomas & John Seely Brown). AJG notes the figure varies by skill type. — [AJG, "Half-life of a skill"](https://www.ajg.com/be/news-and-insights/features/half-life-of-a-skill-digital-transformation/)
- SHRM's coverage of an IBM Institute for Business Value executive survey (>5,250 executives, 37 countries) said the half-life of learned skills like critical thinking, collaboration and communication is ~5 years, "even shorter for technical skills". — [SHRM](https://www.shrm.org/topics-tools/news/organizational-employee-development/employers-need-to-broaden-strategies-to-close-skills-gap)
- The "technical skills ≈2.5 years, per IBM" figure appears only in secondary blogs (e.g., 360Learning, Interview Guys). **No IBM primary document stating 2.5 years was found.** — [360Learning](https://360learning.com/blog/half-life-skills/) **[weakly sourced]**
- Emeritus attributes a ~5-year estimate to the 2017 World Economic Forum, "closer to four by late 2021". — [Emeritus](https://emeritus.org/blog/the-half-life-of-skills/) **[secondary]**
- Note: these "half-life" claims are about **market relevance/obsolescence of skill content**, not individual memory decay. These are two different processes and should be modeled separately.

### Inferences
Recommended functional form (design proposal):
- Separate two factors:
  1. **Personal decay** (has the person's ability faded from disuse).
  2. **Market obsolescence** (is the skill itself still demanded). Obsolescence is better measured directly from posting frequency trends than assumed.
- Personal decay: use exponential decay of *evidence weight* since last use, `w(t) = w₀ · 2^(−t / h)`, with a **floor** to reflect relearning savings and retained declarative knowledge: `w(t) = w_floor + (w₀ − w_floor) · 2^(−t/h)`.
  - Evidence-anchored defaults: **h ≈ 12 months** for tool/API-specific procedural skills (between the 6.5-month accuracy and 13-month speed half-lives).
  - Use **h ≈ 24–36 months** for conceptual/foundational skills (e.g., algorithms, statistics). This is an inference, since the meta-analysis covers procedural skills only.
  - Suggested floor `w_floor ≈ 0.3–0.5` of the original weight. This is an inference: the source flags relearning effects but gives no number.
- Note that the meta-analysis reports a near-linear trend in SD units (0.06–0.08 SD/month). Over 0–24 months exponential and linear are close, and exponential with a floor avoids negative values.
- Scale decay by depth of original acquisition (years of use, number of projects). The Arthur line of research finds overlearning and complexity moderate decay. **[moderator directions unverified this session]**

### Gaps
- No empirical study found specifically on decay of *programming-language or framework* proficiency in professional developers.
- Arthur et al. (1998) moderator effect sizes (closed- vs open-loop tasks, physical vs cognitive, natural vs artificial settings) were not verified. The PDF could not be text-extracted in this session.
- The authors of the 2025 *Psychological Bulletin* paper were not captured. The DOI is given above.

---

## Q5. Skill adjacency and transfer: modeling related skills and partial credit

### Takeaway
Three families of methods exist:
1. **Taxonomy edges** (LinkedIn parent/child/sibling and skill groups, ESCO skill-skill relations).
2. **Co-occurrence statistics from postings**, preferably weighted by Revealed Comparative Advantage (RCA) so ubiquitous skills don't dominate.
3. **Learned embeddings**: Sentence-BERT fine-tuned on co-occurrence (SkillMatch), or code-derived embeddings (Dey et al. Skill Space).

Partial credit = similarity(required skill, held skill) × held proficiency.

### Cited Findings
- LinkedIn expands tagged skills via graph structure: same skill group, parent, child, sibling. The scoring model also consumes skill embeddings and co-occurrence rates. — [LinkedIn Engineering, extraction post](https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content)
- Dawson et al., "Skill-driven Recommendations for Job Transition Pathways", used ~8 million Australian job ads.
  - Skill importance within an ad is measured by **RCA**, which down-weights skills that appear everywhere.
  - Two skills are similar when they are simultaneously important for the same set of ads.
  - RCA is argued to be a better importance proxy than raw frequency.

  — [arXiv 2011.11801](https://arxiv.org/pdf/2011.11801); [ar5iv](https://ar5iv.labs.arxiv.org/html/2011.11801) **[snippet only]**
- A related Australian study defines **skill complementarity θ = min(P(A|B), P(B|A))** over RCA-effective skills co-used in the same ad. — [arXiv 2008.12459](https://arxiv.org/pdf/2008.12459) **[snippet only]**
- Liu et al. built a skill co-occurrence network from 65M UK Adzuna postings (2016–2022) with Markov-stability clustering at multiple resolutions. Some technical skills (e.g., cybersecurity) are less interconnected. — [arXiv 2406.03139](https://arxiv.org/abs/2406.03139) **[snippet only]**
- Decorte et al. released **SkillMatch**, a skill-relatedness benchmark built from job ads, and a Sentence-BERT model adapted by self-supervised learning on skill co-occurrence. They report it "greatly surpasses traditional models". — [arXiv 2410.05006](https://arxiv.org/html/2410.05006v1) **[snippet only]**
- Dey et al.'s Skill Space puts APIs, developers and projects in one embedding space, so a developer's proximity to an unfamiliar API/project measures adjacency from actual code. — [arXiv 2005.10176](https://arxiv.org/abs/2005.10176v2)
- The ESCO model includes `relatedEssentialSkill`, which can relate a skill to another skill. — [ESCO LOD model](https://ec.europa.eu/esco/lod/static/model.html)

### Inferences
- Partial-credit formula (proposal): `coverage(req) = max over held skills s of [ sim(req, s) · prof(s) · conf(s) ]`. Here `sim` is a blend: 1.0 for identity/alias, ~0.7–0.8 for a direct child/parent in the taxonomy, otherwise cosine similarity from a SkillMatch-style embedding, clipped below a threshold (e.g., <0.5 counts as 0). The coefficients are illustrative and need calibration.
- Use RCA, not raw co-occurrence, when deriving relatedness from postings. Otherwise generic skills ("communication", "Git") look related to everything.
- Partial credit should be **asymmetric**: knowing a child (PyTorch) implies the parent (deep learning) more strongly than the reverse. The parent→child direction should get lower credit. This follows from the hierarchy semantics, not from a cited result.

### Gaps
- No public numeric similarity thresholds or partial-credit coefficients from LinkedIn or other production systems were found.
- SkillMatch's exact metrics (e.g., AUC values) were not fetched.

---

## Q6. Cold start for a new user: minimum profile and onboarding elicitation

### Takeaway
No job-seeker-specific study on minimal onboarding was found. General recommender research says **which** items you ask about matters more than **how many**. Smart static or pairwise questionnaires can cut questionnaire length by up to 3×. Asking about *attributes* (not just items) helps cold-start users. In the job domain the CV itself is a rich content signal, so cold start is mostly a content-based problem: parse the CV/GitHub, then confirm.

### Cited Findings
- Cremonesi et al. frame the number of ratings asked of new users as a trade-off between recommendation quality and user effort/burden, which affects perceived quality. — [Cremonesi et al. (PoliMi)](https://re.public.polimi.it/bitstream/11311/692316/3/p27-cremonesi.pdf) **[snippet only]**
- Sepliarskaia et al. (RecSys 2018), "Preference Elicitation as an Optimization Problem": a static questionnaire of **pairwise** questions shortens the needed questionnaire by **up to a factor of three** vs prior state of the art. Item selection determines recommendation quality. — [UvA PDF](https://irlab.science.uva.nl/wp-content/papercite-data/pdf/sepliarskaia-preference-2018.pdf)
- Personalized embedding-region elicitation (2024) uses two phases: a **burn-in** on popular items, then adaptive questions. — [arXiv 2406.00973](https://arxiv.org/abs/2406.00973)
- A 2025 study reports that asking about **item attributes** in addition to items improved results for cold-start users. — [arXiv 2510.27342](https://arxiv.org/html/2510.27342v1) **[snippet only]**
- In job recommendation, click-data availability strongly shapes which methods are viable. That favors content/knowledge-based approaches when there is no interaction history. — [de Ruijt & Bhulai, arXiv 2111.13576](https://arxiv.org/abs/2111.13576)
- Zell & Krizan: specific, objective self-evaluation questions are more accurate than broad ones, which is relevant to how onboarding questions are phrased. — [PubMed 26173249](https://pubmed.ncbi.nlm.nih.gov/26173249/)

### Inferences
Proposed minimum viable person profile for day-one matching:
1. **Hard constraints**: work authorization/visa status for the EU, remote vs relocation willingness, time zone, salary floor, and languages with level.
2. **Target roles**, 1–3, mapped to ESCO occupations.
3. **CV upload**: LLM extraction, then normalization to ESCO/LinkedIn-style canonical skills, then a user confirm/edit pass.
4. Optional **GitHub handle**: API-level skill evidence plus recency.
5. **3–5 pairwise or attribute questions** to rank the top skills and preferences (e.g., "which would you rather do: build ML pipelines or build product UIs?").

Then learn from implicit feedback (saves, dismissals, applications) as it arrives.
- Elicit **attributes** (stack, seniority, company size, remote policy) rather than asking the user to rate many individual postings, following the 2025 attribute finding and the pairwise efficiency result.

### Gaps
- No empirical study found on onboarding length or abandonment for job-seeker apps specifically.
- No source found on the minimum CV information needed for acceptable person-job fit accuracy.
