import argparse
import json
import os

json_raw = {}
sounds_synopsis_dict = {}


def extract_sounds_content(input_folder_path):
    for file in os.listdir(input_folder_path):
        if "sounds" in file:
            with open(f"{input_folder_path}{file}") as f:
                for line in f:
                    if line[0]=="{":
                        json_content = json.loads(line)
                        if "synopses" in json_content:
                            synopsis = json_content["synopses"]
                            json_raw[json_content["pid"]] = json_content

                            synopsis = json_content["synopses"]
                            if "brand_title" not in json_content:
                                title = ""
                            else:
                                title = json_content["brand_title"]
                                
                            if json_content["pid"] not in sounds_synopsis_dict:
                                sounds_synopsis_dict[json_content["pid"]] = {}
                            sounds_synopsis_dict[json_content["pid"]]["title"] = title
                            if "short" in synopsis:
                                if synopsis["short"] != "":
                                    sounds_synopsis_dict[json_content["pid"]]["synopsis"] = synopsis["short"]
                            if "medium" in synopsis:
                                if synopsis["medium"] != "":
                                    sounds_synopsis_dict[json_content["pid"]]["synopsis"] = synopsis["medium"]
                            if "long" in synopsis:
                                if synopsis["long"] != "":
                                    sounds_synopsis_dict[json_content["pid"]]["synopsis"] = synopsis["long"]
                        else:
                            continue
            f.close()
            
def trec_formatter(doc_id, body, title):
    url = "https://bbc.co.uk/" + doc_id[25:]
    content = ""
    content = (u'<DOC>\n')
    content += (u'<DOCNO>')
    content += doc_id
    content += (u'</DOCNO>\n')
    content += (u'<DOCHDR>\n')
    content += url
    content += (u'\n')
    content += (u'</DOCHDR>\n')
    content += (u'<HTML>\n')
    content += (u'<HEAD>\n')
    content += title
    content += (u'\n')
    content += (u'</HEAD>\n')
    content += (u'<BODY>\n')
    content += body
    content += (u'\n')
    content += (u'</BODY>\n')
    content += (u'</HTML>\n')
    content += (u'</DOC>\n')
    return content

def sounds_to_trec(sounds_synopsis_dict, output_folder_path):
    output_file = open(f"{output_folder_path}trec_sounds.trecweb","w")
    for sounds_id, sounds_info in sounds_synopsis_dict.items():
        sounds_title = sounds_info["title"]
        sounds_synopsis = sounds_info["synopsis"]
        sounds_body = sounds_title + " " + sounds_synopsis
        trec_formatted_string = trec_formatter(sounds_id, sounds_body, sounds_title)
        output_file.write(trec_formatted_string)
    output_file.close()
    
def sounds_to_json(sounds_synopsis_dict, output_folder_path):
    output_file = open(f"{output_folder_path}trec_sounds.json","w")
    output_json = []
    for sounds_id, sounds_info in sounds_synopsis_dict.items():
        sounds_title = sounds_info["title"]
        sounds_synopsis = sounds_info["synopsis"]
        sounds_body = sounds_title + " " + sounds_synopsis
        to_append_dict = {
            "id": sounds_id,
            "contents": sounds_body,
        }
        output_json.append(to_append_dict)
    json.dump(output_json, output_file)
    output_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Usage: python sounds_extractor.py input_folder output_folder')
    parser.add_argument('input_folder_path', help='bbc folder to process, folder name should end in /')
    parser.add_argument('output_folder_path', help='output folder to write out, not filename, should also end in /')
    parser.add_argument('output_format', help='can be either "json" or "trec"')
    args = parser.parse_args()
    
    input_folder_path = args.input_folder_path
    output_folder_path = args.output_folder_path
    output_format = args.output_format
    
    extract_sounds_content(input_folder_path)
    if output_format == "trec":
        sounds_to_trec(sounds_synopsis_dict, output_folder_path)
    elif output_format == "json":
        sounds_to_json(sounds_synopsis_dict, output_folder_path)
    else:
        print("provide correct output format")
    