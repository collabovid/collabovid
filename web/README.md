# Web
The web component contains the website (frontend) code along
with some controllers and handlers to communicate with the other services.


### Django-Pipeline
In order to reduce loading times, we use the [django-pipeline](https://django-pipeline.readthedocs.io/en/latest/)
module that combines an minifies our static css and js files.
The *assets* folder contains third-party libraries that are used
in the project. The definitions can be found in `web/pipeline.py`.

## Core
The *core* app contains almost all views that can be found on the website.
It provides the base template and all necessary static files as well as some 
useful templatetags that are used throughout the project.

See below on how to use the base template:

    {% extends "core/base.html" %}
    {% block content %}
        <div class="gradient-header pb-0 overflow-hidden">
            <!-- Content of the (blue) header portion --->
            
            <!-- Include the following for a rounded bottom --->
            {% include 'core/partials/_rounded_bottom.html' %}
        </div>
    
        <!-- Content of the site --->
        
    {% endblock %}
    
    {% block script %}
       <!-- Will be placed at the end of the page after all js libs were included --->
    {% endblock %}
    
    {% block css %}
        <!-- Will be placed in the <head> portion of the website --->
    {% endblock $}
    
### Statistics
Some pages need statistics of a given set of papers or categories to 
display them in a chart or table. The `statistics`
package includes several classes that compute certain statistics
and convert them into JSON format that can be processed by the Javascript
in the frontend.

## Search
As the search functionality is a big part of the website, we decided to
define a custom app that provides views and models that are used for search.

### Tagify

For certain filters like authors, journals or locations we want
to allow the user to quick search and display suggestions. 
We included (and modified) the [Tagify](https://github.com/yairEO/tagify)
library. For every model, we have created a `TagifySearchable` subclass
that converts the model into a json. Along with the `tagify_helper`
templatetag, we have an easy to extend interface for new search filters like this.

### Request Helper

The request helper module contains helper classes that communicate 
with the search service. Note that for the classic search, the search
service will return the dois for a *single* page and not the complete
result set. The custom `FakePaginator` class allows us to use the single
 page result set as if it would contain the complete search result. 

### Queries

For further analysis of our users behaviour, we opted to save the 
queries that were submitted to our server. 

---
**Note**

Queries will only be saved to the database when the user is not logged in, e.g. we won't log our own queries.

---

Search queries are saved into the `SearchQuery` model which contains a single
field that stores the query as a JSON. This allows us to extend the search
with new filters and variations without changing our query model.

## Dashboard

The dashboard app contains front- and backend code for the admin panel
of the website. Once logged in, we are able to start and overview tasks 
that are provided by other services, manipulate the papers in our database,
create/change topics, edit location and author information of the papers,
see statistics on recent search queries and detect papers that were not written
in english language.

The code of the dashboard is somewhat straightforward. The base template 
for the dashboard can be found in `dashboard/templates/base.html` and is
very similar to the one used in `core`.
