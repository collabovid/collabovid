# covid19-publications

## Installation

    # Run all commands from project root directory
    
    # Remove existing database
    rm -f db.sqlite3
    
    # Install required packages
    pip install -r requirements.txt

    # Migrate database scheme to current state
    python3 manage.py migrate
    
    # Load database and PDF thumbnails
    python3 manage.py loaddata db-yyyymmddhhmm
    python3 manage.py loaddata topics
 
    # Run setup scripts
    export DJANGO_SETTINGS_MODULE=covid19_publications.settings
    python3 setup/image_downloader.py
    python3 setup/lda_setup.py