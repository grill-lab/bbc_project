import argparse
import re
import json
import os
from bs4 import BeautifulSoup

bbc_article_dict = {}
bbc_related_links = {}
last_updated_dict = {}
bbc_thing_tags = {}
raw_json = {}
input_json_list = []
sub_topic_dict = {}
tag_re = re.compile(r'<[altText][^>]*>(.+?)</[altText]>')

acceptable_content_types = ["news/","new/","sports/","newsround/","sport/","food/","music/","bitesize/","health/"]
#paths = ["./bbc/news-20200101-20201115/","./bbc/news_av/"]

def get_follow_up_candidates():
    output = {}
    for article_id in bbc_related_links.keys():
        if article_id not in output:
            output[article_id] = {"related":[], "sub_topics": [],"bbc_things":[]}
        output[article_id]["related"] += bbc_related_links[article_id]
        output[article_id]["sub_topics"] += sub_topic_dict[article_id]
        output[article_id]["bbc_things"] += bbc_thing_tags[article_id]
    return output

def parse_input(input_folder_path):
    for file in os.listdir(input_folder_path):
        full_path = os.path.join(input_folder_path, file)
        if os.path.isdir(full_path):
            print(file)
            parse_input(full_path)
        else:
            if (file[-5:] != ".json") and "newsround" not in file:
                continue
            if ".ipynb" in full_path:
                continue
            with open(full_path) as f:
                json_content = json.load(f)
                input_json_list.append(json_content)
            f.close()

def denoise_string(text):
    if text[-1:] in ['.','?','!']:
        text += ' '
    if text[-2:-1] not in ['.','?','!'] and text[-1:] != ' ':
        text += '. '
    text = text.replace("&quot;","\"")
    text = text.replace("\\'","'")
    text = text.strip()
    return text

def id_to_url(doc_id):
    doc_id_2 = doc_id[:doc_id.rfind(".")]
    if "urn:bbc:content:assetUri" in doc_id:
        if "." in doc_id:
            url = "https://bbc.co.uk/" + doc_id_2[25:]
        else:
            url = "https://bbc.co.uk/" + doc_id[25:]
        return url
    return doc_id

def bbc_extract_single_block(content):
    extracted_text = ''
    extracted_potential_related_candidates = ''
    sub_topics = []
    if content['type'] == 'paragraph' and content['markupType'] == 'plain_text':
        text = content['text']
        text_filtered = re.sub("<altText>.*?</altText>",'',text)
        text_filtered = re.sub('<[^>]+>','', text_filtered)
        extracted_text += text_filtered
    elif content['type'] == 'paragraph' and content['markupType'] == 'candy_xml':
        if 'meta' in content:
            headline = content['meta'][0]['headlines']['headline']
            extracted_text += headline
            related_bbc_id = content['meta'][0]['id']
            extracted_potential_related_candidates += related_bbc_id
        else:
            text = content['text']
            text_filtered = re.sub("<altText>.*?</altText>",'',text)
            text_filtered = re.sub('<[^>]+>','', text_filtered)
            extracted_text += text_filtered
            soup = BeautifulSoup(f"<div>{text}</div>",features="html.parser")
            if soup is not None:
                url = soup.find('url')
                if url is not None:
                    url = url['href']
                    if url is not None:
                        if 'https://www.bbc.co.uk' in url:
                            extracted_potential_related_candidates += "urn:bbc:content:assetUri:" + url[22:]
    elif content['type'] == 'crosshead' and content['markupType'] == 'plain_text':
        #extracted_text += '<h2>' + content['text'] + '</h2>'
        extracted_text += content['text']
        sub_topics.append(content['text'])
        
    return (extracted_text, extracted_potential_related_candidates,sub_topics)
        
def bbc_extract_full_block(contents):
    extracted_full_text = []
    extracted_potential_related_candidates = []
    all_sub_topics = []
    for content in contents:
        if content['type'] == 'list':
            for item in content['items']:
                text, candidates, sub_topics = bbc_extract_single_block(content)
                all_sub_topics += sub_topics
                if text != "":
                    text = denoise_string(text)
                    extracted_full_text.append(text)
                if candidates != "":
                    extracted_potential_related_candidates.append(candidates)
        else:
            text, candidates, sub_topics = bbc_extract_single_block(content)
            all_sub_topics += sub_topics
            if text != "":
                text = denoise_string(text)
                extracted_full_text.append(text)
            if candidates != "":
                extracted_potential_related_candidates.append(candidates)
    return (extracted_full_text, extracted_potential_related_candidates, all_sub_topics)


def extract_all_content(input_json_list):         
    for json_content in input_json_list:
        if "metadata" not in json_content:
            continue
        article_id = json_content['metadata']['locators']['cpsUrn']
        last_updated_date = json_content['metadata']['lastUpdated']
        
        if not any(content_type in article_id for content_type in acceptable_content_types):
            continue
            
        raw_json[article_id] = json_content

        if article_id not in bbc_article_dict:
            bbc_article_dict[article_id] = {}
            bbc_related_links[article_id] = []
            bbc_thing_tags[article_id] = []
            sub_topic_dict[article_id] = []

        if article_id in last_updated_dict:
            if (last_updated_date > last_updated_dict[article_id]):
                bbc_article_dict[article_id] = {}
                bbc_related_links[article_id] = []
                bbc_thing_tags[article_id] = []
            else:
                continue

        last_updated_dict[article_id] = last_updated_date
        last_published_date = json_content['metadata']['lastPublished']
        url = id_to_url(article_id)
        title = json_content['promo']['headlines']['headline']
        contents = json_content['content']['blocks']
        extracted_text, potential_related_candidates, sub_topics = bbc_extract_full_block(contents)
        
        bbc_article_dict[article_id]["title"] = title
        bbc_article_dict[article_id]["content"] = extracted_text
        bbc_article_dict[article_id]["last_published"] = last_published_date
        bbc_article_dict[article_id]["url"] = url
        
        sub_topic_dict[article_id] += sub_topics

        related_content_main_block = json_content['relatedContent']
        if "groups" in related_content_main_block:
            related_content_sub_block_list = related_content_main_block["groups"]
            for related_content_sub_block in related_content_sub_block_list:
                if "promos" in related_content_sub_block:
                    related_content_list = related_content_sub_block["promos"]
                    for related_content in related_content_list:
                        if "locators" in related_content:
                            related_article_id = related_content["locators"]["cpsUrn"]
                            bbc_related_links[article_id].append(related_article_id[:25] + related_article_id[26:])
        bbc_related_links[article_id] += potential_related_candidates

        if 'about' in json_content['metadata']['tags']:
            tags_block  = json_content['metadata']['tags']['about']
            bbc_thing_tags[article_id] = tags_block

            
def get_passages(article_dict, passage_size=100, window_size=50):
    output_dict = {}
    for article_id, article_content in article_dict.items():
        content_as_list = article_content["content"]
        title = article_content["title"]
        url = article_content["url"]
        last_published_date = article_content["last_published"]
        slice_start = 0
        slice_end = passage_size
        sub_id = 0
        content_as_string = " ".join(content_as_list)
        content_broken_to_words_as_list = content_as_string.split()
        content_len = len(content_broken_to_words_as_list)
        while (slice_end < content_len):
            passage = " ".join(content_broken_to_words_as_list[slice_start:slice_end])
            output_dict[f"{article_id}.{sub_id}"] = {"contents":passage, 
                                                     "title": title,
                                                     "url": url,
                                                     "last_published": last_published_date
                                                    }
            slice_start += window_size
            slice_end += window_size
            sub_id += 1
        passage = " ".join(content_broken_to_words_as_list[slice_start:content_len])
        output_dict[f"{article_id}.{sub_id}"] = {"contents":passage, 
                                                     "title": title,
                                                     "url": url,
                                                     "last_published": last_published_date
                                                    }
    return output_dict

def trec_formatter(doc_id, body, title):
    doc_id_2 = doc_id[:doc_id.rfind(".")]
    if "." in doc_id:
        url = "https://bbc.co.uk/" + doc_id_2[25:]
    else:
        url = "https://bbc.co.uk/" + doc_id[25:]
    content = ""
    content = (u'<DOC>\n')
    content += (u'<DOCNO>')
    content += doc_id
    #content += (u'\n')
    content += (u'</DOCNO>\n')
    content += (u'<DOCHDR>\n')
    content += (u'\n')
    content += (u'</DOCHDR>\n')
    #content += (u'<HTML>\n')
    content += (u'<TITLE>')
    content += title
    #content += (u'\n')
    content += (u'</TITLE>\n')
    content += (u'<URL>')
    content += url
    #content += (u'\n')
    content += (u'</URL>\n')
    content += (u'<BODY>\n')
    content += body
    content += (u'\n')
    content += (u'</BODY>\n')
    #content += (u'</HTML>\n')
    content += (u'</DOC>\n')
    return content

def to_trec_web(article_dict, passage_dict, output_folder):
    doc_only_output_file = open(f"{output_folder}trec_full_doc.trecweb","w")
    passage_only_output_file = open(f"{output_folder}trec_full_passages.trecweb","w")
    mixed_output_file = open(f"{output_folder}trec_mixed.gov2","w")
    
    for article_id, article_content in article_dict.items():
        title = article_content["title"]
        content_as_list = article_content["content"]
        content_as_string = " ".join(content_as_list)
        trec_content = trec_formatter(article_id, content_as_string, title)
        doc_only_output_file.write(trec_content)
        mixed_output_file.write(trec_content)
    
    for passage_id, passage_block in passage_dict.items():
        passage = passage_block["contents"]
        title = passage_block["title"]
        trec_content = trec_formatter(passage_id, passage, title)
        passage_only_output_file.write(trec_content)
        mixed_output_file.write(trec_content)
    
    doc_only_output_file.close()
    passage_only_output_file.close()
    mixed_output_file.close()
    
def to_json(article_dict, passage_dict, output_folder):
    doc_only_output_file = open(f"{output_folder}trec_full_doc.json","w")
    passage_only_output_file = open(f"{output_folder}trec_full_passages.json","w")
    mixed_output_file = open(f"{output_folder}trec_mixed.json","w")
    
    doc_only_json = []
    passage_only_json = []
    mixed_json = []
    
    for article_id, article_content in article_dict.items():
        title = article_content["title"]
        url = article_content["url"]
        last_published_date = article_content["last_published"]
        content_as_list = article_content["content"]
        content_as_string = " ".join(content_as_list)
        to_append_dict = {
                "id": article_id,
                "title": title,
                "contents": content_as_string,
                "url": url, 
                "last_published": last_published_date,
            }
        doc_only_json.append(to_append_dict)
        mixed_json.append(to_append_dict)
        
    for passage_id, passage_block in passage_dict.items():
        passage = passage_block["contents"]
        title = passage_block["title"]
        url = article_content["url"]
        last_published_date = article_content["last_published"]
        to_append_dict = {
                "id": passage_id,
                "title": title,
                "contents": passage,
                "url": url, 
                "last_published": last_published_date,
            }
        passage_only_json.append(to_append_dict)
        mixed_json.append(to_append_dict)
    
    json.dump(doc_only_json,doc_only_output_file)
    json.dump(passage_only_json, passage_only_output_file)
    json.dump(mixed_json, mixed_output_file)
    
    doc_only_output_file.close()
    passage_only_output_file.close()
    mixed_output_file.close()
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Usage: python bbc_extractor.py input_folder output_folder --passage_size ## --window_size ##')
    parser.add_argument('input_folder_path', help='bbc folder to process, folder name should end in /')
    parser.add_argument('output_folder_path', help='output folder to write out, not filename, should also end in /')
    parser.add_argument('output_format', help='can be either "json" or "trec"')
    parser.add_argument('--passage_size', type=int,default=100)
    parser.add_argument('--window_size', type=int,default=50)
    args = parser.parse_args()
    
    input_folder_path = args.input_folder_path
    output_folder_path = args.output_folder_path
    output_format = args.output_format
    passage_size = args.passage_size
    window_size = args.window_size
    
    parse_input(input_folder_path)
    extract_all_content(input_json_list)
    follow_up_candidates = get_follow_up_candidates()
    
    with open(os.path.join(output_folder_path, "offline_candidates.json" ), "w") as f:
        json.dump(follow_up_candidates, f)
 
    passage_dict = get_passages(bbc_article_dict, passage_size, window_size)
    if output_format == "trec":
        to_trec_web(bbc_article_dict, passage_dict, output_folder_path)
    elif output_format == "json":
        to_json(bbc_article_dict, passage_dict, output_folder_path)
    else:
        print("provide correct output format")
    