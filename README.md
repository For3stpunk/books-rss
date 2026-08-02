# literary-digest

Merges ~133 books/literary RSS feeds (see `sites_list.md`) into one
combined feed, on a schedule, for free. Same pattern as `politics-rss`.

## Setup

```
pip install -r requirements.txt
python merge_feeds.py
```

## Sharing the combined feed for free (GitHub Pages)

1. Push this repo to GitHub (public, for the free Pages tier).
2. **Settings → Pages → Deploy from a branch → `main` / root** → Save.
3. Your feed: `https://<username>.github.io/<repo>/combined.xml`
   Your browsable page: `https://<username>.github.io/<repo>/`
4. Drop the `combined.xml` URL into Feedly, Inoreader, Flipboard, etc.

Two things that bit the politics-rss repo, already handled here:
- `.github/workflows/update.yml` is at the correct nested path (GitHub
  Actions only looks in `.github/workflows/`, not a bare `workflows/`
  folder — easy to get wrong if you create it by hand in the GitHub UI).
- `.nojekyll` is included at the repo root so GitHub Pages serves
  `combined.xml`/`combined.html` as static files instead of running
  them through Jekyll (which otherwise falls back to rendering
  `README.md` as your site if it doesn't see an `index.html` yet).

Until you run the script once (locally or via **Actions → Update combined
digest → Run workflow**), there's no `combined.xml`/`index.html` in the
repo yet, so Pages has nothing to serve but the README.

## A note on this list

The source list was ~1000 lines but heavily padded with near-duplicate
names and repeated sub-feeds that don't correspond to real, distinct
sites. `merge_feeds.py`'s docstring explains exactly what was dropped
and why. What's left is ~133 real, findable publications -- still with
plenty of `# verify` tags since that many feeds can't be hand-checked
one by one. Run it, read the `[skip] ...` lines in the console, and
prune/fix from there.
