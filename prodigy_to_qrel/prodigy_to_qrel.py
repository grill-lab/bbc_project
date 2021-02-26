import json
import argparse
import re
import pickle
from qwikidata.linked_data_interface import get_entity_dict_from_api

error_list = []
to_run_dict = {}
annotations_dict = {}

def get_entity_from_wiki_id(wiki_id):
    q42_dict = get_entity_dict_from_api(wiki_id)
    if 'en' not in q42_dict['labels']:
        print(wiki_id)
        print(q42_dict)
        print("________________________")
        return None
    return q42_dict['labels']['en']['value']

def find_all_mentions(text, entity):
    output = []
    entity_len = len(entity)
    start_indices = [m.start() for m in re.finditer(entity, text)]
    for start_index in start_indices:
        output.append([start_index, start_index + entity_len])
    return output

def convert_prodigy_to_qrel(prodigy_file, clean_nil):
    annotation_list = []
    with open(prodigy_file) as f:
        for line in f:
            annotation = json.loads(line)
            annotation_list.append(annotation)
    f.close()
    
    unique_annotation_set = []
    #output_file = open(f"{output_folder}qrels.json","w")
    for annotation in annotation_list:
        
        text = annotation["text"]
        start_span = annotation["spans"][0]["start"]
        end_span = annotation["spans"][0]["end"]
        entity = text[start_span:end_span]
        all_mentions = find_all_mentions(text,entity)
        
        target = text[text.rfind(" ")+1:]
        if "programmes" in target:
            target_id = target[33:]
        elif "sounds/play/" in target:
            target_id = target[34:]
        else:
            if ".co.uk" in target:
                target_id = "urn:bbc:content:assetUri:" + target[22:]
            else:
                target_id = "urn:bbc:content:assetUri:" + target[20:]
        
        if target_id not in to_run_dict:
            to_run_dict[target_id] = text
        
        if len(annotation["accept"])<1:
            error_list.append(annotation)
            continue
            
        chosen_wiki_id = annotation["accept"][0]
        if chosen_wiki_id == "not_in_kb":
            if clean_nil is True:
                continue
            chosen_wiki_id = "NIL/"+text[start_span:end_span]
            
        if chosen_wiki_id == "not_listed":
            if "custom_wikidata" not in annotation:
                error_list.append(annotation)
                continue
            custom_wiki_id = annotation["custom_wikidata"]
            if "/" in custom_wiki_id:
                chosen_wiki_id = custom_wiki_id[custom_wiki_id.rfind('/')+1:]
        if chosen_wiki_id == "not_listed" and clean_nil is True:
            continue
            
            #else:
                #chosen_wiki_id = custom_wiki_id
                #chosen_wiki_entity = get_entity_from_wiki_id(custom_wiki_id)
            #else:
                #chosen_wiki_entity = get_entity_from_wiki_link(custom_wiki_id)
        #else:
            #chosen_wiki_entity = get_entity_from_wiki_id(chosen_wiki_id)
        
        #chosen_wiki_entity = chosen_wiki_entity.replace(" ","_")
        
        if (target_id, chosen_wiki_id) in unique_annotation_set:
            continue
        unique_annotation_set.append((target_id, chosen_wiki_id))
        
        
        salience = annotation["salience_rating"]
        persona_relevance = annotation["persona_relevance"]
        link_accuracy = annotation["link_accuracy"]
        
        if target_id not in annotations_dict:
            annotations_dict[target_id] = []
        entity_dict = {
            "entity": entity,
            "id": chosen_wiki_id,
            "mentions": all_mentions,
            "salience": salience,
            "persona_relevance": persona_relevance,
            "match_type": link_accuracy
            
        }
        annotations_dict[target_id].append(entity_dict)
    #json.dump(annotations_dict, output_file)
        #output_file.write(f"{target_id}\t0\t{chosen_wiki_entity}\t1\n")
    #output_file.close()
    
def to_trec(output_folder):
    output_file = open(f"{output_folder}trec_qrel.csv","w")
    output_file_2 = open(f"{output_folder}trec_qrel_labels.csv","w")
    for doc_id, entity_list in annotations_dict.items():
        for entity in entity_list:
            entity_id = entity['id'].replace(' ','')
            if entity_id[0]=="Q":
                entity_label = get_entity_from_wiki_id(entity_id)
                if entity_label is None:
                    entity_label = entity_id
            else:
                entity_label = entity_id
            output_file.write(f"{doc_id}\t0\t{entity['id'].replace(' ','')}\t{entity['salience']}\n")
            output_file_2.write(f"{doc_id}\t0\t{entity_label}\t{entity['salience']}\n")
    output_file.close()
    output_file_2.close()

def to_genre(output_folder):
    output_list_id = []
    output_list_labels = []
    output_file_id = open(f"{output_folder}genre_format_qrel.pickle","wb")
    output_file_labels = open(f"{output_folder}genre_format_qrel_labels.pickle","wb")
    for doc_id, entity_list in annotations_dict.items():
        for entity in entity_list:
            entity_id = entity['id'].replace(' ','')
            if entity_id[0]=="Q":
                entity_label = get_entity_from_wiki_id(entity_id)
                if entity_label is None:
                    entity_label = entity_id
            else:
                entity_label = entity_id
            for mention_span in entity["mentions"]:
                output_list_id.append((doc_id, mention_span[0],mention_span[1], entity_id))
                output_list_labels.append((doc_id, mention_span[0],mention_span[1], entity_label))
    pickle.dump(output_list_id, output_file_id)
    pickle.dump(output_list_labels, output_file_labels)
    output_file_id.close()
    output_file_labels.close()
                

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_folder_path', help='output folder to write out, not filename, should also end in /')
    parser.add_argument('output_format', help='trec format or genre format')
    parser.add_argument('--clean_nil', type=bool, default=True)
    
    args = parser.parse_args()
    
    input_file_path = args.input_file
    output_folder_path = args.output_folder_path
    if output_folder_path[-1:] != "/":
        output_folder_path += "/"
    output_format = args.output_format
    clean_nil = args.clean_nil
    convert_prodigy_to_qrel(input_file_path, clean_nil)
    if output_format == 'trec':
        to_trec(output_folder_path)
    elif output_format == 'genre':
        to_genre(output_folder_path)
    else:
        print("please input correct format, either trec or genre")