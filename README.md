

# Collabovid

![](https://img.shields.io/badge/-docker-blue)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![](https://img.shields.io/github/repo-size/michip/collabovid)
![](https://img.shields.io/github/languages/count/michip/collabovid)
![](https://img.shields.io/github/issues-closed/michip/collabovid)
![](https://img.shields.io/github/commit-activity/m/michip/collabovid)
![](https://img.shields.io/twitter/follow/collabovid?style=social)

---

Researchers from all over the world are working hard on the investigation of the SARS-CoV-2 
virus and the impact of the disease, resulting in many new publications in journals or on
so-called _preprint versions_ such as [medRxiv](https://connect.medrxiv.org/relate/content/181) or [bioRxiv](https://connect.biorxiv.org/relate/content/181). 
However, time is short and thus, a good interface to access, 
sort and classify the huge amount of preprint papers is needed.
Several times a day, Collabovid searches for newly published research articles on different well-known servers. 
Apart from meta information, the content of some articles can be extracted. Machine learning techniques are used to analyze the publications and make them semantically searchable and comparable.
This repository contains the source code of the Collabovid project.


## Table of Contents


- [Installation](#installation)
- [Components](#components)
- [CVID CLI](#CvidToolbox)
- [Team](#team)
- [FAQ](#faq)
- [License](#license)

## Installation

    # Run all commands from project root directory
    
    pip install -e collabovid-shared
    pip install -e collabovid-store
    
    # Remove possibly existing database
    rm -f db.sqlite3
    
    # Install required packages
    pip install -r web/requirements.txt
    pip install -r search/requirements.txt
    pip install -r scrape/requirements.txt
    
Even though Django supports multiple database systems, some of our features rely on PostgreSQL. Therefore we recommend installing PostgreSQL on your system.
    
    # Neceassary Environment Variables
    export DJANGO_SETTINGS_MODULE=web.settings_dev
    export RDS_DB_NAME=db
    export RDS_USERNAME=xxx
    export RDS_PASSWORD=xxx
    export RDS_HOSTNAME=localhost
    export RDS_PORT=xxxx
    
    # Migrate database scheme to current state
    python3 web/manage.py migrate
    
    # Load database
    python3 web/manage.py loaddata lit-covid-categories
    python3 web/manage.py loaddata initial_nameresolutions
 
## Components

Collabovid requires multiple subcomponents to run on independent servers.
To allow every component to operate on common models and provide some
functionality to all servers
the *collabovid-shared* and *collabovid-store* packages are used.

* *collabovid-shared* contains shared settings (collabovid_settings, storage), 
shared models (data), handlers for the geonames database (geolocations)
as well as helpers for running tasks.

* *collabovid-store* contains utility functions that allow other components 
to work with files that are stored in an S3 bucket.

#### Docker

Coming soon..

#### Tasks

Tasks are classes that run certain code that can be executed from
anywhere. To create a task one must include the base class. To register
a tasks so that it is callable in- and outside of its component the task
must be registered

    from tasks.definitions import Runnable, register_task
    
    @register_task
    class MyTask(Runnable):
    
        def __init__(self, arg1: str = '', arg2: bool = False, *args, **kwargs):
            #  Make sure to annotate the arguments. They are parsed automatically
            super(MyTask, self).__init__(*args, **kwargs)
            self._arg1 = arg1
            self._arg2 = arg2

        @staticmethod
        def task_name():
            return "my-task"  # Identifier is used when the task is called
           
        def run(self):  # Is called when the task is executed
            self.log("Test")  # Logs are saved to the database automatically
            
            for i in self.progress(range(100)):  #  Progress will be set automatically while iterating
                pass
                
To register a task and make it visible to all other components, execute the following CVID CLI command:

    cvid collect-tasks

The task can now be called from the command line, e.g.
    
    # arg2 is automatically converted to a boolean flag
    python component/run_task.py -u username my-task --arg1 Value --arg2
            

It is also possible to execute a task from code or via the admin dashboard at the `/dashboard/tasks` url.


### Scrape

The scrape app is responsible for keeping the article data up-to-date. On the one hand,
the app provides interfaces between the external data sources and our internal database.
On the other hand, different tools are provided, concerning the maintenance of the data.

For further information look at the [README](scrape/README.md).

### Search
For further information look at the [README](search/README.md).

### Web

The web component contains the website (frontend) code along
with some controllers and handlers to communicate with the other services.

For further information look at the [README](web/README.md).

## CVID CLI

The command line interface contains useful commands that help us to deploy
collabovid to an Kubernetes cluster as well as up-/downloading data, models, paper matrices
and resources to an S3 bucket so that they can be distributed among the developers
and the server. If files are uploaded to S3 they are automatically downloaded by the *sync-daemon*.
This allows us to exchange such resources without deploying a new server version
as well as operating on the newest dataset when developing new features.

### Installation

To install the CVID CLI toolbox run the following command from the root directory of this 
repository
    
    pip install -e cli
    
We recommend using the `-e` option so that updates to the tool are automatically applied
without the need to reinstall the package. Afterwards the command `cvid` can be executed 
from anywhere. Note that you need to make sure that the folder contains the
 `cvid-config.json` file with your configuration.


### Configuration

The CVID CLI needs to be configured according to your needs. The configuration
contains options for Kubernetes/Docker as well as credentials for certain resources
like the S3 Bucket. To see the default values for all possible options see `cli/cvid/defaults.json`.

A sample configuration might look like this:

    {
        "env": "prod", // Current Environment (will be changed when executing cvid use)
        "envs": { // Configurations for each environment
            "dev": {
                "optionFiles": [
                    "imagePullPolicy_Never.yaml", // Sets the image pull policy to never
                    "no-registry.yaml", // We don't have a local registry
                    "searchMemoryRequirements_Zero.yaml" // Resets the memory requirements of search
                ],
                "kubectl-context": "docker-desktop" // Kubernetes context for (local) deployment
            },
            "prod": {
                "registry": "XXXXXXX.amazonaws.com", // S3 registry configuration
                "s3_access_key": "XXXXXXX",
                "s3_secret_access_key": "XXXXXXX",
                "s3_endpoint_url": "https://s3.XXXXX.amazonaws.com",
                "s3_bucket_name": "XXXXXXX",
                "optionFiles": [ // Option file locationsab are relative to k8s/options
                    "secrets/prod.yaml", // Using prod secrets
                    "imagePullPolicy_Always.yaml" // Sets image pull policy to always
                ],
                "kubectl-context": "prod-cluster-name" // Kubernetes context for deployment
            },
            "test": {
                "registry": "XXXXXXX.amazonaws.com", // S3 test registry configuration
                "s3_access_key": "XXXXXXX",
                "s3_secret_access_key": "XXXXXXX",
                "s3_endpoint_url": "https://s3.XXXXX.amazonaws.com",
                "s3_bucket_name": "XXXXXXX",
                "optionFiles": [
                    "secrets/test.yaml", // Using test secrets
                    "imagePullPolicy_Always.yaml" // Sets image pull policy to always
                ],
                "kubectl-context": "test-cluster-name" // Kubernetes context for test deployment
            }
        }
    }


### Commands
For details on the specific commands use the `--help` option.
    
    $ cvid --help
    usage: cvid [-h]
                {use,build,push,cluster,jobs,aws-registry-login,cronjobs,collect-tasks,release,version,configure-k8s,register,models,paper-matrices,share-config,resources,data}
                ...
    
    positional arguments:
      {use,build,push,cluster,jobs,aws-registry-login,cronjobs,collect-tasks,release,version,configure-k8s,register,models,paper-matrices,share-config,resources,data}
        use                 Specify which environment to use. Options are:
                            dict_keys(['dev', 'prod', 'test'])
        build               Build a repository and tag it with the current
                            version.
        push                Pushes the image of a service to the registry defined
                            by the current environment
        cluster             Run Commands on the cluster
        jobs                Manage Kubernetes jobs
        aws-registry-login  Login the docker client into the aws registry
        cronjobs            Manage Kubernetes cronjobs
        collect-tasks       Collects all tasks from scrape,search
        release             Full build, push and cluster update
        version             Retrieves the currently running version in the cluster
        configure-k8s       Manage Kubernetes jobs
        register            Adds user to the cluster
        models              Upload/download models
        paper-matrices      Upload/download paper matrices to s3
        share-config        Share release config with others
        models              Upload/download models
        paper-matrices      Upload/download paper matrices to s3
        resources           Upload/download resources
        data                Upload archive to S3 or download from S3 to local
                            storage. Delete remote exports (delete-remote)
    
    optional arguments:
      -h, --help            show this help message and exit


## Deployment

To deploy the servers to a Kubernetes cluster configure the CVID CLI as described before.
In our sample `cvid-config.json`, we added a `secrets/prod.yaml` option to our
production environment. Such a file overwrites values of the kubernetes configuration that should
be kept secret and might look similar to this:

    apiVersion: v1
    kind: Service
    metadata:
      name: postgres
    spec:
      externalName: XXXXX // Set postgres url, e.g. collabovid-db-url.com
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: web
      annotations:
        service.beta.kubernetes.io/aws-load-balancer-ssl-cert: XXXXX  // Set arn:aws-certificate
    ---
    kind: PersistentVolume
    apiVersion: v1
    metadata:
      name: elasticsearch-pv
    spec:
      awsElasticBlockStore:
        volumeID: XXXXX // Set volume ID
        

Moreover, one has to set the environment variables for the production server
in `k8s/overlays/prod/envs`:

1. `k8s/overlays/prod/envs/shared.env` (shared across all services)
    
        RDS_DB_NAME=XXXXX // Postgres configuration
        RDS_USERNAME=XXXXX
        RDS_PASSWORD=XXXXX
        RDS_HOSTNAME=postgres.default.svc.cluster.local
        RDS_PORT=XXXXX
        AWS_ACCESS_KEY_ID=XXXXX // AWS S3 configuration
        AWS_SECRET_ACCESS_KEY=XXXXX
        AWS_STORAGE_BUCKET_NAME=XXXXX
        AWS_S3_REGION_NAME=XXXXX
        AWS_S3_HOST=s3.amazonaws.com
        AWS_S3_PROTOCOL=https
        REGISTRY=XXXXX // Kubernetes registry url
        SEARCH_MODELS_HOST_PATH=/opt/models // Necessary paths for resources, models etc.
        PAPER_MATRIX_BASE_DIR=/models/paper_matrix
        MODELS_BASE_DIR=/models
        RESOURCES_HOST_PATH=/opt/resources
        RESOURCES_BASE_DIR=/resources
        ELASTICSEARCH_URL=http://elasticsearch.default.svc.cluster.local:9200 // Elasticsearch url in cluster
        USING_ELASTICSEARCH=1 // Enables elasticsearch in every component
        TOPICS_FILE_URL=XXXXX // Url to a topics.json for the ingest-topics job

2. `k8s/overlays/prod/envs/daemon.env`
    
        AWS_BASE_DIR=xy // can be empty, base dir in aws s3 bucket
    
3. `k8s/overlays/prod/envs/scrape.env`
    
        DJANGO_SETTINGS_MODULE=scrape.settings_prod // Production settings
        ALLOW_IMAGE_SCRAPING=1 // Enables image scraping (from pdfs)
        ALTMETRIC_KEY=XXXXX // Altmetric API Key
        
4. `k8s/overlays/prod/envs/search.env`

        SECRET_KEY=XXXXX // Django secret key
        DJANGO_SETTINGS_MODULE=search.settings_prod // Production settings
        
5. `k8s/overlays/prod/envs/web.env`

        SECRET_KEY=XXXXX // Django secret key
        SUPERUSER_USERNAME=XXXXX // Superuser configuration is set when the create superuser job is executed
        SUPERUSER_EMAIL=XXXXX
        SUPERUSER_PASSWORD=XXXXX
        ALLOWED_TEST_HOST=XXXXX // Add a custom host to allowed hosts (for testing)
        DJANGO_SETTINGS_MODULE=web.settings_prod // Production settings
        DATA_PROTECTION_URL=XXXXX/data_protection_declaration.md // Link to the data protection declaration
        IMPRINT_URL=XXXXX/imprint.md // Link to the imprint


After all variables are set execute the following commands to release a new version:

Specify environment

    cvid use prod
    
Optional: log into aws
    
    cvid aws-registry-login --region xxx

Build all docker images, push them to the registry and apply them in the cluster

    cvid release
    

## Team

Currently our team consists of 5 computer science students from Germany.
More details can be found on the [about page](https://www.collabovid.org/about).
 
## FAQ

The FAQ's can be found on the [website](https://www.collabovid.org/about).

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
- **[GPL-3.0 license](https://www.gnu.org/licenses/gpl-3.0.de.html)**
- Copyright 2020 © Collabovid