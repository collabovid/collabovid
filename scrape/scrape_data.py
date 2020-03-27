import json
import requests

def get_data():
    biorxiv_corona_json = 'https://connect.biorxiv.org/relate/collection_json.php?grp=181'

    response = requests.get(biorxiv_corona_json)
    data = json.loads(response.text)['rels']

    return data