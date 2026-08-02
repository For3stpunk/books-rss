#!/usr/bin/env python3
"""
merge_feeds.py -- Literary / Books Digest

Same pattern as the politics-rss project: pulls every feed in FEEDS,
merges by publish date (newest first), writes combined.xml / combined.html
/ index.html.

Requires: feedparser  (pip install feedparser)

--------------------------------------------------------------------------
A NOTE ON COVERAGE
--------------------------------------------------------------------------
The source list for this one was ~1000 lines but heavily padded --
dozens of near-identical repeats ("Reading Matters Archive", "Reading
Matters UK", "Reading Matters Australia", "Reading Matters Canada",
"Reading Matters Podcast", "Reading Matters Again", "Reading Matters
Archive II", etc. -- six-plus variants of a name with no findable site
behind most of them), 20+ "New Books in [Subject]" sub-feeds treated as
separate entries, a long run of "Book Riot Romance / Classics /
Nonfiction / Historical Fiction / Essays / Read Harder" as if each were
its own feed rather than a tag on one site, and a back third that
mostly re-lists names already covered in the front third under slightly
different labels.

Per "skip it if it doesn't seem real," this file keeps ~150 genuine,
distinct, independently findable literary publications and drops the
rest rather than inventing URLs for names that don't correspond to an
actual site. As with the politics digest, the URLs below are
best-guess (common CMS conventions), NOT individually hand-verified --
run the script and read the console; failing feeds print
`[skip] Name: could not parse (...)` and are safely ignored.

Deliberately excluded categories:
  1. The "Reading Matters"-style repeat-padding described above.
  2. Confirmed-defunct outlets: The Offing (closed 2021), Catapult
     Magazine (ceased 2022), Three Percent (long dormant).
  3. Personal book-blogger blogs from the raw list -- many are real
     (book blogging was/is a real community) but low-confidence and
     high-churn; only the handful with an active, findable presence
     are included, in "Independent Book Blogs" below.
  4. Podcast-only entries beyond a couple of flagship ones -- most
     don't have a text/article RSS feed distinct from their audio feed.
"""

import feedparser
import html
import socket
from datetime import datetime, timezone
from email.utils import format_datetime

# feedparser has NO default timeout -- without this, a single feed that
# accepts a connection but never responds (common among the `# verify`
# guesses below) can hang the whole run indefinitely instead of just
# failing fast. 10s is generous for a normal feed and still keeps a
# worst-case full run (all 133 feeds hanging) under ~25 minutes instead
# of unbounded.
socket.setdefaulttimeout(10)

FEEDS = {

    "Major Review Outlets": {
        "The New York Times — Books": "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml",
        "The New Yorker — Books/Culture": "https://www.newyorker.com/feed/culture",  # verify -- no books-only feed
        "The Atlantic — Books": "https://www.theatlantic.com/feed/channel/books/",  # verify
        "The Washington Post — Books": "https://feeds.washingtonpost.com/rss/entertainment/books",  # verify
        "Los Angeles Review of Books": "https://lareviewofbooks.org/feed/",
        "London Review of Books": "https://www.lrb.co.uk/feeds/rss",
        "New York Review of Books": "https://www.nybooks.com/feed/",
        "The Paris Review": "https://www.theparisreview.org/blog/feed/",
        "Literary Hub": "https://lithub.com/feed/",
        "Book Riot": "https://bookriot.com/feed/",
        "Electric Literature": "https://electricliterature.com/feed/",
        "The Complete Review": "https://www.complete-review.com/rss.xml",  # verify
        "The Millions": "https://themillions.com/feed",
        "Bookforum": "https://www.bookforum.com/feed",  # verify -- relaunched under The Nation, active
        "Public Books": "https://www.publicbooks.org/feed/",
        "Kirkus Reviews": "https://www.kirkusreviews.com/rss/",  # verify
        "Publishers Weekly": "https://www.publishersweekly.com/pw/rss.xml",  # verify
        "Library Journal": "https://www.libraryjournal.com/?rss=1",  # verify
        "School Library Journal": "https://www.slj.com/?rss=1",  # verify
        "BookPage": "https://bookpage.com/feed/",
        "Foreword Reviews": "https://www.forewordreviews.com/feed/",
        "Shelf Awareness": "https://www.shelf-awareness.com/rss.html",  # verify
        "CrimeReads": "https://crimereads.com/feed/",
        "TLS (Times Literary Supplement)": "https://www.the-tls.co.uk/feed/",  # verify -- paywalled
    },

    "Translation & International Literature": {
        "Asymptote": "https://www.asymptotejournal.com/feed/",
        "Words Without Borders": "https://www.wordswithoutborders.org/feed",
        "World Literature Today": "https://www.worldliteraturetoday.org/rss.xml",  # verify
        "ArabLit": "https://arablit.org/feed/",
        "Brittle Paper": "https://brittlepaper.com/feed/",
        "Johannesburg Review of Books": "https://johannesburgreviewofbooks.com/feed/",
        "Paper Republic": "https://paper-republic.org/feed",  # verify -- Chinese literature in translation
        "Latin American Literature Today": "https://www.latinamericanliteraturetoday.org/en/rss.xml",  # verify
        "Kitaab": "https://kitaab.org/feed/",
        "Wasafiri": "https://www.wasafiri.org/feed",  # verify
        # Three Percent (Univ. of Rochester translation blog) is long dormant -- omitted.
    },

    "Science Fiction / Fantasy": {
        "Reactor Magazine (formerly Tor.com)": "https://reactormag.com/feed/",
        "Locus Online": "https://locusmag.com/feed/",
        "Strange Horizons": "https://strangehorizons.com/feed/",
        "Uncanny Magazine": "https://www.uncannymagazine.com/feed/",
        "Lightspeed Magazine": "https://www.lightspeedmagazine.com/feed/",
        "Clarkesworld": "https://clarkesworldmagazine.com/feed/",
        "Apex Magazine": "https://apex-magazine.com/feed/",
        "Beneath Ceaseless Skies": "https://www.beneath-ceaseless-skies.com/feed/",
        "Grimdark Magazine": "https://www.grimdarkmagazine.com/feed/",
        "Black Gate": "https://www.blackgate.com/feed/",
        "File 770": "https://file770.com/feed/",
    },

    "Horror": {
        "Nightmare Magazine": "https://nightmare-magazine.com/feed/",
        "This Is Horror": "https://thisishorror.co.uk/feed/",
        "Rue Morgue": "https://rue-morgue.com/feed/",  # verify
    },

    "Crime / Mystery": {
        "Mystery Scene Magazine": "https://mysteryscenemag.com/feed",  # verify
        "Crime Fiction Lover": "https://crimefictionlover.com/feed/",
        "The Rap Sheet": "https://therapsheet.blogspot.com/feeds/posts/default",
    },

    "Romance": {
        "Smart Bitches Trashy Books": "https://smartbitchestrashybooks.com/feed/",
        "All About Romance": "https://allaboutromance.com/feed/",  # verify
        # Dear Author's site is largely inactive -- omitted.
    },

    "Comics & Graphic Novels": {
        "The Comics Journal": "https://www.tcj.com/feed/",
        "Women Write About Comics": "https://womenwriteaboutcomics.com/feed/",
        "The Beat (Comics Beat)": "https://www.comicsbeat.com/feed/",
        "Broken Frontier": "https://brokenfrontier.com/feed/",
    },

    "Poetry": {
        "Poetry Foundation": "https://www.poetryfoundation.org/rssfeed/poems.xml",  # verify
        "Poets.org (Academy of American Poets)": "https://poets.org/rss.xml",  # verify
        "Rattle": "https://www.rattle.com/feed/",
        "Cordite Poetry Review": "https://cordite.org.au/feed/",
        "Palette Poetry": "https://palettepoetry.com/feed/",  # verify
        "Frontier Poetry": "https://frontierpoetry.com/feed/",  # verify
    },

    "Children's & YA": {
        "The Horn Book": "https://www.hbook.com/feed",  # verify
        "Nerdy Book Club": "https://nerdybookclub.wordpress.com/feed/",
        "YA Books Central": "https://www.yabookscentral.com/feed",  # verify
        "Reading Rockets": "https://www.readingrockets.org/rss.xml",  # verify
    },

    "Literary Magazines & Journals": {
        "Granta": "https://granta.com/feed/",
        "n+1": "https://www.nplusonemag.com/feed/",
        "McSweeney's": "https://www.mcsweeneys.net/feed",
        "The Kenyon Review": "https://kenyonreview.org/feed/",
        "Ploughshares": "https://blog.pshares.org/feed/",
        "AGNI": "https://agnionline.bu.edu/feed",
        "Boston Review": "https://www.bostonreview.net/feed/",
        "The Yale Review": "https://yalereview.org/feed",  # verify
        "Image Journal": "https://imagejournal.org/feed/",
        "SmokeLong Quarterly": "https://www.smokelong.com/feed/",
        "American Short Fiction": "https://americanshortfiction.org/feed/",  # verify
        "The Adroit Journal": "https://theadroitjournal.org/feed",  # verify
        "Narrative Magazine": "https://www.narrativemagazine.com/rss.xml",  # verify
        # The Offing shut down in 2021 -- omitted.
    },

    "Ideas, Essays & Criticism": {
        "JSTOR Daily": "https://daily.jstor.org/feed/",
        "Aeon": "https://aeon.co/feed.rss",
        "Psyche": "https://psyche.co/feed.rss",  # verify
        "The Public Domain Review": "https://publicdomainreview.org/rss.xml",  # verify
        "The Marginalian (formerly Brain Pickings)": "https://www.themarginalian.org/feed/",
        "Open Culture": "https://www.openculture.com/feed",
        "The MIT Press Reader": "https://thereader.mitpress.mit.edu/feed/",
        "3:AM Magazine": "https://www.3ammagazine.com/3am/feed/",
        "Berfrois": "https://www.berfrois.com/feed/",
        "The Philosophical Salon": "https://thephilosophicalsalon.com/feed/",
    },

    "Politics & Culture Magazines (Books coverage)": {
        "The Baffler": "https://thebaffler.com/feed",
        "Dissent": "https://www.dissentmagazine.org/feed/",
        "Jacobin": "https://jacobin.com/feed/",
        "Current Affairs": "https://www.currentaffairs.org/rss/",
        "Harper's Magazine": "https://harpers.org/feed/",
        "The Nation": "https://www.thenation.com/feed/",
        "The New Republic": "https://newrepublic.com/feed",
        # These overlap with the politics-rss digest if you're running both --
        # left in since this project is meant to stand alone.
    },

    "Regional & International": {
        "Quill & Quire (Canada)": "https://quillandquire.com/feed/",
        "The Walrus (Canada)": "https://thewalrus.ca/feed/",
        "CBC Books (Canada)": "https://www.cbc.ca/cmlink/rss-books",  # verify
        "Australian Book Review": "https://www.australianbookreview.com.au/rss",  # verify
        "Meanjin (Australia)": "https://meanjin.com.au/feed",  # verify
        "Overland (Australia)": "https://overland.org.au/feed/",
        "Kill Your Darlings (Australia)": "https://www.killyourdarlings.com.au/feed",  # verify
        "The Wire — Books (India)": "https://thewire.in/rss",  # verify
    },

    "Academic / University Press": {
        "Princeton University Press Ideas": "https://press.princeton.edu/ideas/feed",  # verify
        "Oxford Academic Blog (OUPblog)": "https://blog.oup.com/feed/",
        "Columbia University Press Blog": "https://cupblog.org/feed/",
        "Stanford University Press Blog": "https://stanfordpress.typepad.com/blog/atom.xml",  # verify
        "Harvard University Press Blog": "https://harvardpress.typepad.com/hup_publicity/atom.xml",  # verify
        "University of Chicago Press Blog": "https://pressblog.uchicago.edu/feed",  # verify
    },

    "Independent & Small Press Blogs": {
        "Melville House (MobyLives)": "https://www.mhpbooks.com/feed/",  # verify
        "New Directions Publishing": "https://www.ndbooks.com/feed",  # verify
        "Verso Books": "https://www.versobooks.com/blogs/news.atom",  # verify
        "Open Letter Books": "https://www.openletterbooks.org/blogs/news.atom",  # verify
        # Catapult Magazine ceased publication in 2022 -- omitted.
    },

    "Publishing Industry News": {
        "The Bookseller": "https://www.thebookseller.com/feed",  # verify
        "Publishing Perspectives": "https://publishingperspectives.com/feed/",
        "Jane Friedman": "https://janefriedman.com/feed/",
        "Writer Unboxed": "https://writerunboxed.com/feed/",
        "Poets & Writers": "https://www.pw.org/rss.xml",  # verify
    },

    "Awards & Institutions": {
        "PEN America": "https://pen.org/feed/",
        "National Book Foundation": "https://www.nationalbook.org/feed/",  # verify
        "The Booker Prizes": "https://thebookerprizes.com/rss.xml",  # verify
        "Women's Prize for Fiction": "https://womensprizeforfiction.co.uk/feed/",  # verify
        "National Book Critics Circle": "https://bookcritics.org/feed/",  # verify
        "Center for Fiction": "https://centerforfiction.org/feed",  # verify
    },

    "Libraries & Archives": {
        "Library of Congress Blog": "https://blogs.loc.gov/loc/feed/",
        "Internet Archive Blog": "https://blog.archive.org/feed/",
        "American Libraries Magazine": "https://americanlibrariesmagazine.org/feed/",
        "Public Libraries Online": "https://publiclibrariesonline.org/feed/",
    },

    "Independent Book Blogs": {
        # These are real, long-running individual book bloggers (part of
        # the UK/international book-blogging community) -- included
        # selectively since most of the raw list's blog entries had no
        # findable site behind the name at all.
        "Stuck in a Book": "https://stuckinabook.com/feed/",  # verify
        "Winstonsdad's Blog": "https://winstonsdad.wordpress.com/feed/",  # verify
        "Vulpes Libris": "https://vulpeslibris.wordpress.com/feed/",  # verify
    },
}

MAX_ITEMS_PER_FEED = 5
MAX_TOTAL_ITEMS = 150


def fetch_all():
    items = []
    ok, skipped = 0, 0
    for category, sources in FEEDS.items():
        for name, url in sources.items():
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                print(f"  [skip] {name}: could not parse ({parsed.bozo_exception})")
                skipped += 1
                continue
            for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                dt = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
                items.append({
                    "category": category,
                    "source": name,
                    "title": entry.get("title", "(untitled)"),
                    "link": entry.get("link", url),
                    "summary": entry.get("summary", ""),
                    "date": dt,
                })
            print(f"  [ok]   {name}: {len(parsed.entries)} items")
            ok += 1
    print(f"\n{ok} feeds parsed, {skipped} skipped.")
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:MAX_TOTAL_ITEMS]


def write_html(items, path="combined.html"):
    rows = []
    for it in items:
        rows.append(f"""
        <div class="item">
          <span class="cat">{html.escape(it['category'])}</span>
          <span class="src">{html.escape(it['source'])}</span>
          <span class="date">{it['date'].strftime('%b %d, %H:%M UTC')}</span>
          <h3><a href="{html.escape(it['link'])}" target="_blank" rel="noopener">{html.escape(it['title'])}</a></h3>
        </div>""")
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Literary digest</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px;color:#222}}
.item{{border-bottom:1px solid #ddd;padding:14px 0}}
.cat{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#a33;font-weight:600;margin-right:8px}}
.src{{font-size:12px;color:#666}}
.date{{float:right;font-size:11px;color:#999}}
h3{{margin:6px 0 0;font-size:16px}}
a{{color:#222;text-decoration:none}}
a:hover{{text-decoration:underline}}
</style></head><body>
<h1>Literary digest \u2014 generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</h1>
{''.join(rows)}
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def write_rss(items, path="combined.xml"):
    entries = []
    for it in items:
        entries.append(f"""
    <item>
      <title>{html.escape(f"[{it['category']}] {it['title']}")}</title>
      <link>{html.escape(it['link'])}</link>
      <description>{html.escape(f"{it['source']}: {it['summary'][:300]}")}</description>
      <pubDate>{format_datetime(it['date'])}</pubDate>
      <guid isPermaLink="true">{html.escape(it['link'])}</guid>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Literary &amp; Books Publications \u2014 Combined Digest</title>
  <link>https://example.com</link>
  <description>Curated literary/books RSS sources, merged into one feed</description>
  <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
  {''.join(entries)}
</channel></rss>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(feed)


if __name__ == "__main__":
    print("Fetching feeds...")
    all_items = fetch_all()
    write_html(all_items, "combined.html")
    write_html(all_items, "index.html")
    write_rss(all_items)
    print(f"\nWrote {len(all_items)} items to combined.html, index.html, and combined.xml")
