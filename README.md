# ONDA

**(Online News Diversity Analyser)**

It has two parts, the extractor/aggregator/analyser (this part, written in
Python ) and the PHP front-end which also generates diversity scores in real-time.

I created this project for my University dissertation at The University of
Sheffield, and while successful was not perfect and could almost certainly do
with some improvements in style and in performance.

If you stumble across this I would be most interested to know what you make of
it.

## Getting Started: How does it work?

I'm writing this 6 years later, trying to work out how it worked, so I'll do
my best to describe it here in case you feel like helping.

### Assumptions that ONDA makes

* There is a MySQL database available with a certain schema (to be determined)
* The schema includes a list of newspapers' RSS feeds (sources) from which to
gather information about where to download articles (HTML web pages)
* The machine running ONDA has access to the web
* The system running it is capable of multi-threading

### Downloading articles

Before analysing or clustering anything, first a load of articles must be
downloaded. This appears to happen in `retrieval/source.py` whose `__main__`
function will, if certain lines are uncommented, retrieve articles from all of
the sources stored in the database.

The articles will sometimes be plain text but in other instances stored as
HTML, sometimes in horrible formats which need to be cleaned up. Once this is
done, they're put straight into the database.

### Counting terms

Once the articles have been downloaded and their raw text stored, ONDA needs
to count the individual terms used and remove any terms which are too common
to be considered significant.

This happens in `countuncountedarticles.py` - the counting refers to counting
terms. E.g., article 3829 may have 5 instances of the word "iraq" and 3
instances of the word "war" and 2 of the word "blair". (These examples aren't
random; part of my dissertation writeup covered the way that the news media
covered the Iraq War of 2003-2011).

The terms are also pruned: stop words stored in `stop_words` are not counted
when they are encountered because they are statistically insignificant and do
not reveal anything about the content of an article.

The code which is responsible for counting terms is in
`unigrammodel/termcounter.py`.


