def download_files():
    import os
    import requests
    from analyze.vectorizer import TitleSentenceVectorizer, SentenceChunkVectorizer, PretrainedLDA

    URLS = {
        "lda-model":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/lda.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "lda.pkl")
            },
        "lda-vectorizer":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/vectorizer.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "vectorizer.pkl")
            },
        "lda-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/lda/paper_matrix.pkl",
                "destination": os.path.join(PretrainedLDA.LDA_BASE_DIR,
                                            "paper_matrix.pkl")
            },
        "title-sentence-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/title_sentence_vectorizer/paper_matrix.pkl",
                "destination": os.path.join(TitleSentenceVectorizer.TITLE_SENTENCE_VECTORIZER_BASE_DIR,
                                            "paper_matrix.pkl")
            },
        "sentence-chunk-paper-matrix":
            {
                "download": "https://covid-publications.s3.amazonaws.com/resources/sentence_chunk_vectorizer/paper_matrix.pkl",
                "destination": os.path.join(SentenceChunkVectorizer.SENTENCE_CHUNK_VECTORIZER_BASE_DIR,
                                            "paper_matrix.pkl")
            }
    }

    def download_file(down, path):
        if os.path.exists(path):
            print(path, "exists, skipping...")
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            r = requests.get(down)
            with open(path, 'wb') as f:
                f.write(r.content)

    for key, config in URLS.items():
        print("Downloading", key)
        download_file(config["download"], config["destination"])


if __name__ == "__main__":
    import django
    django.setup()

    download_files()

    from tasks.task_runner import TaskRunner
    from analyze.setup_vectorizer import SetupVectorizer
    from analyze.update_topic_assignment import UpdateTopicAssignment

    TaskRunner.run_task(SetupVectorizer, started_by="Setup Script")
    TaskRunner.run_task(UpdateTopicAssignment, started_by="Setup Script")
