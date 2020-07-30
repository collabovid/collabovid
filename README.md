

# Collabovid

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
- [Cvid Toolbox](#CvidToolbox)
- [Team](#team)
- [FAQ](#faq)
- [License](#license)

## Installation

    # Run all commands from project root directory
    
    pip install -e collabovid-shared
    
    # Remove possibly existing database
    rm -f db.sqlite3
    
    # Install required packages
    pip install -r requirements.txt
Even though Django supports multiple database systems, some of our features rely on PostgreSQL. Therefore we recommend installing PostgreSQL on your system.
    
    # Neceassary Environment Variables
    export DJANGO_SETTINGS_MODULE=web.settings
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
                
The task can now be called from the command line, e.g.
    
    # arg2 is automatically converted to a boolean flag
    python component/run_task.py -u username my-task --arg1 Value --arg2
            

It is also possible to execute a task from code.


### Scrape
For further information look at the [README](scrape/README.md).

### Search
For further information look at the [README](search/README.md).

### Web

For further information look at the [README](web/README.md).

## Cvid Toolbox

## Team

Currently our team consists of 5 computer science students from Germany.
More details can be found on the [about page](https://www.collabovid.org/about).
 
## FAQ

The FAQ's can be found on the [website](https://www.collabovid.org/about).

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
- **[GPL-3.0 license](https://www.gnu.org/licenses/gpl-3.0.de.html)**
- Copyright 2020 © Collabovid