import sling
import pprint
import json
import sys
import argparse
import os

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
    output_json = {"name": "", "category": [], "related_entities": [], "attributes": [], "contents": "", "id": ""}
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
                else:
                    for k, v in value_description:                            
                        inner_k = get_string_name_from_sling_object(k)
                        inner_v = get_string_name_from_sling_object(v)
                        if type(inner_k) is str and type(inner_v) is str:
                            output_json["attributes"].append([key_description, [inner_k, inner_v]])
                        if type(v) is sling.Frame:
                            if check_if_frame_wikidata_item_2(v):
                                output_json["related_entities"].append(v.name)
            else:
                pass
        else:
            pass
                
    for predicate, objects in output_json["attributes"]:
        output_json["contents"] += f"{predicate} {objects} "
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
    for entity in names.lookup("Glasgow"):
        x = frame_to_json(entity)
        with open("./testjson.json", "w") as test_file:
            json.dump(x, test_file) 

        break
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


    
    

