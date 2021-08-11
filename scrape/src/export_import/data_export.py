import getpass
import io
import json
import os
import tarfile
from datetime import datetime, timedelta
from timeit import default_timer as timer

import requests
from django.conf import settings

from data.models import (
    AuthorNameResolution,
    CategoryMembership,
    DeleteCandidate,
    GeoLocationMembership,
    GeoNameResolution,
    IgnoredPaper,
)


class DataExport:
    """
    Export database content to a .tar.gz file.
    """
    EXPORT_VERSION = 6

    @staticmethod
    def download_image(url):
        response = requests.get(url, stream=True)
        if not response.ok:
            return None
        else:
            return io.BytesIO(response.content)

    @staticmethod
    def _export_geo_name_resolutions():
        return [{"source_name": resolution.source_name, "target_geonames_id": resolution.target_geonames_id}
                for resolution in GeoNameResolution.objects.all()]

    @staticmethod
    def _export_ignored_papers():
        return [paper.doi for paper in IgnoredPaper.objects.all()]

    @staticmethod
    def _export_delete_candidates():
        return [{"doi": candidate.paper.doi, "type": candidate.type,
                 "fp": candidate.false_positive, "score": candidate.score}
                for candidate in DeleteCandidate.objects.all()]

    @staticmethod
    def _export_author_resolutions():
        resolutions = []
        for res in AuthorNameResolution.objects.all():
            target_fname = res.target_author.first_name if res.target_author else None
            target_lname = res.target_author.last_name if res.target_author else None
            resolutions.append({"source_fname": res.source_first_name, "source_lname": res.source_last_name,
                                "target_fname": target_fname, "target_lname": target_lname})
        return resolutions

    @staticmethod
    def export_data(queryset, out_dir, export_images=True, log=print):
        """
        Exports database data in json format and preview images to a tar.gz archive.
        Returns the path to the newly created archive.
        """
        start = timer()

        authors = {}
        paperhosts = {}
        journals = {}
        categories_ml = {}
        locations = {}
        papers = []

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        time = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M")
        filename = f"export_{time}_{getpass.getuser()}.tar.gz"
        path = f"{out_dir}/{filename}"
        json_path = f"{out_dir}/data.json"

        log(f"Create archive \"{path}\"")
        image_id_counter = 0
        try:
            with tarfile.open(path, "w:gz") as tar:
                for paper in queryset:
                    if paper.host_id not in paperhosts:
                        paperhosts[paper.host_id] = {"name": paper.host.name}

                    for author in paper.authors.all():
                        if author.pk not in authors:
                            authors[author.pk] = {
                                "lastname": author.last_name,
                                "firstname": author.first_name,
                            }

                    if paper.journal and paper.journal not in journals:
                        journals[paper.journal_id] = {"name": paper.journal.name}

                    for category in paper.categories.all():
                        if category.model_identifier not in categories_ml:
                            categories_ml[category.model_identifier] = {"name": category.name,
                                                                        "description": category.description,
                                                                        "color": category.color}
                    for location in paper.locations.all():
                        if location.pk not in locations:
                            location_info = {"geonames_id": location.geonames_id, "name": location.name,
                                             "alias": location.alias, "latitude": location.latitude,
                                             "longitude": location.longitude}
                            if location.is_country:
                                country = location.geocountry
                                location_info["type"] = "country"
                                location_info["alpha_2"] = country.alpha_2
                            else:
                                city = location.geocity
                                location_info["type"] = "city"
                                location_info["country_id"] = city.country.pk
                                #  We need to export the city's country here as well, if it is not already
                                #  in the list. Can happen that this country is not added (because not referenced
                                #  from anywhere else (from no paper directly).
                                citys_country = city.country
                                if citys_country.pk not in locations:
                                    locations[citys_country.pk] = {"geonames_id": citys_country.geonames_id,
                                                                   "name": citys_country.name,
                                                                   "alias": citys_country.alias,
                                                                   "latitude": citys_country.latitude,
                                                                   "longitude": citys_country.longitude,
                                                                   "type": "country",
                                                                   "alpha_2": citys_country.alpha_2}
                            locations[location.pk] = location_info

                    paper_data = {
                        "doi": paper.doi,
                        "title": paper.title,
                        "abstract": paper.data.abstract,
                        "author_ids": [author.pk for author in paper.ranked_authors],
                        "content": paper.data.content if paper.data else None,
                        "published_at": datetime.strftime(paper.published_at, "%Y-%m-%d")
                        if paper.published_at
                        else None,
                        "paperhost_id": paper.host_id,
                        "version": paper.version,
                        "covid_related": paper.covid_related,
                        "url": paper.url,
                        "pdf_url": paper.pdf_url,
                        "is_preprint": paper.is_preprint,
                        "image": None,
                        "last_scrape": datetime.strftime(
                            paper.last_scrape, "%Y-%m-%d %H:%M:%S"
                        )
                        if paper.last_scrape
                        else None,
                        "datasource_id": paper.data_source_value,
                        "pubmed_id": paper.pubmed_id,
                        "journal_id": paper.journal.pk if paper.journal else None,
                        "category_memberships": [{"identifier": c.model_identifier,
                                                  "score": CategoryMembership.objects.get(
                                                      category__model_identifier=c.model_identifier, paper=paper).score}
                                                 for c in paper.categories.all()],
                        "locations": [{"id": loc.pk,
                                       "state": GeoLocationMembership.objects.get(paper=paper,
                                                                                  location__id=loc.pk).state,
                                       "word": GeoLocationMembership.objects.get(paper=paper,
                                                                                 location__id=loc.pk).word}
                                      for loc in paper.locations.all()],
                        "location_modified": paper.location_modified,
                        "scrape_hash": paper.scrape_hash,
                        "visualized": paper.visualized,
                        "vectorized": paper.vectorized,
                        "manually_modified": paper.manually_modified
                    }

                    if export_images and paper.preview_image and paper.preview_image.path:
                        image_path = f"thumbnails/{image_id_counter}.jpg"
                        if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
                            tar.add(paper.preview_image.path, arcname=f"thumbnails/{image_id_counter}.jpg")
                            image_id_counter += 1
                            paper_data['image'] = image_path
                        elif settings.DEFAULT_FILE_STORAGE == 'storage.custom_storage.MediaStorage':
                            image = DataExport.download_image(paper.preview_image.name)
                            if image:
                                tarinfo = tarfile.TarInfo(name=f"thumbnails/{image_id_counter}.jpg")
                                tarinfo.size = len(image.getbuffer())
                                tar.addfile(tarinfo, fileobj=image)
                                image_id_counter += 1
                                paper_data['image'] = image_path

                    papers.append(paper_data)

                geo_name_resolutions = DataExport._export_geo_name_resolutions()
                ignored_papers = DataExport._export_ignored_papers()
                delete_candidates = DataExport._export_delete_candidates()
                author_resolutions = DataExport._export_author_resolutions()

                data = {
                    "export_version": DataExport.EXPORT_VERSION,
                    "authors": authors,
                    "paperhosts": paperhosts,
                    "papers": papers,
                    "journals": journals,
                    "categories_ml": categories_ml,
                    "locations": locations,
                    "geo_name_resolutions": geo_name_resolutions,
                    "ignored_papers": ignored_papers,
                    "delete_candidates": delete_candidates,
                    "author_resolutions": author_resolutions
                }

                with open(json_path, "w") as file:
                    json.dump(data, file, indent=4)

                tar.add(json_path, arcname="data.json")
        except Exception as ex:
            # Remove tar archive, if export was not successful
            if os.path.exists(path):
                os.remove(path)

            raise ex
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

        end = timer()

        log(f"Finished export (version {DataExport.EXPORT_VERSION}) in {timedelta(seconds=end - start)}")
        log("Exported")
        log(f"\t{len(paperhosts)} paperhosts")
        log(f"\t{len(authors)} authors")
        log(f"\t{len(papers)} articles")
        log(f"\t{len(categories_ml)} ML categories")
        log(f"\t{len({id: l for id, l in locations.items() if l['type'] == 'country'})} countries")
        log(f"\t{len({id: l for id, l in locations.items() if l['type'] == 'city'})} cities")
        log(f"\t{len(geo_name_resolutions)} geo name resolutions")
        log(f"\t{len(author_resolutions)} author name resolutions")
        log(f"\t{len(ignored_papers)} ignored papers")
        log(f"\t{len(delete_candidates)} delete candidates")
        log(f"\t{image_id_counter} images")
        log("Archive size: {0} MB".format(round(os.stat(path).st_size / (1000 ** 2), 2)))

        return filename
