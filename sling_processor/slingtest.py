import sling
import pprint
import requests
import pprint
import json


def print_frame(frame):
    print(frame.get("name"))
    print(frame.get("/w/item/category").get("/w/item/category"))
    for key, value in frame:
        key_is_frame = type(key) is sling.Frame
        description = key
        if key_is_frame:
            if "name" in key:
                description = key.get("name")
            elif "id" in key:
                description = key.get("id")
            else:
                pass
                
        value_is_frame = type(value) is sling.Frame
        value_name = value
        if value_is_frame:
            if "name" in value:
                value_name = value.get("name")
            else:
                temp = ""
                for k, v in value:
                    inner_key = k
                    if type(k) is sling.Frame:
                        if "name" in k:
                            inner_key = k.get("name")
                    inner_value = v
                    if type(v) is sling.Frame:
                        if "name" in v:
                            inner_value = v.get("name")
                    temp += f"{(inner_key, inner_value)} | "
                value_name = temp
        print(f"{type(description)} / {(description, value_name)} / {type(value) is sling.Frame}")
        print("_________________________________________________________________________")


def get_string_from_sling_object(item):
    if "name" in item:
        return item.get("name")
    elif "id" in item:
        return item.get("id")
    elif "is" in item:
        return item.get("is")
    else:
        return ""
    
def check_if_frame_wikidata_item(item):
    if "isa" in item:
        return get_string_from_sling_object(item.get("isa")) == "Wikidata item"
    return False
            
    
def frame_to_trecweb(frame):
    output_json = {"name": "", "category": [], "related_entities": [], "attributes": [], "contents": "", "id": ""}
    for key, value in frame:
        key_is_frame = type(key) is sling.Frame
        key_description = get_string_from_sling_object(key)
        
        if key_description == "name":
            if type(key_description) is bytes:
                continue
            output_json["name"] = str(value)
        elif key_description == "id":
            output_json["id"] = str(value)
        elif key_description == "/w/item/category":
            output_json["category"].append(str(get_string_from_sling_object(value)))
        else:
            value_description = value
            if type(value_description) is sling.Frame:
                is_wikidata_item = check_if_frame_wikidata_item(value_description)        
                value_description = get_string_from_sling_object(value)
                
                if is_wikidata_item and value_description != "" and type(value_description) is str:
                    output_json["related_entities"].append(value_description)
                    
                if type(value_description) is sling.Frame:
                    is_wikidata_item = check_if_frame_wikidata_item(value_description)        
                    value_description = get_string_from_sling_object(value_description)
                    if is_wikidata_item and value_description != "" and type(value_description) is str:
                        output_json["related_entities"].append(value_description)
                        
                if type(value_description) is str:
                    output_json["attributes"].append([key_description, value_description])
            else:
                if type(value) is str:
                    output_json["attributes"].append([key_description, value])
                    
    for predicate, objects in output_json["attributes"]:
        output_json["contents"] += f"{predicate} {objects} "
    return output_json
        
if __name__ == "__main__":

    kb = sling.Store()
    kb.load("/nfs/project/bbc/sling/wiki/kb.sling")
    names = sling.PhraseTable(kb, "/nfs/project/bbc/sling/wiki/en/phrase-table.repo")
    n_item = kb["/w/item"]
    kb.freeze()
    
    output_list = []
    kb_len = len(kb)
    x = 0
    i = 0
    for f in kb: 
        if f.isa(n_item):
            try:
                json_frame = frame_to_trecweb(f
                output_list.append(json_frame)
                i += 1
                if i % 10000 == 0:
                    print(f"DONE: {i} / {kb_len}")
                if i % 10000000 == 0 or i >= kb_len:
                    with open(f"./index_collection/kb_index_{x}.json", "w+") as g:
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

    
    



    
    

