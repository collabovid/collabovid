# Collabovid

Researchers from all over the world are working hard on the investigation of the SARS-CoV-2 
virus and the impact of the disease, resulting in many new publications in journals or on
so-called _preprint versions_ per day, e.g. at [medRxiv](https://connect.medrxiv.org/relate/content/181) or [bioRxiv](https://connect.biorxiv.org/relate/content/181). 
However, time is short and thus, a good interface to access, 
sort and classify the huge amount of preprint papers is needed.
Several times a day, Collabovid searches for newly published research articles on different well-known servers. Apart from meta information, the content of some articles can be extracted. Machine learning techniques are used to analyze the publications and make them semantically searchable and comparable.
## Installation

    # Run all commands from project root directory
    
    pip install -e collabovid-shared
    
    # Remove possibly existing database
    rm -f db.sqlite3
    
    # Install required packages
    pip install -r requirements.txt
Even though Django supports multiple database systems, some of our features rely on PostgreSQL. Therefore we recommend installing PostgreSQL on your system.
    
    # Neceassary Environment Variables
    export DJANGO_SETTINGS_MODULE=covid19_publications.settings
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    export RDS_DB_NAME=db
    export RDS_USERNAME=xxx
    export RDS_PASSWORD=xxx
    export RDS_HOSTNAME=localhost
    export RDS_PORT=xxxx
    
    # Migrate database scheme to current state
    python3 manage.py migrate
    
    # Load database and PDF thumbnails
    python3 manage.py loaddata lit-covid-categories
    python3 manage.py loaddata initial_nameresolutions
 
    