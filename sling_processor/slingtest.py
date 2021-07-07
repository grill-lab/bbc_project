import sling
import pprint
import json
import sys
import argparse
import os
import re

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def get_string_name_from_sling_object(item):
    if type(item) is sling.Frame:
        if "name" in item:
            return item.get("name")
        elif "is" in item:
            return item.get("is")
        elif "id" in item:
            return item.get("id")
    else:
        return item
    
def check_if_frame_wikidata_item(item):
    if "isa" in item:
        return get_string_name_from_sling_object(item.get("isa")) == "Wikidata item"
    return False

def check_if_frame_wikidata_item_2(item):
    if "name" in item:
        return True
    return False
    
def frame_to_json(frame):
    # Set up basic fields/variables
    output_json = {"name": "", 
                   "category": [], 
                   "related_entities": [], 
                   "attributes": [], 
                   "contents": "", 
                   "id": "", 
                   "related_entities_id": []}
    name = frame.name
    if type(name) is not str:
        return {}
    output_json["name"] = frame.name
    output_json["id"] = frame.id
    
    for key, value in frame:
        key_description = get_string_name_from_sling_object(key)
        if key_description == "/w/item/category":
            output_json["category"].append(get_string_name_from_sling_object(value))
            continue
        elif key_description == "BBC Things ID":
            output_json["BBC Things ID"] = get_string_name_from_sling_object(value)
        else:
            pass
        
        value_description = value
        if type(value_description) == str:
            output_json["attributes"].append([key_description, value])
            
        elif type(value_description) is sling.Frame:
            value_description = get_string_name_from_sling_object(value)
            
            if type(value_description) is str:
                output_json["attributes"].append([key_description, value_description])
            elif type(value_description) is sling.Frame:
                if check_if_frame_wikidata_item_2(value_description):
                    output_json["related_entities"].append(value_description.name)
                    output_json["related_entities_id"].append(value_description.id)
                else:
                    for k, v in value_description:                            
                        inner_k = get_string_name_from_sling_object(k)
                        inner_v = get_string_name_from_sling_object(v)
                        if type(inner_k) is str and type(inner_v) is str:
                            output_json["attributes"].append([key_description, [inner_k, inner_v]])
                        if type(v) is sling.Frame:
                            if check_if_frame_wikidata_item_2(v):
                                output_json["related_entities"].append(v.name)
                                output_json["related_entities_id"].append(v.id)
            elif type(value_description) == int:
                output_json["attributes"].append([key_description, value_description])
            else:
                pass
        elif type(value_description) == int:
            output_json["attributes"].append([key_description, value_description])
        else:
            pass
    output_json["contents"] = "feature removed for now"            
    #for predicate, objects in output_json["attributes"]:
    #    output_json["contents"] += f"{predicate} {objects} "
    return output_json
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('output_folder')
    parser.add_argument('kb_sling_filepath', default = "./wiki/kb.sling")
    parser.add_argument('phrase_table_filepath', default = "./wiki/en/phrase-table.repo")
    args = parser.parse_args()
    
    kb_sling_filepath = args.kb_sling_filepath
    phrase_table_filepath = args.phrase_table_filepath
    output_folder = args.output_folder
    
    kb = sling.Store()
    kb.load(kb_sling_filepath)
    names = sling.PhraseTable(kb, phrase_table_filepath)
    n_item = kb["/w/item"]
    kb_len = len(kb)
    kb.freeze()
    
    x = 0
    count = 0
    h = open(os.path.join(output_folder, f"kb_index_{x}.jsonl"), "w+")
    error_file = open(os.path.join(output_folder, "error_log.txt"), "w+")
    for i in range(10):
        corpus = sling.Corpus(f"./wiki/en/documents-0000{i}-of-00010.rec", commons=kb)
        for document in corpus:
            try:
                frame_object = document.frame
                text = document.text.decode()
                if len(text) > 0:
                    text = text.split("\n")[0]
                    text = cleanhtml(text)
                corr_wd_id = frame_object["/wp/page/item"]
                frame_as_json = frame_to_json(corr_wd_id)
                frame_as_json["description"] = text
                frame_as_json["wp_name"] =  frame_object["/wp/page/title"]
                frame_as_json["wp_url"] = frame_object["url"]
                if "id" in frame_as_json:
                    h.write(json.dumps(frame_as_json))
                    h.write("\n")
                    count += 1
                if count % 10000 == 0:
                    print(f"DONE: {count} / {kb_len}")
                if count % 10000000 == 0:
                    h.close()
                    x += 1
                    h = open(f"./index_collections/index_collection_3/kb_index_{x}.json", "w+")
            except Exception as e:
                error_file.write(f"{e} \n {document} \n ___________________________________")
    h.close()

    '''
    for entity in names.lookup("Glasgow"):
        #print(entity)
        pprint.pprint(frame_to_json(entity))
        #x = frame_to_json(entity)
        #with open("./testjson.json", "w") as test_file:
            #json.dump(x, test_file) 

        break
            
                   
    x = 0
    i = 0
    h = open(os.path.join(output_folder, f"kb_index_{x}.jsonl"), "w+")
    
    for f in kb:
        if f.isa(n_item):
            try:
                json_frame = frame_to_json(f)
                if len(json_frame) > 0:
                    h.write(json.dumps(json_frame))
                    h.write("\n")
                    i += 1
                if i % 10000 == 0:
                    print(f"DONE: {i} / {kb_len}")
                if i % 10000000 == 0 or i >= kb_len:
                    h.close()
                    x += 1
                    h = open(f"./index_collections/index_collection_3/kb_index_{x}.json", "w+")
            except Exception as e:
                print(f)
                print(e)
                print("___________________________________")
    '''
    '''
    

    output_list = []
    kb_len = len(kb)
    x = 0
    i = 0
    for f in kb: 
        if f.isa(n_item):
            try:
                json_frame = frame_to_json(f)
                output_list.append(json_frame)
                i += 1
                if i % 10000 == 0:
                    print(f"DONE: {i} / {kb_len}")
                if i % 10000000 == 0 or i >= kb_len:
                    with open(f"./index_collections/index_collection_3/kb_index_{x}.json", "w+") as g:
                        json.dump(output_list, g)
                    output_list = []
                    x += 1
            except Exception as e:
                print(f)
                print(json_frame)
                print(e)
                print("___________________________________")
    try:
        g.close()
    except:
        pass
    '''


    
    

