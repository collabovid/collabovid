def run(output):
    import os
    import requests
    from analyze import get_analyzer

    VECTORIZER_DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/s/rlx75dmyl4rn9v2/vectorizer.csv'
    LDA_DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/s/7aaoq40qgiagsrb/lda.csv'

    VECTORIZER_PATH = os.path.join(os.getcwd(), 'analyze/res/vectorizer.pkl')
    LDA_PATH = os.path.join(os.getcwd(), 'analyze/res/lda.pkl')

    def download_file(down, path):
        if os.path.exists(path):
            output(path, "exists, skipping...")
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            r = requests.get(down)
            with open(path, 'wb') as f:
                f.write(r.content)

    download_file(VECTORIZER_DOWNLOAD_URL, VECTORIZER_PATH)
    download_file(LDA_DOWNLOAD_URL, LDA_PATH)

    analyzer = get_analyzer()
    analyzer.save_paper_matrix()
    analyzer.assign_to_topics()

    output("Assigned lda to topics")


if __name__ == "__main__":
    import django
    django.setup()

    run(print)