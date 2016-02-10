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
