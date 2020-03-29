# Frequently Asked Questions

### What's the purpose of this website?
Since 13th January 2019, 882 articles, concering the COVID-19 virus, are pulished on preprint servers (State: 2020/03/29).
This is an average of **more than eleven papers per day**. Most of these papers are not reviewed in a professional
reviewing process at the time of publication on the preprint server.

Our objective is to develop an easy to use interface to access, sort and classify the huge amount of articles about the 
COVID-19 virus.

**Features:**

- List and access all available preprints
- Sort and filter preprints by publishing date, authors name, title, keywords and category.
- Get a list of all papers, related to one of the predefined topics
- Get a list of recommended papers related to a specific question
- Sort papers by authors credits (Citations on [Google Scholar](https://scholar.google.com))

**Features (not yet implemented):**
- Allow verified experts to evaluate and review the papers informally to introduce a discussion before the paper is 
published officially and provide indications for the quality of the articles.

### Is this website ready-to-use?

This website was created during the [COVID-19 Global Hackathon](https://covid-global-hackathon.devpost.com) and is just 
a proof-of-concept.
In the current state, we cannot guarantee that the list of papers is always complete.
The number of citations per author is collected automatically and the correctness of the author mapping is not verified yet.

### Where does the research data come from?

- The database contains all paper from the [medRxiv](https://connect.medrxiv.org/relate/content/181) /
[bioRxiv](https://connect.biorxiv.org/relate/content/181) COVID-19 SARS-CoV-2 preprints page and is updated several
times a day.
- The number of citations per author is taken from Google Scholar.
- The different topics are taken from the
[COVID-19 Open Research Dataset Challenge (CORD-19)](https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/tasks),
initiated inter alia by the Allen Institue for AI (AI2) and the White House.

### Why do not all authors have a citation number?

Not for every author a profile could be found on Google Scholar or an unambiguous match was not possible.

### What's the difference between __category__ and __topic__?

The category represents the subject area, the paper is assigned to on medRxiv/bioRxiv. 
The topic is a question, asked as a task in the COVID-19 Open Research Dataset Challenge. We classify each paper
to one of these questions.

### How are the data classified to topics?

I don't know :)

### How does the paper recommandation for arbitrary questions work?

I don't know :)