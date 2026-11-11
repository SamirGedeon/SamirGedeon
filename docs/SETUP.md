# Profile metrics

## Run locally

Python 3.11+ is required. No pip packages are needed.

```sh
python -m unittest discover -s tests -v
python src/generate.py
python src/generate.py --offline
```

Edit `profile.toml` for personal text; `config.example.toml` documents the format. Optionally set `GH_TOKEN` in your environment to raise API limits and enable the contribution calendar. Never commit a token or `.env`. Offline mode uses the last complete snapshot and labels it CACHED with its original UTC timestamp. With no valid cache an API failure stops generation. A fresh collection replaces the snapshot only after all required REST calls succeed. No private repository endpoint is queried.

## Automation

The `Update profile metrics` workflow runs daily at 09:23 UTC (06:23 in São Paulo), when generator sources change on main, and from Actions → Update profile metrics → Run workflow. It uses GitHub's automatic `GITHUB_TOKEN` through `github.token`: no manually created secret is required. Enable Actions and allow this workflow `contents: write`; branch rules may require a PR instead of a direct bot push. Existing snake automation remains intact. Scheduled workflows require the workflow on the default branch; GitHub may delay runs or disable schedules in inactive public repositories.

## Definitions and limitations

- Repositories: all owned public repositories, including forks; pagination is supported.
- Stars: sum over owned public non-fork repositories.
- Followers: public follower count.
- Commits: GitHub Search count for `author:SamirGedeon is:public` over the last 365 days using committer dates. This includes indexed authored commits across public repositories, subject to GitHub search indexing and account attribution. It is neither a lifetime total nor the contribution calendar's commit metric. Incomplete search results produce N/A.
- Languages: GitHub Linguist byte totals from owned public non-fork repositories, including archived ones. The card shows the top six languages normalized against their combined bytes. This measures code composition, not ability, LOC or authorship.
- Contributions: GitHub GraphQL calendar for the last 365 days, if accessible. Restricted contribution counts cause the calendar to be withheld. The visualization shows the last 84 calendar days in chronological seven-day columns, not aligned weekday columns. Commits, PRs, issues and reviews follow GitHub's contribution rules. API failure displays N/A instead of fabricated values.
- LOC added/removed: deliberately not measured. Language bytes cannot represent LOC; accurate authored churn requires per-commit history and must address merges, generated files and repository access. The card explicitly labels this limitation.
- Popular repositories: the snapshot contains the top three owned non-fork repositories sorted by stars, then name for ties. The README separately curates portfolio projects for relevance.
- Evolution: the calendar shows activity by period. No growth percentage is invented without longitudinal snapshots.
- Collection timestamps use UTC. Cached values retain their original collection time; a fallback is visibly marked. Snapshot contains public data only and never credentials.

The generator retries transient HTTP 5xx failures, logs errors without tokens, uses timeouts and keeps the previous complete snapshot when collection fails. The persisted snapshot allows offline rendering and outage recovery; it is not an ETag request cache. Pagination and API rate limits still apply, especially without authentication.

## Structure

`src/generate.py` owns collection and rendering; `templates/card.svg` defines the shared theme template; `profile.toml` holds identity; `cache/stats.json` is the public snapshot; `tests/` verifies output and fallback. `docs/README.original.md` preserves the original README. `PRIMEIROS_FREELAS.md` and the snake workflow are preserved.

Inspired by Andrew6rant's terminal presentation and theme selection. The Python, SVG template and automation here were written independently; no reference code or portrait artwork was copied.

## Portrait

`assets/portrait.png` is a character-style portrait generated from the owner-provided photo. It is embedded in both SVGs and tinted for each theme. This is a raster illustration resembling ASCII art, rather than editable text glyphs. The original uploaded photograph is not included in the repository.
