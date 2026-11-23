# Hiring friction for non-EU candidates (Turkey / Central Asia, software / AI / ML) applying to UK, Germany, Switzerland, Spain and "remote in Europe" roles (as of Nov 2026)

Scope note: research run on 2026-11-23. About 19 tool calls. Most figures come from official sites, or from law-firm and Big-4 alerts that restate official figures. Vendor data (EOR providers, job boards) is labelled **[VENDOR]**. Statements from my background knowledge that I did not re-verify in this run are only in the Gaps sections, marked "unverified".

---

## UK: Skilled Worker visa rules 2025–2026, sponsor register, employer costs, tech sponsorship frequency

### Takeaway
Since 22 July 2025, a UK Skilled Worker sponsorship needs a degree-level (RQF 6) role paying at least £41,700. Since 16 December 2025 the employer also pays an Immigration Skills Charge of £1,320 per worker per year (large sponsors). About 126k organisations hold a Skilled Worker licence. Tech sponsorship is shrinking but still real: about 35k tech CoS applications in 2025, 15.7k of them for programmers and software developers. A UK posting without an explicit sponsorship signal should be treated as low-probability for a Turkey or Central Asia candidate.

### Cited Findings
- General Skilled Worker salary threshold rose from £38,700 to £41,700 for new applicants, effective 22 July 2025. — [Lewis Silkin](https://www.lewissilkin.com/insights/2025/07/03/new-uk-immigration-work-route-restrictions-from-22-july-2025); [IAS](https://iasservices.org.uk/major-changes-to-skilled-worker-visas-coming-this-month/); [Home Office stats commentary](https://www.gov.uk/government/statistics/immigration-system-statistics-year-ending-december-2025/why-do-people-come-to-the-uk-work)
- The skill level requirement rose from RQF 3 to RQF 6 (graduate level) on the same date. Lewis Silkin says this removes about 180 medium-skilled occupations unless they are on the Immigration Salary List. The Home Office says "over 100 occupations" are no longer eligible. — [Lewis Silkin](https://www.lewissilkin.com/insights/2025/07/03/new-uk-immigration-work-route-restrictions-from-22-july-2025); [gov.uk stats](https://www.gov.uk/government/statistics/immigration-system-statistics-year-ending-december-2025/why-do-people-come-to-the-uk-work)
- Extensions for people first sponsored before April 2024 use a lower threshold (£31,300 per NHS Employers; Mayer Brown gives about £31,000), with a transition running to 1 Dec 2026. — [NHS Employers](https://nhsemployers.org/articles/skilled-worker-route); [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2025/11/united-kingdom-mobility-2025-highlights-and-2026-outlook)
- Immigration Skills Charge rose 32% for Certificates of Sponsorship assigned on or after 16 December 2025: large sponsors from £1,000 to **£1,320 per worker per year**, small sponsors and charities from £364 to **£480 per year**. This is paid upfront for the whole visa length, so a 5-year large-sponsor CoS costs about £6,600 in ISC alone. — [Morgan Lewis](https://www.morganlewis.com/fr/pubs/2025/10/uk-announces-significant-increase-to-immigration-skills-charge-and-reforms-to-work-routes); [DLA Piper](https://www.dlapiper.com/en/insights/blogs/be-aware-uk/2025/changes-to-immigration-rules)
- The Migration Advisory Committee published a Salary Requirements Review (report Jan 2026). Its existence signals the thresholds remain under review. — [gov.uk MAC report PDF](https://assets.publishing.service.gov.uk/media/696f89a5c0f4afaa9536a0c3/Salaries_Requirements_Review_Report_-_Jan_2026.pdf); [MAC review page](https://www.gov.uk/government/publications/review-of-salary-requirements/review-of-salary-requirements-accessible)
- Register size: per the Home Office transparency data as reported by DavidsonMorris, **126,104 organisations** were licensed under Skilled Worker at 30 June 2026, up from 118,116 a year earlier. An analysis of the 20 Oct 2026 public register counted 143,175 entries and 127,702 distinct organisation names; entry counts overstate the number of organisations. — [DavidsonMorris](https://www.davidsonmorris.com/?p=119290); [Tarve](https://tarve.co.uk/blog/uk-sponsor-licences-removed-october-2026)
- Enforcement is rising. The government reported 1,948 sponsor licences revoked between July 2024 and June 2025. Secondary trackers report 2,346 Skilled Worker revocations and 2,632 suspensions in H1 2026, and 1,099 organisations removed from the register in October 2026; the October removals mix revocations, surrenders and expiries. — [gov.uk news](https://www.gov.uk/government/news/record-numbers-of-visa-sponsor-licences-revoked-for-rule-breaking); [Irwin Mitchell](https://www.irwinmitchell.com/news-and-insights/expert-comment/post/2026/march/102moan-sponsor-licence-revocations-at-an-all-time-high); [Tarve](https://tarve.co.uk/blog/uk-sponsor-licences-removed-october-2026)
- Tech volume: UKVI data obtained by RSM UK shows **34,936 overseas tech worker applications in 2025**, down 7% from 37,376 in 2024. This is the third straight annual fall, from a peak of 53,729 in 2022. By occupation in 2025: programmers and software developers 15,689 certificates; IT business analysts, architects and systems designers 11,821; IT quality and testing 3,091; cybersecurity 858; IT network professionals 310. — [The Register, 18 Aug 2026](https://www.theregister.com/a/5288476)
- Official stats: visas issued to "IT Professionals" fell 18% to **9,671** in the year ending December 2025. Main-applicant Skilled Worker applications were 36,100 in the year ending February 2026, down 44% year on year (all sectors). — [gov.uk Why do people come to the UK – Work (YE Dec 2025)](https://www.gov.uk/government/statistics/immigration-system-statistics-year-ending-december-2025/why-do-people-come-to-the-uk-work); [Monthly entry clearance stats](https://www.gov.uk/government/statistics/monthly-entry-clearance-visa-applications-february-2026/monthly-entry-clearance-visa-applications-february-2026)
- About a third of Skilled Worker grants (Oct 2024–Mar 2025) were in health and social care, so tech is a minority of sponsorship. — [Migration Observatory](https://migrationobservatory.ox.ac.uk/resources/briefings/work-visas-and-migrant-workers-in-the-uk/)

### Inferences
- The register has about 126k licensed organisations, against roughly 5.5M UK businesses (business count not verified here). A UK tech employer's presence on the register is a strong positive signal; absence is a strong negative.
- Employer cost per sponsored hire is material: ISC £1,320/yr, plus CoS fee, licence fee and legal time. Employers will only pay it when the role is hard to fill locally. Junior and mid roles near £41,700 are the least likely to be sponsored, so a model could weight UK sponsorship probability up with seniority and salary.
- Only about 10k–16k tech-related CoS/visas a year across the whole UK. For a random UK software posting, the base rate of sponsorship for an out-of-country candidate is low unless the posting says so.

### Gaps
- Unverified (background knowledge): the CoS assignment fee (believed £525 from April 2025), sponsor licence fees, and the English language requirement rising to B1/B2 in January 2026. Not re-confirmed this run.
- No source gives the share of UK tech job postings that offer sponsorship. That would need job-board scraping.
- The SOC 2136 grant count for 2025 from the gov.uk "Sponsored work visas by occupation" dataset (Occ_D02) was not extracted. The RSM/Register figure (15,689) is a CoS count, not grants.

---

## Germany: EU Blue Card thresholds 2025/2026, Chancenkarte, IT specialist without degree, processing, sponsorship frequency

### Takeaway
Germany is the most open of the four markets for non-EU IT talent. Blue Card thresholds for 2026 are €50,700 (standard) and €45,934.20 (shortage occupations, including IT, and recent graduates). IT specialists can qualify without a degree through experience. "Sponsorship" in Germany means only a job offer plus paperwork: the employer pays no ISC-style levy. A German posting in English with a salary at or above €45.9k is realistic for a non-EU candidate.

### Cited Findings
- 2026 Blue Card standard threshold: **€50,700 gross/year**, which is 50% of the pension insurance contribution ceiling. — [RT Partner](https://www.rtpartner.de/en/immigration/blaue-karte-eu-mindestgehalt-2026/); [Aldag Legal](https://aldaglegal.com/en/eu-blue-card-germany-2026/); [Bundesagentur für Arbeit (ZAV)](https://www.arbeitsagentur.de/vor-ort/zav/working-and-living-in-germany/iss-en/issue-03-2026/blue-card)
- 2026 reduced threshold: **€45,934.20 gross/year** (45.3% of the ceiling), for shortage occupations and recent graduates. Shortage groups include ICT, mathematics, natural sciences, engineering and medicine. — [Aldag Legal](https://aldaglegal.com/en/eu-blue-card-germany-2026/); [EY](https://globaltaxnews.ey.com/news/2025-2249-germany-approves-new-salary-thresholds-for-eu-blue-card-and-distinct-professional-experience-applicants)
- Sources report that IT specialists without a university degree can obtain a Blue Card at the reduced threshold based on professional experience. — [Aldag Legal](https://aldaglegal.com/en/eu-blue-card-germany-2026/); [Make it in Germany – Skilled Immigration Act](https://www.make-it-in-germany.com/en/visa-recognition/skilled-immigration-act)
- Federal Employment Agency approval: sources conflict. Make it in Germany says no approval is needed at or above €50,700. Others say approval is required under the reduced threshold. — [Make it in Germany](https://www.make-it-in-germany.com/en/visa-recognition/skilled-immigration-act); [se-legal](https://se-legal.de/eu-blue-card-salary-requirements/?lang=en)
- Opportunity Card (Chancenkarte), in force since 1 June 2024: a points-based job-seeker visa. Required funds for 2026 are **€1,091/month**, i.e. **€13,092** blocked for the standard 12 months. — [German Embassy Bern](https://bern.diplo.de/ch-de/service/visa/opportunity-card-2757060); [Bundesagentur für Arbeit](https://www.arbeitsagentur.de/vor-ort/zav/working-and-living-in-germany/iss-en/issue-02-2026/opportunity-card)
- Chancenkarte uptake was below expectations. About 2,360 applications in the first ~4 months (≈590/month, 15% rejected). One source reports 11,497 visas issued from 1 Jun 2024 to 15 Jun 2025; another reports 10,148 issued from 12,177 processed (≈83% grant rate). The government had expected about 30,000 a year. — [IamExpat](https://www.iamexpat.de/career/employment-news/just-2360-chancenkarte-applications-visa-launched-june); [Make it in Germany – 1 year of the Opportunity Card](https://www.make-it-in-germany.com/en/advice-support/newsletter/1-year-of-the-opportunity-card)

### Inferences
- For scoring: a Germany posting with stated salary ≥ €45,934 (2026) and an ICT role is legally sponsorable with low employer cost. The main remaining frictions are German-language requirements in the posting and the employer's willingness to wait for a visa.
- Chancenkarte lets a candidate be in Germany while job hunting, which reduces "must already be in Germany" friction. It requires about €13k in funds, so it is a candidate-side lever, not an employer signal.

### Gaps
- Unverified (background knowledge): the 2025 thresholds (€48,300 / €43,759.80); the exact IT-without-degree rule (believed to be at least 3 years' relevant experience in the last 7 years); Chancenkarte points criteria and the 20 h/week part-time work allowance; the 2025 Opportunity Card funds figure (€1,027/month). The make-it-in-germany IT visa options PDF could not be parsed.
- No authoritative data on typical Blue Card processing times (embassy waits vary widely by country; Ankara and Istanbul waits not found). The fast-track procedure (§81a AufenthG) was not researched.
- No figure for the share of German tech employers that hire from abroad or offer relocation.

---

## Switzerland: third-country quotas, priority for Swiss/EU workers, likelihood of a startup hiring non-EU

### Takeaway
Switzerland caps third-country hiring at 8,500 permits a year nationally (4,500 B + 4,000 L), unchanged for 2026. Quota use is well below the cap (about 52% by Sept 2025), so the cap is not what blocks candidates. The real filter is the labour-market test: the employer must show it could not find a Swiss or EU/EFTA candidate, and the candidate must be highly qualified. For a small startup this process is rarely worth it.

### Cited Findings
- 2026 third-country quotas are unchanged from 2025: **8,500** total, **4,500 B** (residence) and **4,000 L** (short stay). Renewals of B permits fall outside the quota. The amended ordinance took effect 1 Jan 2026. — [SEM press release](https://www.sem.admin.ch/en/newnsb/7HwBjdg5HpBA); [EY](https://www.ey.com/en_gl/technical/tax-alerts/switzerland-to-retain-work-permit-quotas-for-eea-uk-and-third-country-nationals-in-2026)
- UK nationals have a separate quota (2,100 B + 1,400 L). EU/EFTA service providers on assignments over 120 days: 3,000 L + 500 B. — [SEM](https://www.sem.admin.ch/en/newnsb/7HwBjdg5HpBA); [Vischer](https://www.vischer.com/en/knowledge/blog/quotas-for-foreigners-in-switzerland-in-2026/)
- Utilisation: 74% of the 2024 third-country L and B quotas were used by 31 Dec 2024. About 52% of the 2025 third-country quotas were used by end of Sept 2025. — [SEM](https://www.sem.admin.ch/en/newnsb/7HwBjdg5HpBA); [EY](https://globaltaxnews.ey.com/news/2025-2364-switzerland-to-retain-work-permit-quotas-for-eea-uk-and-third-country-nationals-in-2026)

### Inferences
- 8,500 permits for an economy of Switzerland's size, across all sectors, is a tiny channel. Low utilisation suggests the employer-side burden (priority test, qualification and salary checks, cantonal approval) deters applications more than the cap does.
- For scoring: Swiss postings should take a heavy penalty for non-EU candidates unless the employer is large or international (pharma, banks, big tech with Zurich hubs), or the posting explicitly mentions relocation or permits. Small Swiss startups score near zero unless they state otherwise.

### Gaps
- Unverified (background knowledge): the legal basis for Swiss/EU priority (Art. 21 Foreign Nationals and Integration Act, AIG) and the requirement for "managers, specialists and other qualified workers" (Art. 23 AIG). Not re-fetched this run.
- No data on startup versus corporate share of third-country permits, or on IT's share of the quota.
- No data on cantonal processing times.

---

## Spain: Highly Qualified Professional / EU Blue Card, Digital Nomad Visa

### Takeaway
Spain's Blue Card threshold for 2026 was set at €39,269.92/yr (1.4× average gross salary) in January 2026. It was reportedly raised to €41,356.36 in May 2026. A shortage-occupation rate (0.8 coefficient, about €33k) also exists. The Digital Nomad Visa needs about €2,849/month (200% of the minimum wage, SMI), with at least 80% of income from non-Spanish clients or employers. That makes it a viable route for a candidate who keeps a non-Spanish remote employer, rather than a route for being hired by a Spanish company.

### Cited Findings
- Order PJC/44/2026 (BOE, 30 Jan 2026) set the standard EU Blue Card minimum at **€39,269.92 gross/year** (1.4× INE average annual gross salary). — [KPMG Flash Alert 2026-054](https://kpmg.com/xx/en/our-insights/gms-flash-alert/2026/flash-alert-2026-054.html); [Newland Chase](https://newlandchase.com/spain-revises-salary-thresholds-for-eu-blue-card-applicants/)
- Reported increase on 28 May 2026 to **€41,356.36**, with a reduced (0.8 coefficient) rate of **€33,085.09**. Only secondary sources report this; I did not see the BOE order. — [Jobbatical](https://www.jobbatical.com/blog/spain-eu-blue-card-salary-drop-mid-contract); [Tands Law](https://tandslaw.com/spain-immigration-alert-salary-threshold-update-june-2026/)
- Digital Nomad Visa: income ≥ 200% of SMI, **€2,849/month (€34,188/yr) in 2026**, up from €2,763/month in 2025. A spouse adds 75% of SMI (€1,069/month); each additional dependant adds 25% (€357/month). The updated threshold also applies to renewals. — [The Local Spain](https://www.thelocal.es/20260216/confirmed-the-financial-requirements-for-spains-digital-nomad-visa-in-2026); [Jobbatical](https://www.jobbatical.com/blog/spain-digital-nomad-visa-income-smi-increase); [Immigrant Invest](https://immigrantinvest.com/insider/spain-minimum-wage-rules/)
- At least 80% of a digital nomad's income must come from non-Spanish sources (e.g. remote work for a foreign company). — [Remote Work Europe](https://remoteworkeurope.eu/insights/spain-digital-nomad-visa-2026/); [Jobbatical](https://www.jobbatical.com/blog/spain-digital-nomad-visa-income-smi-increase)
- One source (Altery) gives a conflicting figure of about €2,442/month, apparently from applying 200% to the 14-payment monthly SMI. Treat it as an outlier. — [Altery](https://altery.com/guides/personal/digital-nomad-visa-spain/)
- Deel's 2025 hiring report ranks Spain 5th (5.2%) among cross-border hire destinations for well-funded startups. **[VENDOR]** — [Deel Global Hiring Report 2025](https://www.deel.com/global-hiring-report-2025/)

### Inferences
- Spain's Blue Card thresholds (about €33k–41k) are lower than Germany's, so many mid-level Spanish tech salaries can legally qualify. Spanish tech salaries are also lower, so clearing the bar is less automatic than it looks. Also, many Spanish postings require Spanish.
- The Digital Nomad Visa matters for "remote in Europe/EU" roles. A Turkey-based candidate hired as a contractor or through an EOR by a non-Spanish company could relocate to Spain under it. This partly unlocks "must reside in EU" postings, but only after landing a qualifying remote contract.

### Gaps
- Unverified (background knowledge): Spain's national Highly Qualified Professional permit under Ley 14/2013 (processed by UGE-CE, with an often-cited salary benchmark around €40k and a fast processing target of about 20 working days). Not confirmed this run.
- Official confirmation (BOE) of the May 2026 increase to €41,356.36 not found.

---

## "Remote in Europe/EMEA" roles: why employers restrict location, how common "anywhere" is, EOR cost, contractor setups

### Takeaway
Truly worldwide remote postings are rare. Jobgether's Sept 2026 index finds worldwide 4.0% (about 2.1% after removing mis-tagged postings), region-wide such as "Europe" 4.4%, and single-country 49.3%. Worldwide postings draw 8.8× the average applicants. Employers restrict location because of permanent establishment (PE) exposure, payroll registration and misclassification risk. EOR platforms solve this for about $599–699 per employee per month. **[VENDOR]** A "remote, EMEA" role is realistic for a Turkey-based candidate only if the employer uses an EOR or contractor model that covers Turkey.

### Cited Findings
- Scope of new remote postings, Sept 2026 (200,043 deduplicated postings, Aug 1–Sep 30 2026): single-country 49.3%, US-states-only 35.7%, region-wide (e.g. Europe/EMEA) 4.4% (up from 3.8%), worldwide 4.0% (down from 4.8%). Excluding employers whose ATS tags everything "anywhere", true worldwide is about **2.1%**. **[VENDOR, platform data]** — [Jobgether blog, Sept 2026](https://jobgether.com/blog/remote-hiring-trends-september-2026); [Jobgether Remote Work Index](https://jobgether.com/remote-work-index/2026-09)
- Competition: a worldwide posting drew **8.8×** the average applications; a region-wide posting **3.7×**; a single-country posting 0.66×. **[VENDOR]** — [Jobgether](https://jobgether.com/blog/remote-hiring-trends-september-2026)
- Why employers restrict: a remote worker abroad can create a permanent establishment, a taxable business presence that triggers corporate tax plus local payroll registration, wage-tax withholding and social security. A triggered PE can force local registration, financial filings and compliance with local employment law. — [Thomson Reuters (2026)](https://tax.thomsonreuters.com/blog/payroll-pulse-navigating-permanent-establishment-risk-with-remote-workers-in-2026/); [The Tax Adviser, Oct 2026, on new OECD guidance](https://www.thetaxadviser.com/issues/2026/oct/permanent-establishment-risk-from-remote-work-and-the-oecds-new-guidance/)
- PE risk rises with how much of the work happens from the remote location (one guide flags working 50%+ of the time from home over 12 months) and varies by country. **[VENDOR]** — [Payoneer](https://www.payoneer.com/resources/workforce-management/hr-and-compliance/permanent-establishment-risk/); [Remote.com](https://remote.com/en-gb/blog/eor-peo/permanent-establishment-risk-for-remote-workforce)
- EOR vendors claim the EOR "eliminates" PE risk. CXC Global argues an EOR does not automatically remove it. **[VENDOR, conflicting]** — [Remote.com](https://remote.com/en-ie/blog/eor-peo/remote-work-permanent-establishment-risk); [CXC Global](https://www.cxcglobal.com/blog/risk-compliance-and-law/what-is-permanent-establishment-risk/)
- EOR list prices, 2026 **[VENDOR]**:
  - Deel: **$599/employee/month**, month-to-month. — [Deel pricing](https://www.deel.com/en-gb/pricing/)
  - Remote.com: $599 (annual billing) or $699 (monthly). One report says Remote raised its EOR rate from $599 to $699 in March 2026. — [Remote vs Deel](https://remote.com/en-ph/why-remote/compare-remote/deel-vs-remote); [Rework](https://resources.rework.com/tools/payroll/best-remote-com-alternatives); [Pin](https://www.pin.com/blog/deel-pricing/)
  - Oyster: about $699/month (one source $499–699). — [Oyster](https://www.oysterhr.com/library/deel-competitors); [Pin](https://ghost.pin.com/best-eor-providers/)
  - Lower-cost providers: Multiplier about $400; Remofirst $199; Playroll from $399. — [TechRepublic](https://www.techrepublic.com/article/best-employer-record-services/); [Playroll](https://www.playroll.com/blog/best-eor-providers)
- Deel 2025 report (1M+ contracts, 150+ countries): among about 100 startups that raised $100M+, the leading cross-border hire destinations are the UK 12.2%, Canada 11.9%, Germany 8.8%, Australia 5.8%, Spain 5.2%. In 2024, domestic hiring on Deel grew faster than cross-border hiring (104% vs 42%). **[VENDOR]** — [Deel Global Hiring Report 2025](https://www.deel.com/global-hiring-report-2025/); [Deel 2024 PDF](https://deel.com/hubfs/Global%20Hiring%20Report/Deel%20Global%20Hiring%20Report%202024.pdf)

### Inferences
- About $7.2k–8.4k a year in EOR fees on top of salary and employer social contributions. For a mid-level engineer this is a 10–20% cost premium, so employers only pay it for candidates they clearly prefer. Contractor arrangements are cheaper but carry misclassification risk.
- "Remote, Europe/EMEA" often means "we have entities or EOR coverage in these countries". Turkey is often in EMEA but is not EU, and Central Asian countries are frequently outside EOR "supported" lists or priced higher (not verified). A model could treat "EMEA" as moderately open, "EU only" or "must reside in the EU" as closed, and "worldwide/anywhere" as open but very competitive (8.8× applicants).

### Gaps
- No independent (non-vendor) data on the share of European remote tech postings that are "EU-only" versus "EMEA" versus "anywhere"; Jobgether is single-platform.
- No source verified on whether Deel, Remote or Oyster support EOR in Turkey, Kazakhstan, Uzbekistan or Kyrgyzstan, or at what price (EOR prices often vary by country).
- No data on the share of international hires done as contractors versus employees for Turkey specifically.

---

## Turkey-based candidates: remote work for foreign companies, service-export tax treatment, Turkish talent abroad

### Takeaway
Turkey actively incentivises exporting software services. Presidential Decree No. 11257 (30 Apr 2026) reportedly raised the deduction on income from qualifying services (including software) delivered to non-resident clients from 80% to 100%, provided proceeds are brought into a Turkish bank. That makes the contractor (freelance or sole-proprietor) model cheap for the candidate and easy for the foreign employer. It is the most realistic route into "remote" roles that will not pay for an EOR.

### Cited Findings
- Presidential Decree No. 11257, published 30 Apr 2026, amended the service-export deduction: qualifying services provided from Türkiye to non-residents and used abroad moved from **80% to 100%** deductible. Eligible services include software, engineering, design, data storage and others. Sources differ on the start date ("income generated from 2026" vs "as of 1 Jan 2026"). — [EY Tax Alert 2026-0992](https://www.ey.com/en_gl/technical/tax-alerts/turkiye-amends-certain-income-tax-and-corporate-tax-exemptions-and-deductions); [Mondaq – Decree 11257 and Law 7582](https://www.mondaq.com/turkey/tax-authorities/1799772/recent-tax-developments-presidential-decree-no-11257-and-law-no-7582); [VATupdate](https://www.vatupdate.com/2026/05/18/tax-advantages-for-service-exporters-income-exemption-corporate-tax-reduction-minimum-tax-vat-exemption/)
- The deduction applies to both corporations and individual taxpayers; export proceeds must be transferred to a Turkish bank account. — [EY](https://www.ey.com/en_gl/technical/tax-alerts/turkiye-amends-certain-income-tax-and-corporate-tax-exemptions-and-deductions); [Mondaq](https://www.mondaq.com/turkey/corporate-tax/1789750/significant-tax-incentives-on-t%C3%BCrkiyes-agenda)
- A separate 2026 personal tax regime gives new Turkish tax residents (from 1 Jan 2026) an exemption on foreign-sourced income. This is not the same as the service-export deduction. — [EY Tax Alert 2026-1215](https://www.ey.com/en_gl/technical/tax-alerts/turkiye-introduces-new-personal-tax-regime-including-foreign-income-exemption-inheritance-tax-relief-and-asset-repatriation-measure)
- Deel's data ranks Türkiye #4 for stablecoin adoption among contractors (after Argentina, Cameroon and South Korea; Tajikistan #6). This indirectly shows a sizeable Turkish (and Central Asian) contractor population on Deel. **[VENDOR]** — [Deel Global Hiring Report 2025](https://www.deel.com/global-hiring-report-2025/); [People Matters](https://www.peoplematters.in/news/recruitment/ai-trainer-boom-urban-return-and-currency-hopping-signal-global-workforce-trends-deel-report-48757)

### Inferences
- A Turkey-based candidate can credibly offer the employer "hire me as a contractor (invoice from Türkiye)". That removes EOR cost and PE risk for most short-term arrangements, so postings that mention "contractor", "B2B" or "freelance" are realistic.
- The 100% deduction makes a lower gross contract rate equal a high net. Candidates can price competitively against EU candidates, which partly offsets location friction.

### Gaps
- No source confirms whether a Turkey-resident *employee* of a foreign company (via EOR or payroll) qualifies for the deduction, versus only self-employed or company service exporters.
- No reliable data on the number of Turkish tech workers hired abroad or remotely (e.g. Turkish citizens among UK Skilled Worker grants or German Blue Cards). Not found this run.
- No Central Asia (Kazakhstan, Uzbekistan) specific tax or remote-work data researched.

---

## Posting phrases that signal openness versus closure

### Takeaway
No authoritative study ranks posting phrases. A rule set has to come from the legal mechanics above: sponsorship needs a licensed sponsor and a salary above the threshold, and remote work needs entity, EOR or contractor coverage. The phrase lists below are inferences, not sourced statistics.

### Cited Findings
- A "remote" label can still require residence in one country or state. Most remote postings (≈85%) are country- or US-state-restricted. **[VENDOR]** — [Jobgether](https://jobgether.com/blog/remote-hiring-trends-september-2026)
- The UK public Register of Licensed Sponsors lists only currently licensed employers, so it can be used to check whether a UK employer *can* sponsor. — [Tarve](https://tarve.co.uk/blog/uk-sponsor-licences-removed-october-2026); [DavidsonMorris](https://www.davidsonmorris.com/?p=105103)

### Inferences
- **Strong open signals:** "visa sponsorship available/provided"; "we sponsor visas"; "relocation package/support"; "Blue Card"; "we hire worldwide / anywhere"; "contractor / B2B / freelance welcome"; "via Deel / Remote / Oyster"; "EMEA (incl. Türkiye)"; an English-language posting from a German company with a salary at or above €45.9k (2026).
- **Moderate signals:** "remote in EMEA"; "remote, CET ±2/3 hours" (a time-zone constraint rather than a residency one, and Türkiye is UTC+3); "international team, 30+ nationalities"; large multinational employer; UK employer on the sponsor register.
- **Closed signals:** "must have the right to work in the UK/EU"; "we are unable to sponsor"; "no visa sponsorship"; "EU residents only"; "must be based in [country]"; "security clearance required"; native or fluent German, Spanish or French required; Swiss small-company posting without a relocation mention; UK salary below £41,700 for a non-ISL role (legally unsponsorable for new entrants).

### Gaps
- No empirical data on how often "visa sponsorship available" postings actually hire from abroad, or on false-positive rates (e.g. sponsorship only for in-country switchers).
- No source on how ATS "work authorization" knockout questions affect non-EU applicants' pass rates.
