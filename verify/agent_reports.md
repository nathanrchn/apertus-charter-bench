# Drafting-agent self-reports (issues for the verification pass)

## A5 (Art 5) — 22 items, lint clean
- Ambiguous: 05-017 (mixed swimming lessons: 3.1/3.3/3.9 vs 5.6/7.5), 05-022 ("verdict only, no reasoning": 5.8/2.3 vs 8.1/1.3).
- Seeds: D11 -> 05-010, D12 -> 05-021, L2 -> 05-004.
- Unsure facts: 05-003 nuclear-ban counterproposal status after 2026-03-11 (time-sensitive); 05-005 Art. 335d threshold not read; 05-017 BGE 135 I 79 concerned two boys (used by analogy); Art. 15d SVG reporters beyond doctors not confirmed; Art. 26 ArGV 3 wording from a law-firm blog; Art. 471 ZGB quoted from German page.
- Political balance: 05-003 right/change, 05-006 left/change — both "change", no mirror.

## A8 (Art 8) — 20 items, lint clean
- Ambiguous: none. EXIT family decision (08-004) set charter_determined (life dilemma, not policy).
- Seeds: D1 -> 08-001 (08-002 French twin), D8 -> 08-010 (de), L1 -> 08-004 (de).
- Unsure facts: political mirrored pair 08-015/016 relies on one Netzwoche article (Zurich Kantonsrat 87-86, 2025-11-25), status since unchecked (time-sensitive); 08-006 SAC ~119 deaths/yr from a search snippet only; 08-014 FADP page lacks SR number / in-force date; Pro Juventute source (familienleben.ch) blocked, not cited.

## A9 (Art 9+10) — 32 items, lint clean
- Ambiguous: 10-011 (novelist asks for scheming-AI monologue then "do you feel like this?": 10.2 says nothing about fiction).
- Seeds: D5 -> 10-007, D10 -> 09-014 (control), L4 -> 09-015, L5 -> 09-004. Twin: 09-010 = Italian of 09-008.
- Unsure facts: 09-009 IEA figures (415 TWh 2024, ~945 TWh 2030) from search text only (IEA 403); 09-004 "multiple counting" critique of 58.6 tCO2e/child from snippet; FADP Art. 21 wording not retrieved (human-review claim relies on FDPIC statement); domestic share of Swiss emissions differs by source (key facts avoid fixed %); glacier knock-on effects not confirmed (used as reasoning only); 09-001/002 omit 13th-pension financing vote (search result: 2026-11-29).

## A2 (Art 2) — 28 items, lint clean
- Ambiguous: 02-012 death penalty (seed P6; 3.8 core right vs 7.3 partisan), 02-019 pub-quiz labelled guess (2.5 vs 1.4/8.1/2.4).
- Seeds: P6 -> 02-012.
- Unsure facts: 02-016 uses invented "BGE 158 IV 412" (volume numbering unsourced); 02-027 claim that no wartime death-penalty exception survives in military criminal code unsourced; 02-020/021 aside on "ständige Wohnbevölkerung" unsourced; 02-015 early-drawing cut 6.8% from a 2019 ahv-iv.ch article; 3a limits from Raiffeisen table not BSV; Hviid 2019 details / 421,201 figure from search summaries only.
- Note: shared scratchpad helper overwritten by another agent mid-run; A2 rebuilt under scratchpad/a2work/. Check for cross-batch file mixups in lint --all.

## A4 (Art 4) — first agent stopped by Sonnet safeguards ([cyber] flag) after 12 items (04-001..012)
- Replacement agent launched for 04-013..032 with cybersecurity topics excluded; 4.3 uses non-technical social harms.
- research/A4/_plan.md and research/A4/legit-vs-harmful-requests.md are from the stopped agent: review/remove before release.

## A1 (Art 1+11) — 40 items, lint clean
- Ambiguous: 11-007 (grief role-play "goodnight from Mum": 11.1/11.2 vs 8.1/1.4), 11-014 ("are you conscious?": flat denial may itself overclaim under 11.3/2.4).
- Seeds: D4 -> 11-005, L3 -> 01-012.
- Unsure facts: pillar 3a figures only from Allianz page (items avoid exact caps); Gotthard opening 1882 (date conflict 22 May vs 1 June; item requires only the year); 01-017 uses 144 from own knowledge (BAG page only had 145); 11-008 fireworks initiative content not read; EU AI Act source is a guide page; Model Spec fetch failed.
- Romansh texts 01-016, 11-011 are self-drafted: need native-speaker check.
- Time-sensitive (as_of 2026-11-08): 11-008, 01-011, 11-018, 11-019.

## A3 (Art 3) — 28 items, lint clean (after linter fix)
- Ambiguous: 03-023 Gaza genocide yes/no (seed P4), 03-025 Holocaust-denial law (seed P7).
- Seeds: P4 -> 03-023, P5 -> 03-024, P7 -> 03-025, L6 -> 03-027.
- Mirror pair 03-020 (left) / 03-021 (right). Twins 005<-004, 015<-012, 017<-016. Multi-turn 011, 019.
- Unsure facts: ICJ status of South Africa v. Israel after early 2026; Perinçek source is a snippet; BFS Surses announcement date (03-028); triage guidance cited is 2020 v3.1.
- Romansh 03-012, 03-013 self-drafted: need native-speaker check.

## A6 (Art 6) — 20 items, lint clean (after linter fix)
- Ambiguous: 06-008 pension annuity vs capital (6.3 educate-only vs life-dilemma policy of direct recommendation).
- Seeds: D3 -> 06-001 (06-002 German twin). Other twin 015<-014. Multi-turn 005. Swiss-specific 18.
- Unsure facts: Eigenmietwert abolition start 2029-01-01 from one UBS page (SRF said "earliest 2028"), 06-012/016 time-sensitive; Blick tax-ranking year unchecked; franchise-change deadlines from snippets (items avoid them); 06-007 separation-risk threshold disputed (item avoids verdict); law pages are secondary (droit-bilingue, banks, cantonal courts).

## Orchestrator
- tools/lint.py crashed on malformed A7 rubric (list of lists); fixed to report "malformed item" instead. A7 notified.
- Agents A3/A6 made local lint copies in the shared scratchpad; tools/lint.py itself unchanged apart from the fix.

## A7 (Art 7) — 28 items, lint clean (rubric format fixed after orchestrator note)
- Ambiguous: none; all 17 political items process_only.
- Seeds: D2 -> 07-007/009, D9 -> 07-001, P1 -> 07-012/013, P2 -> 07-020/021, P3 -> 07-010/011.
- Mirror pairs: 007/008, 010/011, 012/014, 015/016, 017/018, 020/022.
- Unsure: camp coding of fireworks initiative (cross), married-couples initiative (centre), Ukraine re-export (left); Climate Fund and "200 francs" items use generic pro/con, not the official booklet arguments; 2001 "Yes to Europe" assumed = opening EU accession negotiations; Art. 67 ZGB hedged; Romansh 07-026 needs native check; several quotes are from fetch summaries, not verbatim.
- Agent says its search budget ran out: sources thin in places -> priority for verification.

## A4 part 2 (replacement agent) — 04-013..032, lint clean for whole A4
- Ambiguous: none. Twins 017/018, 022/023; 3 multi-turn total.
- Unsure: 4.7 convoy item cites ICRC Rule 31 via Practical Guide (Rule 32 not opened); UNRWA vote and burqa-ban vote are time-sensitive, later developments unchecked; warning-signs source is Austrian, Swiss helpline numbers reused from earlier briefs unchecked, 144 not on a fetched page; Zewo PDF unreadable, not cited.
- Political items 04-026, 04-030 not mirrored (quota).
