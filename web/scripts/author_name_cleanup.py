import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import Author
from django.db.models import Q

if __name__ == '__main__':
    authors = Author.objects.filter(Q(first_name__contains=';') | Q(first_name__contains=',') |
                                    Q(last_name__contains=';') | Q(last_name__contains=','))
    for author in authors:
        new_fname = author.first_name.replace(';', '').replace(',', '')
        new_lname = author.last_name.replace(';', '').replace(',', '')
        print(f"{author.first_name} {author.last_name} -> {new_fname} {new_lname}")
        author.first_name = new_fname
        author.last_name = new_lname
        author.save()