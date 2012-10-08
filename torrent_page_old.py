#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 andronikov
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
from bs4 import BeautifulSoup
import sys
import os
import re
from datetime import datetime
import unicodecsv

def get_torrent_page(torrent_id, protocol):
    r = requests.get(protocol + "://thepiratebay.se/torrent/" + str(torrent_id), headers={'user-agent': 'tpb2csv'})
    print "Getting torrent page:",
    print r.status_code

    if (r.status_code != 200):
        return r.status_code
        
    soup = BeautifulSoup(r.content.replace('document.write(\"<scr\"+\"ipt language=\'JavaScr\"+\"ipt\' src=\'http://d3.zedo.com/jsc/d3/fo.js\'></scr\"+\"ipt>\");\n',''))

    if (soup.find(id="err")):
        return 404

    description_text = soup.find("div", {"class": "nfo"}).pre.get_text()[:-2]

    first_level = str(int(torrent_id) / 1000000) + "xxxxxx/"
    second_level = str(int(torrent_id) / 100000) + "xxxxx/"
    third_level = str(int(torrent_id) / 10000) + "xxxx/"

    if not os.path.exists("data/"):
        os.makedirs("data/")
    if not os.path.exists("data/" + first_level):
        os.makedirs("data/" + first_level)
    if not os.path.exists("data/" + first_level + second_level):
        os.makedirs("data/" + first_level + second_level)
    if not os.path.exists("data/" + first_level + second_level + third_level):
        os.makedirs("data/" + first_level + second_level + third_level)
    if not os.path.exists("data/" + first_level + second_level + third_level + str(torrent_id)):
        os.makedirs("data/" + first_level + second_level + third_level + str(torrent_id))

    path = "data/" + first_level + second_level + third_level + str(torrent_id)

    open(path + "/description.txt", 'w').write(description_text.encode('utf-8', 'replace'))
    details_csv = open(path + "/details.csv", 'w')
    details_csv.write(u'\ufeff'.encode('utf-8')) # BOM
    csv_writer = unicodecsv.writer(details_csv, encoding='utf-8')

    title = soup.find("div", {"id": "title"}).get_text()[3:-1]

    one_column = bool(soup.find("img", {"title": "picture"}))
    imdb = bool(soup.find("a", {"title": "IMDB"}))
    imdb_link = ''
    spoken = ''
    texted = ''
    tags_exist = bool(soup.find("dl", {"class": "col1"}).find(href=re.compile("/tag/")))

    column1 = [i for i in soup.find("dl", {"class": "col1"}).contents if i != '\n' and str(i) != '<br/>' and i != ' ']
    column2 = [i for i in soup.find("dl", {"class": "col2"}).contents if i != '\n' and str(i) != '<br/>' and i != ' ']

    offset = 0
    spoken_exists = bool(soup.find("dl", {"class": "col1"}).find(text=re.compile("Spoken language\(s\)")) or soup.find("dl", {"class": "col2"}).find(text=re.compile("Spoken language\(s\)")))
    texted_exists = bool(soup.find("dl", {"class": "col1"}).find(text=re.compile("Texted language\(s\)")) or soup.find("dl", {"class": "col2"}).find(text=re.compile("Texted language\(s\)")))

    if imdb:
        offset += 2

    if spoken_exists:
        if column1[6+offset].get_text() == "Spoken language(s):":
            spoken_pos = 6+offset
        elif column1[8+offset].get_text() == "Spoken language(s):":
            spoken_pos = 8+offset
        offset += 2

    if texted_exists: 
        if column1[6+offset].get_text() == "Texted language(s):":
            texted_pos = 6+offset
        elif column1[8+offset].get_text() == "Texted language(s):":
            texted_pos = 8+offset
        offset += 2

    if tags_exist:
        offset += 2

    category = column1[1].a.get("href")[-3:]

    num_of_files = column1[3].get_text()

    size = column1[5].get_text().replace(u'\xa0', u' ') ## TPB loves to use &nbsp

    if imdb:
        imdb_link = column1[7].a['href']

    if spoken_exists:
        spoken = column1[spoken_pos+1].get_text()

    if texted_exists:
        texted = column1[texted_pos+1].get_text()

    if tags_exist:
        tags = [tag.get_text() for tag in column1[5+offset].children if tag != ' ']

    if one_column:
        rating_str = column1[7+offset].get_text()[3:-2]
    else:
        rating_str = column2[1].get_text()[3:-2]

    nums = [char for char in rating_str if char.isdigit() or char == '/' or char == '(']
    rating = ''

    for i in nums:
        if i == '(':
            break
        rating +=i

    rating = rating.split('/')
    if one_column:
        timestamp = column1[9+offset].get_text()
    else:
        timestamp = column2[3].get_text()

    uploaded = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S GMT").isoformat() + "Z"

    if one_column:
        username = column1[11+offset].contents[1].get_text()
    else:
        username = column2[5].contents[1].get_text()

    if one_column:
        username_contents_array = [child for child in column1[11+offset].descendants]
    else:
        username_contents_array = [child for child in column2[5].descendants]

    has_icon = False
    if len(username_contents_array) > 4:
        has_icon = True

    icon = ''

    if has_icon:
        if username_contents_array[4]['title'] == 'Trusted':
            icon = '[T]'
        elif username_contents_array[4]['title'] == 'VIP':
            icon = '[V]'    
        elif username_contents_array[4]['title'] == 'Helper':
            icon = '[H]'
        elif username_contents_array[4]['title'] == 'Supermod':
            icon = '[S]'
        elif username_contents_array[4]['title'] == 'Moderator':
            icon = '[M]'
        elif username_contents_array[4]['src'] == '//static.thepiratebay.se/img/admin.gif':
            icon = '[A]'
        else:
            icon = '[O]'

    if one_column:
        seeders = int(column1[13+offset].get_text())
    else:
        seeders = int(column2[7].get_text())

    if one_column:
        leechers = int(column1[15+offset].get_text())
    else:
        leechers = int(column2[9].get_text())

    try:
        btih = soup.find_all("div", {"class": "download"})[1].a['href'][20:60].upper()
    except:
        btih = soup.find("div", {"class": "download"}).find("a", {"title": "Get this torrent"})['href'][20:60].upper()

    if one_column:
        picture = soup.find("img", {"title": "picture"})['src']

    csv_writer.writerow(['Title', 'Type', 'Files', 'Size', 'IMDB', 'Spoken Languages', 'Texted Languages', 'Tags', 'Quality (+)', 'Quality (-)', 'Uploaded', 'By', 'User Type', 'Seeders', 'Leechers', 'Info Hash', 'Picture', 'Capture Date'])

    if not imdb:
        imdb_link = ''

    if not spoken_exists:
        spoken = ''

    if not texted_exists:
        texted = ''

    if not tags_exist:
        tags = ''

    if not one_column:
        picture = ''

    new_tags = [u'"' + unicode(tag )+ u'"' for tag in tags]
    tag_string = u','.join(new_tags)

    cleaned_up_data = []
    for element in [title,category,num_of_files,size,imdb_link,spoken,texted,tag_string,rating[0],rating[1],uploaded,username,icon,seeders,leechers,btih,picture,datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")]:
        cleaned_up_data.append(unicode(element).encode('utf-8', 'replace'))

    csv_writer.writerow(cleaned_up_data)
    return 200

if __name__ == '__main__':
	get_torrent_page(sys.argv[1], 'http')
