if __name__ == '__main__':
    import django
    django.setup()

    from data.models import Paper, DataSource

    print("Set all null values in datasource field to medRxiv datasource")
    papers = Paper.objects.filter(data_source=None)
    datasource, _ = DataSource.objects.get_or_create(name=DataSource.MEDBIORXIV_DATASOURCE_NAME)
    for paper in papers:
        paper.data_source = datasource
        paper.save()
