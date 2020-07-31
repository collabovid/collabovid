# Collabovid – Scrape App

The scrape app is responsible for keeping the article data up-to-date. On the one hand,
the app provides interfaces between the external data sources and our internal database.
On the other hand, different tools are provided, concerning the maintance of the data.

## Interface to external article data sources
### Data Sources
The app uses interfaces to several external data sources, providing meta data about 
COVID-19 related research articles. The articles are distinguished only by its DOIs/
arXiv ids. Hence, if an article was published with two different DOIs (for example as 
preprint and in a journal), it occurs two times in our database. If an article is 
available in more than one data source with the same DOI, we prioritize the data sources
as ordered in the list below and take only the data from the higher prioritized one.

- **medRxiv / bioRxiv** provide a periodically updated JSON-file with all Coronavirus 
  related preprints
- **arXiv** (using [arxiv](https://pypi.org/project/arxiv/)) provides a REST-API to
  access search query results. The used search query is:
  
      title:"COVID 19" OR title:"SARS-CoV-2" OR title:"coronavirus" OR 
      abs:"COVID 19" OR abs:"SARS-CoV-2" OR abs:"coronavirus"
  
- **Elsevier** provides all Coronavirus related research on the
  [Coronavirus Information Center](https://www.elsevier.com/connect/coronavirus-information-center),
  accessible via FTP
  
- **PubMed** (using [forked pymed](https://github.com/iacopy/pymed/tree/fork-fixes))
  provides a REST-API to access search query results. The used search query is:
      
      ("2019/12/01"[Date - Create] : "3000"[Date - Create]) AND 
      ((COVID-19) OR (SARS-CoV-2) OR (Coronavirus)) AND Journal Article[ptyp]
      
The associated classes for fetching the article data are located in `src/updater`, the
insertion to the database and insertion error handling is done by `collabovid-shared`.
 
### Filtering articles
The articles, indexed by Colabovid, are filtered using the two following rules:
1. The article was published in 2020 or later and
2. The title or the abstract matches the following regular expression:
       
       .*(corona.?virus|(^|\s)corona(\s|$)|covid.?(20)?19|(^|\s)covid(\s|$)|sars.?cov.?2|2019.?ncov).*

### CORD-19
The CORD-19 cache in `src/updater/cord19_cache.py` provides an interface to download and
cache the full [CORD-19 dataset](https://www.semanticscholar.org/cord19) from 
semantic scholar. Currently, we do not use any data from the CORD-10 dataset, due to the
following facts:
1. **Focus on COVID-19 research:** 
   The CORD-19 datasets comprises research not only about COVID-19 and the SARS-CoV-2 disease, but also all research about several related viruses and previous diseases, including MERS and SARS. Collabovid on the other hand filters more strictly and focuses on the 2020 SARS-CoV-2 disease with the primary aim of helping scientists to stay up-to-date with the latest research.
2. **Cleanliness of the Data:** 
   The CORD-19 dataset contains a huge amount of articles, fitting perfectly for text mining approaches. But the dataset also contains some amount of errors, misclassified articles, and non-research texts. While this is not a big deal in text mining, our aspiration is to provide a structured, transparent and clean dataset to our users.

## Other tools
### Geolocation extraction
The geolocation extraction works in two steps. First, the NLP framework 
[spaCy](https://spacy.io) is used to determine geopolitical entities (GPE) from 
the article titles. In a second step, the extracted entities are searched in the 
[geonames.org](geonames.org) database, to verify the location and get its coordinates.

The GeoNames wrapper, located in `collabovid_shared/src/geolocations/geonames_db.py`, is
used to build the GeoNames SQLiteDB on the one hand and to access it on the other hand.

The SQLite database can be built as follows:
1. Download the 
[allCountries](http://download.geonames.org/export/dump/allCountries.zip) 
Gazetteer data.
2. Run the `loaddata` method in the GeoNames Python wrapper with the path to the
downloaded file.

### Language Detection
[Googles CLD3](https://github.com/google/cld3) is used to determine the language
of article titles and abstracts. The results can be verified manually on the admin 
dashboard and articles in other languages may be deleted.

### Data Import and Export
The import and export classes may be used to keep local development databases in sync
with the production database without scraping all data redundantly on all systems. Keep
in mind, that artificial primary keys are not exported and hence may differ on
different systems.

Export archives on the productive system can be created as a task in the dashboard and 
are stored in the Amazon S3 bucket. The can be fetched to local development systems
using the cvid cli tool:

- List available archives: `cvid data download -l`
- Download an archive: `cvid data download <number>`

To import an archive, use the _import data_ tab on the admin dashboard.



### Fulltext and PDF Thumbnail Extraction
coming soon...

### Altmetric Scores
[Altmetric]() offers a score for reasearch articles, indicating its popularity in the 
news and on social media platforms. We use this score, to sort search results by trend 
(score increase past day, week, month, etc.) and by popularity (total score). The use of 
the Altmetric API without a rate limit requires an API key, which has to be set as
environment variable `ALTMETRIC_KEY`.
