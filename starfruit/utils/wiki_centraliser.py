import requests
import pprint as pp
import json

import requests
from qwikidata.sparql import return_sparql_query_results
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem

def get_dbpedia_as_wiki(dbpedia_link,epr = "http://dbpedia.org/sparql",f='application/json'):
    entity_name = dbpedia_link[dbpedia_link.rfind('/')+1:]
    q = f"""
    SELECT  ?wikidata_concept
    WHERE {{dbr:{entity_name} owl:sameAs ?wikidata_concept}}
    """
    try:
        params = {'query': q}
        resp = requests.get(epr, params=params, headers={'Accept': f})
        res_list = json.loads(resp.text)["results"]["bindings"]
        for res in res_list:
            #print(res['wikidata_concept'])
            value = res['wikidata_concept']['value']
            if "http://www.wikidata.org" in value:
                entity_name = get_entity_from_wiki_link(value)
                wd_id = value[value.rfind('/')+1:]
                return (entity_name, wd_id)
        return (None,None)
    except Exception as e:
        return (None,None)
    

def get_geoname_as_wiki(geo_link):
    geo_id = geo_link[geo_link[:geo_link.rfind('/')].rfind('/'):].replace('/','')
    sparql_query = f"""
    SELECT ?place ?placeLabel WHERE
    {{
    ?place wdt:P1566 "{geo_id}" . 
    SERVICE wikibase:label {{
          bd:serviceParam wikibase:language "en" .
      }}
    }}
    """
    place_name = None
    wiki_link = None
    try:
        res_raw = return_sparql_query_results(sparql_query)
        if 'results' in res_raw:
            if 'bindings' in res_raw['results']:
                res_list = res_raw['results']['bindings']
                for res in res_list:
                    place_block = res['place']
                    placeLabel_block = res['placeLabel']
                    if "xml:lang" in placeLabel_block:
                        lang = placeLabel_block['xml:lang']
                        if lang == 'en':
                            place_name = placeLabel_block['value']
                            wiki_link = place_block['value']
        return (place_name, wiki_link[wikilink.rfind('/')+1:])
    except Exception as e:
        return (None,None)
    
#print(get_geoname_as_wiki("http://sws.geonames.org/2995469/"))

def get_entity_from_wiki_id(wiki_id):
    q42_dict = get_entity_dict_from_api(wiki_id)
    return q42_dict['labels']['en']['value']

def get_entity_from_wiki_link(wiki_link):
    wiki_id = wiki_link[wiki_link.rfind('/')+1:]
    q42_dict = get_entity_dict_from_api(wiki_id)
    return q42_dict['labels']['en']['value']