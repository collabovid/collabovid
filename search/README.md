# Search

The search component contains all logic and models for semantically analyzing the papers.
It is mainly responsible for implementing the search functionality and the methods for finding similar papers.
This is done by exposing  a `/search` api endpoint and a `/similar` api endpoint.
Furthermore, categorization and computing the coordinates for the visualization is also done by
the search component.

## Search Endpoints

The `api` folder contains a django app where the different api endpoints are exposed:

* GET `/search` The search endpoint receives the following parameters:
    
    | Parameter          | Description                                                                                                                                                                                                                      |
    |--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | published_at_start | Filter out publications that were published before this date.                                                                                                                                                                    |
    | published_at_end   | Filter out publications that were published before after this date.                                                                                                                                                              |
    | query              | The search query                                                                                                                                                                                                                 |
    | tab                | Which kind of search should be used. Possibilities are 'combined' for a search that combines semantic search  and keyword search and 'keyword' for keyword search.                                                               |
    | sorted_by          | By which criteria the results should be sorted. Possible options are 'top', 'newest',  'trending_d' (Trending during the last day), 'trending_w' (Trending during the last week), 'trending_1m' (Trending during the last month) |
    | authors            | The ids of the authors that should be used for filtering.                                                                                                                                                                        |
    | topics             | The ids of the topics that should be used for filtering.                                                                                                                                                                         |
    | authors_connection | Determines how filtering by authors should work. When the option 'one' is specified, a paper only  has to have one of the specified authors. If the option 'all' is specified, all authors have to appear in the paper.          |
    | categories         | The ids of the categories that should be used for filtering.                                                                                                                                                                     |
    | article_type       | Filter for the article type:                                                                                                                                                                                                     |
    | journals           | The ids of the journals that should be used for filtering.                                                                                                                                                                       |
    | paper_hosts        | The ids of the paper_hosts that should be used for filtering.                                                                                                                                                                    |
    | locations          | The ids of the locations that should be used for filtering.                                                                                                                                                                      |
    | result_type        | Either 'papers' (returns just or 'statistics'                                                                                                                                                                                    |
    | page               | Which page should be returned if result_type = 'papers'                                                                                                                                                                          |

    and returns a response object that contains the resulting dois of the paper with 
    their respective scores.

    
* GET `/similar` The similar endpoint retrieves the most similar papers given a set of papers. The endpoint takes
            the following GET parameters.
   
   | Parameter          | Description                                                                                                       |
   |--------------------|-------------------------------------------------------------------------------------------------------------------|
   | dois               | List of dois from the set of papers which most similar paper should be computed                                   |
   | limit              | integer that specifies how many similar papers should be retrieved. If not specified, retrieves all papers.       |
   
   and returns a json response with the following structure:
   
   ```
    {
        "result": [
            {
                "doi": <doi>,
                "score": <score>
            },
            ...
        ]
    }
  
  ```
  
* GET `/startup-probe`

    This is used internally by the Kubernetes scheduler as a startup and readiness probe.
    Because it takes some time to load the different models for providing the search functionality
    and the similar functionality into memory, the search service should not be considered ready when the models
    are not yet loaded. The endpoint simply returns a 500 when the models are not loaded yet
    and a 200 otherwise. This allows us to have no downtime when deploying a new version of the search
    service.
    

## Models

We have a `models` directory where all trained models are stored. During development,
this is simply the `models` directory in the main folder. 
During production, this is a folder that exist on the host (ec2 instance) under `/opt/models`.
The sync-daemon component is responsible for syncing the individual models (just directories that
are stored as zip files) from S3 storage to the models folder. The models folder contains
a file called `timestamps.json` which is used to keep track of new models. If a new model
is pushed to S3, the sync-daemon realizes that the copy on the host is an older copy of the model
and pulls the updated version. 

    
## Vectorizer

For the semantic search, computing similarities, visualizing the papers and the assignment
of topics, we compute an embedding for each publication. Therefore, we introduced the concept
of vectorizers. For every publication, a vectorizer computes one or multiple vectors which are then
stored in a paper_matrix. A paper matrix is a python dict which has the following structure:

    {   
        "index_arr": [<doi_1>, ..., <doi_n>], // contains the dois of the papers in the same order as they appear in the matrix
        "id_map" {doi_i: matrix_index}, // maps each doi to the index of the respective apper in the matrix
        "matrix_1": <numpy matrix of shape (papers x embedding_dimension)>,
        ...
        "matrix_k": <numpy matrix of shape (papers x embedding_dimension)>
    }
The only keys that are required are the `index_arr` and the `id_map`. Depending on
the vectorizer, multiple matrices can be added where each row corresponds to a publication.
The base class for a vectorizer is [PaperVectorizer](src/analyze/vectorizer/paper_vectorizer.py).
To get an instance of a vectorizer, the [get_vectorizer](src/analyze/vectorizer/__init__.py) method should be used.
All vectorizers that are currently used in collabovid are from the type `TransformerPaperVectorizer` which produces embeddings with a
custom trained BERT-siamese-network. Given a title and an abstract, the network was trained, to predict if they are from the same publication or not. 
By randomly exchanging some title and abstracts during training, the network has to learn what the papers are about to be good at the prediction.
Therefore, the resulting embeddings characterize the content of the publications.
A vector is produced for every title and abstract of each publication. Therefore,
the paper_matrix has two matrix entries `title` and `abstract` in this case.

    
After scraping new papers, the embeddings of the newly added papers have to be computed.
This is done by the [setup-vectorizer](src/analyze/setup_vectorizer.py) task.
For each vectorizer, the papers that are currently in the paper_matrix are synced
with the papers that are in the database.

After recomputing the paper matrix, the matrix is pushed to S3 where the matrices are stored in the
same fashion as the models in the `models/paper_matrix` directory and are synchronized by the sync-daemon.
This allows us to run multiple search containers where only one instance has to compute the paper matrix
for all the updated papers. Before every access of the paper matrix, it is checked if there
is a newer version available based on the timestamps file. If this is the case, the new paper
matrix is loaded into memory.


## Categorization

We categorize the papers into categories from LitCovid.
LitCovid is a curated literature hub for tracking scientific information 
about SARS-CoV-2 and labeled each pubmed paper with one or more labels from the categories:
    
    General, Mechanism, Transmission, Diagnosis, Treatment, Prevntenion, Case Report and Epidemic Forescating

We treated this as a multilabel classification problem and trained a longformer model
with a multilabel head on the labeled data from Litcovid. The respective model can be found
in the file [src/analyze/models/litcovid_classifier.py](src/analyze/models/litcovid_classifier.py). The model receives the title and the 
abstract from a paper as an input and outputs a probability for each category. If the probability
is above 0.5, we assign the category to the paper. The category assignment is done in the
[update-category-assignment](src/analyze/update_category_assignment.py) task.


## Visualization Coordinates
For the visualization feature, we wanted to use the coordinates of the vectorizer embeddings to provide
the user with a visual representation of the semantic relationship between papers. 
To map the embeddings into a three dimensional space, we use T-SNE. It does a better job in preserving
the relationships from the high dimensional space in 3d than PCA. But this also means that we have to recompute
the whole set of coordinates each time new papers are added or papers are changed. This is done by the
[reduce-embedding-dimensionality](src/analyze/reduce_embedding_dimensionality.py) task and is run as part of the
[scrape](../scrape/src/task_scrape.py) task.



## Elasticsearch
