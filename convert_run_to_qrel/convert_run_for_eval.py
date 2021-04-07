import argparse
import json
import requests
import pprint
import pywikibot
from qwikidata.linked_data_interface import get_entity_dict_from_api
import pickle
import re

def get_entity_from_wiki_id(wiki_id):
    wikidata_dict = get_entity_dict_from_api(wiki_id)
    wikidata_labels = wikidata_dict["labels"]
    en_label = wikidata_labels.get("en", "")
    if en_label != "":
        return en_label["value"]
    return ""

def find_all_mentions(text, entity):
    output = []
    entity_len = len(entity)
    try:
        start_indices = [m.start() for m in re.finditer(entity, text)]
        for start_index in start_indices:
            output.append([start_index, start_index + entity_len])
        return output
    except:
        print(entity)
        return []

def convert_wikipedia_to_wikidata(wp_name):
    '''
    item = wp_name.replace(" ","%20").replace("_","%20")
    response_json = requests.get(f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&titles={item}").json()
    page_info = response_json["query"]["pages"]
    first_page = list(page_info.keys())[0]
    try:
        wikidata_id = page_info[first_page]["pageprops"]["wikibase_item"]
    except:
        pprint.pprint(response_json)
        return ""
    return wikidata_id

    '''
    wp_name_processed = wp_name.replace("_"," ")
    site = pywikibot.Site("en", "wikipedia")
    try:
        page = pywikibot.Page(site, wp_name_processed)
        item = pywikibot.ItemPage.fromPage(page)
        wd_id = item.getID()
    except:
        wd_id = ""
    return wd_id
    

    
def to_trec(input_file, output_folder, run_name, clean_nil):
    output_file_entity_ids = open(f"{output_folder}{run_name}_ids.csv","w")
    output_file_entity_labels = open(f"{output_folder}{run_name}_labels.csv","w")
    
    with open(input_file) as f:
        e2e_run_json = json.load(f)
    f.close()
    
    for doc_id, entity_list in e2e_run_json.items():
        unique_set = []
        rank = 1
        for entity in entity_list:
            predicted_entity_link = entity["pred"]
            predicted_wikidata_id = convert_wikipedia_to_wikidata(predicted_entity_link)
            if predicted_wikidata_id != "":
                predicted_wikidata_label = get_entity_from_wiki_id(predicted_wikidata_id)
                if predicted_wikidata_label == "":
                    if clean_nil is True:
                        continue
                    predicted_wikidata_id = predicted_entity_link + "/WP"
                    predicted_wikidata_label = predicted_wikidata_id
            else:
                if clean_nil is True:
                    continue
                predicted_wikidata_id = predicted_entity_link + "/WP"
                predicted_wikidata_label = predicted_wikidata_id
            predicted_wikidata_id = predicted_wikidata_id.replace(" ","_")
            if predicted_wikidata_id in unique_set:
                continue
            
            unique_set.append(predicted_wikidata_id)
            scores = entity["scores"]
            all_links = entity["links"]
            for i in range(len(all_links)):
                if all_links[i] == predicted_entity_link:
                    score = scores[i]
                    break
            output_file_entity_ids.write(f"{doc_id}\tQ0\t{predicted_wikidata_id}\t{rank}\t{score}\tSTANDARD\n")
            output_file_entity_labels.write(f"{doc_id}\tQ0\t{predicted_wikidata_label}\t{rank}\t{score}\tSTANDARD\n")
            rank += 1
    output_file_entity_ids.close()
    output_file_entity_labels.close()

def to_genre(input_file, output_folder, run_name, corpus_dict, clean_nil):
    output_file_entity_ids = open(f"{output_folder}{run_name}_ids_genre_format.pickle","wb")
    output_file_entity_labels = open(f"{output_folder}{run_name}_labels_genre_format.pickle","wb")
    
    output_list_ids = []
    output_list_labels = []
    
    with open(input_file) as f:
        e2e_run_json = json.load(f)
    f.close()
    
    for doc_id, entity_list in e2e_run_json.items():
        doc_content = corpus_dict[doc_id]
        unique_set = []
        rank = 1
        for entity in entity_list:
            predicted_entity_mention = entity["mention"]
            predicted_entity_link = entity["pred"]
            scores = entity["scores"]
            all_links = entity["links"]
            for i in range(len(all_links)):
                if all_links[i] == predicted_entity_link:
                    score = scores[i]
                    break
            all_mentions = find_all_mentions(doc_content, predicted_entity_mention)
            
            predicted_wikidata_id = convert_wikipedia_to_wikidata(predicted_entity_link)
            if predicted_wikidata_id != "":
                predicted_wikidata_label = get_entity_from_wiki_id(predicted_wikidata_id)
                if predicted_wikidata_label == "":
                    if clean_nil is True:
                        continue
                    predicted_wikidata_id = predicted_entity_link + "/WP"
                    predicted_wikidata_label = predicted_wikidata_id
            else:
                if clean_nil is True:
                    continue
                predicted_wikidata_id = predicted_entity_link + "/WP"
                predicted_wikidata_label = predicted_wikidata_id
            predicted_wikidata_id = predicted_wikidata_id.replace(" ","_")
            if predicted_wikidata_id in unique_set:
                continue
            
            unique_set.append(predicted_wikidata_id)
            
            for mention_span in all_mentions:
                output_list_ids.append((doc_id, mention_span[0], mention_span[1], predicted_wikidata_id))
                output_list_labels.append((doc_id, mention_span[0], mention_span[1], predicted_wikidata_label))
                
    pickle.dump(output_list_ids, output_file_entity_ids)
    pickle.dump(output_list_labels, output_file_entity_labels)
    output_file_entity_ids.close()
    output_file_entity_labels.close()
            
                

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_run_file')
    parser.add_argument('output_folder_path', help='output folder to write out, not filename, should also end in /')
    parser.add_argument('corpus_path', help='load the relevant corpus json here')
    parser.add_argument('output_format', help='either trec or genre format')
    parser.add_argument('run_name', help='label of model being used, can be also named qrel')
    parser.add_argument('--clean_nil', type=bool, default=True)
    
    args = parser.parse_args()
    
    input_run_file = args.input_run_file
    output_folder_path = args.output_folder_path
    if output_folder_path[-1:] != "/":
        output_folder_path += "/"
    corpus_path = args.corpus_path
    with open(corpus_path) as f:
        corpus_dict = json.load(f)
    f.close()
    output_format = args.output_format
    run_name = args.run_name
    clean_nil = args.clean_nil
    
    if output_format == "trec":
        to_trec(input_run_file, output_folder_path,run_name, clean_nil)
    elif output_format == "genre":
        to_genre(input_run_file, output_folder_path, run_name, corpus_dict, clean_nil)
    else:
        print("error")