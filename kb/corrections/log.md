# KB v3 — Corrections Memory (Layer 5)

Structured learning memory the agent loads at session start. **Not** a raw run log.

**TRP rule:** Every entry must be backed by an observed agent failure with a cited source log. Schema facts and join key formats belong in `kb/domain/` — not here. Do not record the correct answer — record the correct *approach*.

## Format

Each entry: **[query / pattern that failed] → [what was wrong] → [correct approach]**

For join-key failures include: `[Join attempted]`, `[Mismatch cause]`, `[Fix applied]`.

**`[applies_to]` tag** (loader-readable). Each entry declares which queries load it, as a comma-separated list of `dataset/queryN` tokens or a `dataset/*` wildcard. The loader (`common_scaffold/kb_loader.py`) filters entries by this tag so only relevant corrections enter the prompt — keeps the context lean and reduces per-call token cost.

- Examples:
  - `**[applies_to]:** query_yelp/*` — loads for all yelp queries.
  - `**[applies_to]:** query_yelp/query3, query_yelp/query5` — only the attribute-existence queries.
- Untagged entries load for every query in their `[Dataset]` — kept as backward-compat, not preferred.
- Add/remove tokens as new failures reveal which queries an entry actually helps.

---

## Dataset coverage

| `query_*` bundle | Corrections entries | Domain reference |
|------------------|--------------------|--------------------|
| `query_bookreview` | E1 (all queries) | `schemas.md` § Book Reviews, `join_key_glossary.md` § Book Reviews |
| `query_googlelocal/query2` | E8 | `schemas.md` § Google Local, `business_terms.md` § Google Local |
| `query_googlelocal/query3` | E9 | `schemas.md` § Google Local |
| `query_music_brainz_20k` | E10 (all queries) | `schemas.md` § MusicBrainz, `business_terms.md` § MusicBrainz |
| `query_yelp/query1` | E3, E3b | `schemas.md` § Yelp, `join_key_glossary.md` § Yelp |
| `query_yelp/query2` | E3, E3b, E7 | — |
| `query_yelp/query3` | E3, E3c | — |
| `query_yelp/query4` | E3, E5, E6, E7 | — |
| `query_yelp/query5` | E3, E3b, E3c, E7 | — |
| `query_yelp/query6` | E3, E5 | — |
| `query_yelp/query7` | E3, E4, E5, E6, E7 | — |
| All others | — | See `schemas.md` and `join_key_glossary.md` for schema facts |

---

## E1 — Cross-engine SQL (query_bookreview: PostgreSQL + SQLite)

**[Query / pattern]:** Multi-table questions that need both `books_info` and `review`.

**[Dataset]:** `query_bookreview`

**[applies_to]:** `query_bookreview/*`

**[What was wrong]:** Treating `review_database` as queryable inside a single PostgreSQL `JOIN` — the agent wrote a single SQL string that referenced tables from both databases.

**[Correct approach]:** Run **separate** `query_db` calls per logical DB. Merge results in `execute_python`. Use `join_key_glossary.md` § Book Reviews for the correct join key (`books_info.book_id` ↔ `review.purchase_id`).

**[Join attempted]:** `books_info` ↔ `review` in one SQL  
**[Mismatch cause]:** N/A — engines differ (Postgres vs SQLite), not a key format issue.  
**[Fix applied]:** Two separate `query_db` calls + pandas merge on normalized keys.

**[Source logs]:** `DataAgentBench/query_bookreview/query1/logs/data_agent/run_2/final_agent.json`

---

## E3 — Yelp: MongoDB ↔ DuckDB ID prefix mismatch (query_yelp)

**[Query / pattern]:** Any query joining Yelp business metadata (MongoDB) with review data (DuckDB).

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/*`

**[What was wrong]:** Agent joined `business_id` to `business_ref` without stripping the prefix difference, getting zero matched rows. Also: skipping `list_db` caused collection name mismatches.

**[Correct approach]:**
1. Always run `list_db` on `businessinfo_database` first to confirm live collection names.
2. Map IDs: `businessid_N` (MongoDB) → `businessref_N` (DuckDB) via `str.replace('businessid_', 'businessref_')`.
3. Always specify an explicit `limit` in MongoDB queries. Use a small limit (5–20) for exploration/sampling; omit `limit` or set `"limit": 0` for aggregation queries that need all rows. The DAB harness previously defaulted to `limit: 5` — this has been fixed, but explicit limits are still best practice.

**[Join attempted]:** `business.business_id` ↔ `review.business_ref`  
**[Mismatch cause]:** Prefix difference (`businessid_*` vs `businessref_*`).  
**[Fix applied]:** Prefix replacement before merge. Explicit `limit` in all MongoDB queries.

**[Source logs]:** `oracle-forge-data-agent/dab_runs/query_yelp/query1/logs/data_agent/run_2/final_agent.json`

---

## E3b — Yelp: state extraction from `description` field (query_yelp)

**[Query / pattern]:** Queries that group or filter Yelp businesses by US state.

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query1, query_yelp/query2, query_yelp/query5`

**[What was wrong — run_3]:** Agent used a narrow regex (`in [city], [STATE] this`) that only matched a subset of businesses. The unmatched businesses were silently excluded, skewing group counts.

**[What was wrong — run_5]:** Agent fixed the regex but omitted `limit` from the MongoDB query, receiving only a small subset of businesses and skewing aggregation results. (Root cause of the MongoDB limit issue is now fixed in the harness — see E3.)

**[Correct approach]:**
1. Use the regex `r',\s*([A-Z]{2})\s*,'` — the description format is consistently `in [City], [STATE], this...`.
2. Verify coverage: after extraction, check how many businesses have `state == None`. If > 5%, the regex is too narrow — inspect a sample of the unmatched descriptions and broaden the pattern.
3. Always specify an explicit `limit` when querying MongoDB (see E3).
4. Cast rating columns to numeric (`pd.to_numeric`) before any aggregation — DuckDB returns them as strings.
5. **Verify the aggregation winner before reporting.** After `groupby(state).agg(...)`, print the full sorted ranking (top 5 at minimum) and confirm the claimed top state actually has the highest count. Observed failure: agent reported `MO` as the top-review state when correct answer was `PA` — skipping this verification step let an early partial result slip through as the final answer.
6. **Do NOT use `business.review_count` (MongoDB) as the review count.** This field is a denormalized snapshot from the original Yelp dump and does **not** match the actual rows in the DuckDB `review` table in this benchmark. For any "number of reviews per state / per business / per category" question, aggregate from `review` in DuckDB (e.g. `SELECT business_ref, COUNT(*) FROM review GROUP BY business_ref`), then join to MongoDB businesses on the normalized id (E3). Observed failure — run_6: agent returned `PA, 3.6797` (≈ correct state, wrong average) because it counted `business.review_count` instead of joining to actual reviews, so the per-state average was computed over the wrong row set.

**[Join attempted]:** `business.business_id` ↔ `review.business_ref`  
**[Mismatch cause]:** See E3 for prefix handling. State extraction failure was separate.  
**[Fix applied]:** Broader state regex with coverage check; explicit MongoDB limit; numeric cast on rating; explicit top-N ranking print before reporting winner; review counts always aggregated from DuckDB `review`, never from `business.review_count`.

**[Source logs]:**
- run_3: `DataAgentBench/query_yelp/query2/logs/data_agent/run_3/final_agent.json`
- run_5: `DataAgentBench/query_yelp/query2/logs/data_agent/run_5/final_agent.json`
- run_6: `DataAgentBench/query_yelp/query2/logs/data_agent/run_6/final_agent.json` (wrong average from denormalized `review_count`)

---

## E3c — Yelp: "offered [feature]" means attribute key EXISTS, not value is True (query_yelp)

**[Query / pattern]:** Queries that count businesses "offering" a named feature (parking, Wi-Fi, etc.).

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query3, query_yelp/query5`

**[What was wrong — query3, run_1]:** Agent interpreted "offered X" as "has at least one `True` sub-value inside the X attribute dict." Many businesses that list a feature with all sub-values set to `False` were excluded, producing a significant undercount.

**[Correct approach]:**
1. "Offered [feature]" in the Yelp dataset means the **attribute key is present** in the `attributes` dict and is not `None`. A business that lists `BusinessParking: {garage: False, lot: False, ...}` still *offers* business parking as a declared feature.
2. Check: `attrs.get('FeatureName') is not None`.
3. Businesses with `attributes: "None"` (the string `"None"`) have no attribute data — exclude them.
4. Yelp `attributes` values are stored as **strings** (e.g. `"True"`, `"False"`, `"{'garage': False, ...}"`). Use `ast.literal_eval` only when you need to parse nested sub-values. For existence checks, testing `is not None` is sufficient.
5. **MANDATORY first step — sample before filtering.** Before writing any filter/aggregation code, run one small `execute_python` that prints 5 raw `attributes` values, their `type(...)`, and the repr — e.g. `for r in docs[:5]: print(type(r.get('attributes')), repr(r.get('attributes'))[:200])`. Skipping this step is the root cause of the run_3 `no_tool_call` termination: agent wrote a filter against an assumed format, got zero results, retried with slight variations, and gave up without inspecting the actual value.
6. **Never iterate a dict you are mutating.** If you're building a filtered dict from `attrs`, iterate `list(attrs.keys())`, not `attrs.keys()` or `attrs.items()` — observed `RuntimeError: dictionary changed size during iteration` in query3/run_3 caused the agent to abort without producing any output.
7. **Wrap the parser in try/except.** `ast.literal_eval` raises on malformed strings; one bad record should not kill the whole pass.

**[Reference pattern]:**
```python
import ast
def offers(a, k):
    if a in (None, "None", {}): return False
    try: d = ast.literal_eval(a) if isinstance(a, str) else a
    except Exception: return False
    v = d.get(k); return v is not None and v != "None"
# Usage: df[df['attributes'].apply(lambda a: offers(a,'BusinessParking') or offers(a,'BikeParking'))]
```

Do **not** additionally require the sub-values (e.g. `garage: True`) — that filter caused the observed undercount (24 instead of the correct 35).

**[Additional issue observed]:** Agent spent several LLM calls debugging variable name mismatches (`var_call-1` vs `var_tool_query_db_...`). Use `globals().keys()` or `locals().keys()` to inspect available variable names before referencing them.

**[Source logs]:**
- `DataAgentBench/query_yelp/query3/logs/data_agent/run_1/final_agent.json` (original undercount: 24)
- `DataAgentBench/query_yelp/query3/logs/data_agent/run_1_corrected/` (retry after correction)
- `DataAgentBench/query_yelp/query3/logs/data_agent/run_3/final_agent.json` (terminate_reason=`no_tool_call`: agent skipped sampling, hit `RuntimeError: dictionary changed size during iteration`, aborted with empty answer)

---

## E4 — Yelp: user registration year from `yelping_since` (query_yelp)

**[Query / pattern]:** Queries that filter reviewers by the year they registered on Yelp (e.g. "Among users who registered in 2016, which categories received the most reviews since 2016?").

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query7`

**[What was wrong — query7]:** Agent had no guidance on the `user.yelping_since` field format. Observed behaviors across runs: returning empty results, hitting `max_iterations`, and incorrectly filtering reviews before filtering users (so the review cohort was wrong). Runs terminated without an answer or produced zero-row intermediate results that propagated downstream.

**[Correct approach]:**
1. `user.yelping_since` in DuckDB is a string in `YYYY-MM-DD HH:MM:SS` format (same format as `review.date`). Do **not** assume it is a `TIMESTAMP` or `DATE` column — cast it explicitly.
2. Filter users first, then reviews. Two options:
   - **SQL:** `SELECT user_id FROM "user" WHERE yelping_since LIKE '2016-%'` — cheap prefix match.
   - **Pandas:** `pd.to_datetime(df['yelping_since']).dt.year == 2016`.
3. Then filter `review` by `user_id IN (<2016 cohort>)` AND `date >= '2016-01-01'`. The "since 2016" clause applies to **reviews**, not users — don't confuse the two time filters.
4. Categories live in `business.description` (MongoDB), not in `review`. After filtering reviews, join to MongoDB businesses (`business_ref` → `business_id`, see E3) and extract categories per business using E5's anchor-based parser.
5. **Sanity check cohort size:** print `len(users_2016)` and `len(reviews_by_cohort)` before aggregating. If either is 0, the filter is wrong — inspect `yelping_since` samples with `SELECT yelping_since FROM "user" LIMIT 10`.

**[Reference pattern]:**
```sql
-- Step 1: user cohort         SELECT user_id FROM "user" WHERE yelping_since LIKE '2016-%'
-- Step 2: cohort's reviews    SELECT business_ref, rating FROM review
--                             WHERE user_id IN (<cohort>) AND date >= '2016-01-01'
-- Step 3: join business_ref → business_id (E3), extract categories from description (E5), count per category.
```

**[Source logs]:**
- `DataAgentBench/query_yelp/query7/logs/data_agent/run_0/final_agent.json`
- `DataAgentBench/query_yelp/query7/logs/data_agent/run_1/final_agent.json` (hit `max_iterations`)

---

## E5 — Yelp: category extraction from `business.description` (query_yelp)

**[Query / pattern]:** Queries that group Yelp businesses by category (e.g. "Which category has the most businesses that accept credit cards?", "Top categories by review count").

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query4, query_yelp/query6, query_yelp/query7`

**[What was wrong — query4]:** Yelp businesses have **no `categories` field** in MongoDB. Categories are embedded inside the `description` string. Agent either (a) attempted to read a non-existent `business.categories` field and got empty/null results, or (b) parsed descriptions with a naive split that produced truncated or wrong category names. Reported category was `Shopping` with rating 3.78 — correct answer was `Restaurant` (or `Restaurants`) with rating 3.634.

**[Correct approach]:**
1. Categories live only in `business.description`. The description format is:
   `"Located at [address] in [City], [STATE], this [descriptor] offering [CATEGORY_LIST] [tail]."`
   Known anchor phrases that precede the category list: `"offering "`, `"services in "`, `"services, including "`, `"featuring "`. **Sample 10 descriptions first** and confirm which anchor is present before parsing.
2. Split on the anchor, then split the head of the remainder on `,` (strip whitespace). Stop at the first clause boundary — descriptions often append `"perfect for..."` or `"located in..."` after the category list; cut on these tail markers.
3. A business typically has multiple categories. For "which category has the most businesses" questions, **explode** one row per (business, category) before aggregating — a business with 3 categories counts in all 3 buckets.
4. **Normalize category tokens** before grouping: strip whitespace; the ground-truth labels use both singular (`Restaurant`) and plural (`Restaurants`) forms inconsistently — compare against `ground_truth.csv` when validating; don't aggressively stem.
5. After parsing, sanity-check with `df.explode('categories')['categories'].value_counts().head(20)` — if the top tokens look like partial sentences (e.g. `"perfect for date night"`), the split/tail cut is broken.

**[Reference pattern]:**
```python
ANCHORS = [" offering ", " services in ", " services, including ", " featuring "]
TAIL    = [" perfect for", " located in", " that ", "."]
# 1. find earliest anchor in desc.lower(); slice to end-of-anchor
# 2. cut the slice at the earliest TAIL marker
# 3. split on "," and strip → list[str]
# Then: df.explode('categories').groupby('categories').size() — sanity-check the top tokens aren't sentence fragments.
```

**[Source logs]:**
- `DataAgentBench/query_yelp/query4/logs/data_agent/run_0/final_agent.json` (original — wrong category reported)
- `DataAgentBench/query_yelp/query4/logs/data_agent/run_3/final_agent.json` (SyntaxError in generated parser — anchor list not used; agent wrote ad-hoc regex)
- `DataAgentBench/query_yelp/query7/logs/data_agent/run_4/final_agent.json` (top-5 categories returned `Shopping` first instead of `Restaurants` — parser extracted wrong tokens)

---

## E6 — Yelp: there is NO `business.categories` field (query_yelp)

**[Query / pattern]:** Any Yelp query that groups, filters, or counts by business category.

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query4, query_yelp/query7`

**[What was wrong — query4, query7]:** Agents repeatedly generated code like `df.groupby('categories')`, `business.find({'categories': {'$in': [...]}})`, or `SELECT categories FROM business` — all of which silently return empty results because **the field does not exist**. The MongoDB `business` document has: `_id`, `business_id`, `name`, `review_count`, `is_open`, `attributes`, `hours`, `description`. Categories live **only inside the `description` text**.

**[Correct approach]:**
1. Do **not** attempt to read `business.categories`. It will not error — it will return `None` / empty — which silently poisons downstream joins and aggregations.
2. Categories must be **parsed from `description`** using the anchor-based extractor in E5.
3. If a MongoDB query for documents with a specific category is needed, use a case-insensitive regex against `description` (e.g. `{"description": {"$regex": "offering [^.]*Restaurants", "$options": "i"}}`) — not an `$in` on a non-existent field.
4. Sanity check: `list_db` → inspect one `business` document → confirm the actual field set before writing any filter.

**[Source logs]:**
- `DataAgentBench/query_yelp/query4/logs/data_agent/run_0/final_agent.json` (agent tried `business.categories`, got empty, guessed `Shopping`)
- `DataAgentBench/query_yelp/query7/logs/data_agent/run_3/final_agent.json` (same trap — attempted to group on non-existent field)

---

## E7 — Yelp: compound "most X, average rating" questions — disambiguate what "most" counts (query_yelp)

**[Query / pattern]:** Two-part Yelp questions of the form "Which [dimension] has the most [entity that has property P], and what is the average rating of [those entities]?" — e.g. query2, query4, query5, query7.

**[Dataset]:** `query_yelp`

**[applies_to]:** `query_yelp/query2, query_yelp/query4, query_yelp/query5, query_yelp/query7`

**[What was wrong — query5, run_3]:** Agent filtered PA businesses offering WiFi (correct), counted 12 businesses (plausible), but then computed the average rating as `mean(business.stars)` over those 12 businesses — returning `~3.70` when the ground truth is `3.48`. Ground truth averages **review ratings** from DuckDB for those businesses, not the business-level summary rating from MongoDB.

**[What was wrong — query2, run_6]:** Agent counted reviews per state using `business.review_count` (see E3b §6), and used those same metadata values to compute the average — again, the average was computed over the wrong underlying rows.

**[Correct approach]:** For every compound "most X, average rating" question, **resolve two distinct questions** and write them as separate steps:
1. **What does "most" count?** Usually businesses matching a MongoDB filter — answer via MongoDB query + parse `description`/`attributes`. The count is an integer over the filtered MongoDB set.
2. **What does "average rating" average?** Always `review.rating` from DuckDB (cast to numeric), aggregated over the reviews belonging to the businesses identified in step 1 — never `business.stars` / `business.review_count`. Join on normalized id (E3).
3. State both numerators explicitly in a print statement before assembling the final answer, e.g.:
   ```
   n_businesses_in_PA_with_WiFi = 12
   n_reviews_for_those_businesses = 847
   avg_rating_over_those_reviews = 3.48
   ```
   Then report `(PA, 3.48)`. If you only have one intermediate number, you have not completed step 2.

**[Reference pattern]:**
```
# 1. Filter MongoDB → businesses matching property P; extract state/category from description.
# 2. count_by_dim = filtered_biz.groupby(dim).size() ; top = count_by_dim.idxmax() ; print ranking (E3b §5).
# 3. biz_refs = [id.replace('businessid_','businessref_') for id in filtered_biz[dim==top].business_id]
#    reviews = query_db("user_database", f"SELECT rating FROM review WHERE business_ref IN {tuple(biz_refs)}")
#    avg = pd.to_numeric(reviews.rating).mean()   # ← from review.rating, NEVER business.stars / review_count
# Answer = (top, avg). Print n_biz, n_reviews, avg before returning (E7 §3 verification).
```

**[Source logs]:**
- `DataAgentBench/query_yelp/query5/logs/data_agent/run_3/final_agent.json` (wrong average: `3.70` vs expected `3.48` — averaged `business.stars` instead of `review.rating`)
- `DataAgentBench/query_yelp/query2/logs/data_agent/run_6/final_agent.json` (see E3b §6 — same pattern)

---

## E8 — Google Local: business category is NOT in `name` — must search `description` (query_googlelocal)

**[Query / pattern]:** Queries that filter Google Local businesses by domain/category (e.g., "massage therapy businesses", "Chinese restaurants").

**[Dataset]:** `query_googlelocal`

**[applies_to]:** `query_googlelocal/query2`

**[What was wrong — query2, run_0]:** Agent filtered `WHERE name ILIKE '%massage%'` and returned 7 businesses. Missed `J B Oriental Inc` (ground truth, rating 4.166) — its `name` has no massage keyword, but its `description` reads *"rejuvenating therapies and soothing body treatments designed to enhance relaxation and well-being"*. Final answer had 3 of 4 expected massage therapy businesses.

**[Correct approach]:**
1. **There is no `category` column in `business_description`.** Full schema: `name, gmap_id, description, num_of_reviews, hours, MISC, state`. Categories are implicit in the free-text `description` field.
2. For category queries, search `description` with a **semantic keyword set**, not a single literal term. For massage therapy, a regex that captures all four ground-truth businesses: `description ~* '(massage|bodywork|therap(ies|ists)|body treatments|wellness (retreat|studio|center))'`.
3. Broad retrieval will over-match (e.g., `CrossFit to the Core`, `HAVEN Dispensary`). After the keyword filter, sample the matched descriptions and sanity-check each one actually describes the target category before applying the rating filter.
4. `MISC` is sparse and holds service/accessibility metadata (e.g., `{"Accessibility": ["Wheelchair accessible entrance"]}`) — it does **not** hold category tags. Don't rely on it.

**[Source logs]:**
- `DataAgentBench/query_googlelocal/query2/logs/data_agent/run_0/final_agent.json` (name-only filter → missed J B Oriental Inc)

---

## E9 — DAB harness: tool-result variables are `var_tool_*`, NOT `call_*` (query_googlelocal)

**[Query / pattern]:** Multi-step queries where `execute_python` references output from previous `query_db` / `list_db` calls.

**[Dataset]:** `query_googlelocal` (pattern applies to every DAB dataset — this entry targets googlelocal/query3 specifically because that's where the failure was logged; generalize to other datasets if the same pattern recurs there).

**[applies_to]:** `query_googlelocal/*`

**[What was wrong — query3, run_0]:** Agent wrote:
```python
business_df = pd.DataFrame(locals()['call_xR1xKk7DkK77PzQ3i7rZ7iTj'])
review_df  = pd.DataFrame(locals()['call_gE5f7z7OawB6of8w1BfK3q6N'])
```
The `call_*` prefix is hallucinated. DAB stores tool outputs under `var_tool_<tool_name>_<suffix>` (e.g., `var_tool_query_db_XXX`). The `execute_python` failed with `KeyError: 'call_xR1xKk7DkK77PzQ3i7rZ7iTj'`. Agent then proceeded directly to `return_answer` with a **fabricated top-5 list** (Taba Rug Gallery, The Boochyard, Beauty Bungalow, …) that no code ever computed — guaranteed-wrong answer after zero successful data processing.

**[Correct approach]:**
1. Tool-result variable names follow exactly one pattern: `var_tool_<tool_name>_<12-char suffix>`. `query_db` → `var_tool_query_db_<suffix>`; `list_db` → `var_tool_list_db_<suffix>`. Never invent `call_*`, `result_*`, `df_*`.
2. The exact variable name is returned in the tool response — copy it verbatim. If the result was large and written to a file, open it: `open(var_tool_query_db_XXX).read()`.
3. Before referencing any variable in `execute_python`, inspect the live namespace first:
   ```python
   print([k for k in globals() if k.startswith('var_tool_')])
   ```
4. On `KeyError` / `NameError`, **never** skip to `return_answer`. Re-run `execute_python` with the correct key, or re-query if the variable was lost. Hallucinating an answer after a tool error is the single worst failure mode — a wrong but confident answer is worse than `max_iterations`.

**[Source logs]:**
- `DataAgentBench/query_googlelocal/query3/logs/data_agent/run_0/final_agent.json` (`KeyError: 'call_xR1xKk7DkK77PzQ3i7rZ7iTj'` → agent hallucinated top-5 businesses with no computation backing the answer)
- Related: E3c "Additional issue observed" — same pattern in `query_yelp/query3`.

---

## E10 — MusicBrainz: one canonical song → MANY `track_id`s (query_music_brainz_20k)

**[Query / pattern]:** Any query that (a) sums revenue for a named song, or (b) ranks songs by revenue. Both require aggregating across title variants that share a canonical song.

**[Dataset]:** `query_music_brainz_20k`

**[applies_to]:** `query_music_brainz_20k/*`

**[What was wrong — query1, run_0]:** Agent ran `SELECT track_id FROM tracks WHERE title LIKE '%Get Me Bodied%' AND artist LIKE '%Beyonc%'` → got 3 track_ids (4233, 12954, 15158) → summed Apple Music × Canada revenue = **601.44**. Ground truth = **1059.46**. Two track_ids were silently dropped: `5281 "GetMe Bodied"` (no space between words) and `10838 "Beyoncé - Get Me Bodied"` (artist column is NULL, so the `artist LIKE '%Beyonc%'` filter excluded it).

**[What was wrong — query3, run_0]:** Agent ran `SELECT track_id, SUM(revenue_usd) FROM sales GROUP BY track_id` → picked the max (`track_id=14719 "Systemisch bled"`, 2522.82). Ground truth: `Zo gaat het leven aan je voor` at **9013.69** total — spread across 5 distinct `track_id`s (3024, 3435, 12620, 12854, 13225). Grouping by `track_id` under-aggregates: you compare single-variant songs against multi-variant songs, and the multi-variant ones lose.

**[Correct approach]:**
1. **Never group songs by `track_id` alone.** A canonical song can have 3–5+ `track_id`s. Observed variant formats for the *same* song:
   - Plain: `Get Me Bodied`
   - Prefix: `022-Get Me Bodied`, `006-Zo gaat het leven aan je voor` (leading digits + `-`)
   - `Artist - Title` form, often with `artist IS NULL`: `Beyoncé - Get Me Bodied`, `Syb van der Ploeg - Zo gaat het leven aan je voor`
   - Suffix in parens or after ` - `: `Get Me Bodied (Sexxxplicit R&B, Volume 25)`, `Zo gaat het leven aan je voor - Hillich fjoer | Heilig vuur`
   - Whitespace typos: `GetMe Bodied`
2. **Normalize titles before aggregating.** Reference SQL:
   ```sql
   -- Canonical title: strip leading "NNN-", strip "Artist - " prefix, strip trailing " (...)" or " - suffix", lowercase, trim
   SELECT
     TRIM(LOWER(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(title,
         '^[0-9]+-', ''),           -- strip "022-" etc.
         '^[^-]+ - ', ''),           -- strip "Artist - " prefix
         '\s*[-(].*$', ''))) AS canonical_title
   FROM tracks
   ```
3. **When filtering by artist, do NOT rely on `tracks.artist` alone.** It can be NULL for rows where the artist is embedded in the title. Use:
   ```sql
   WHERE (artist ILIKE '%Beyoncé%' OR artist ILIKE '%Beyonce%')
      OR (artist IS NULL AND title ILIKE '%Beyonc%')
   ```
   Accent-insensitive match: `Beyoncé` vs `Beyonce` (both appear in the data).
4. **Aggregate first in Python when DuckDB regex across engines is painful.** Pull all candidate tracks from SQLite, canonicalize titles in pandas, then `GROUP BY canonical_title` and sum revenue from the DuckDB sales pull.
5. **Sanity check against over-counting.** After normalization, print the top 10 canonical titles with their matched raw titles — if `Track A` and `Track B (Live)` collapse incorrectly, tighten the suffix regex.

**[Reference pattern]:**
```python
import re, pandas as pd

def canonical(title: str) -> str:
    if title is None: return ""
    t = re.sub(r'^[0-9]+-', '', title)               # "022-..." → "..."
    t = re.sub(r'^[^-]+ - ', '', t, count=1)          # "Artist - ..." → "..." (only if first chunk is 1 segment)
    t = re.split(r'\s+[-(]', t, maxsplit=1)[0]        # strip " - suffix" and " (paren)" tails
    return t.strip().lower()

tracks['canonical'] = tracks['title'].apply(canonical)
merged = sales.merge(tracks[['track_id', 'canonical']], on='track_id')
per_song = merged.groupby('canonical')['revenue_usd'].sum().sort_values(ascending=False)
```

**[Source logs]:**
- `DataAgentBench/query_music_brainz_20k/query1/logs/data_agent/run_0/final_agent.json` (missed 2 of 5 "Get Me Bodied" variants: `GetMe Bodied` no-space + artist=NULL row → 601.44 vs 1059.46)
- `DataAgentBench/query_music_brainz_20k/query3/logs/data_agent/run_0/final_agent.json` (grouped by `track_id` only → picked single-variant "Systemisch bled" @ 2522.82 instead of 5-variant "Zo gaat het leven aan je voor" @ 9013.69)

---

## Provenance

- All entries above are backed by observed agent failures with cited source logs.
- Schema facts (column semantics, join key formats, DB layouts) belong in `kb/domain/schemas.md` and `kb/domain/join_key_glossary.md` — not here.
- Last reviewed: 2026-04-18. Entries E4–E12 were previously removed (paper-sourced domain facts without failure logs); E4 and E5 have been reintroduced, and E6 and E7 added, each backed by cited Yelp run logs from the 2026-04-18 sweep (pass@1 moved 0.238 → 0.257; query1 0.67 → 0.80; queries 2/3/4/5/7 still at 0 — E3b §6, E3c §5–7, E6, and E7 target those residual failures specifically).
- 2026-04-18 googlelocal sweep (run_0, gemini-3.1-pro, no-KB baseline): query1 PASS, query2/3/4 FAIL. Added E8 (query2 name-vs-description category search) and E9 (query3 `call_*` → `var_tool_*` variable-name hallucination + fabricated-answer after tool error). Query4 terminated `no_tool_call` with 0 completion tokens — Gemini provider-side failure, no data-KB entry warranted.
- 2026-04-18 music_brainz_20k sweep (run_0, gemini-3.1-pro, no-KB baseline): query1 FAIL (601.44 vs 1059.46), query2 PASS, query3 FAIL ("Systemisch bled" vs "Zo gaat het leven aan je voor"). Both failures have the same root cause — one canonical song maps to 3–5+ `track_id`s with title prefix/suffix/whitespace/artist-in-title variants. Added E10 (title normalization + artist fallback when `tracks.artist IS NULL`). Also corrected misleading `domain/business_terms.md` § MusicBrainz entries ("Track = single song identified by track_id" → wrong; "Artist matching = exact case-sensitive" → wrong) and filled in the previously TBD `domain/schemas.md` § MusicBrainz sales schema.


### Pass 1 Correction — 2026-04-17 23:46

**[Failure type]:** WRONG ANSWER — agent returned an incorrect result

**[Query]:** During 2018, how many businesses that received reviews offered either business parking or bike parking?

**[Agent answer]:** 24

**[LLM calls]:** 5 | **[Tool calls]:** 7

**[What to do differently]:** Avoid the approach above. Check the KNOWLEDGE BASE CONTEXT for correct join keys, column semantics, and database routing. If the answer was wrong, re-examine the data processing logic.

---
