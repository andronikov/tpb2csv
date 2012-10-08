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

import sys
import os

import requests
import lxml.html
from lxml.html.soupparser import fromstring
from lxml.html import tostring

from datetime import datetime
import csv

def get_torrent_page(torrent_id, protocol):
    r = requests.get(protocol + "://thepiratebay.se/torrent/" + str(torrent_id), headers={'user-agent': 'tpb2csv'})
    print "Getting torrent page:",
    print r.status_code

    if (r.status_code != 200):
        return r.status_code

    html = fromstring(r.content)

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


    detailsframe = html.xpath('//html/body/div[@id="content"]/div[@id="main-content"]/div/div[@id="detailsouterframe"]/div[@id="detailsframe"]')[0]
    title = unicode(detailsframe.xpath('div[@id="title"]')[0].text[3:-1])
    details = detailsframe.xpath('div[@id="details"]')[0]

    one_column = details.xpath('div[@class="torpicture"]/img') != []
    if one_column:
        picture = details.xpath('div[@class="torpicture"]/img')[0].get('src')
    else:
        picture = ''

    column1 = details.xpath('dl[@class="col1"]')[0]
    column1_tags = zip(column1.findall('dt'), column1.findall('dd'))
    if not one_column:
        column2 = details.xpath('dl[@class="col2"]')[0]
        column2_tags = zip(column2.findall('dt'), column2.findall('dd'))

    category = column1_tags[0][1][0].get('href')[-3:]

    size = column1_tags[2][1].text.replace(u'\xa0', ' ')

    num_files = int(column1_tags[1][1][0].text)

    offset = 0
    if column1_tags[3+offset][0].text == 'Info:':
        imdb = column1_tags[3+offset][1][0].get('href')
        offset += 1
    else:
        imdb = ''

    if column1_tags[3+offset][0].text == 'Spoken language(s):':
        spoken = column1_tags[3+offset][1].text
        offset += 1
    else:
        spoken = ''

    if column1_tags[3+offset][0].text == 'Texted language(s):':
        texted = column1_tags[3+offset][1].text
        offset += 1
    else:
        texted = ''

    tags = [tag.text for tag in column1_tags[3+offset][1]]
    tag_string = u','.join([u'"' + unicode(tag )+ u'"' for tag in tags])

    if one_column:
        rating_str = column1.xpath('dd[@id="rating"]')[0].text[3:-2]
        timestamp = column1_tags[5+offset][1].text
        username = column1_tags[6+offset][1][0].text
        if len(column1_tags[6+offset][1]) == 2:
            usertype = '[' + column1_tags[6+offset][1][1].get('title')[0] + ']'
        else:
            usertype = ''
        seeders = int(column1_tags[7+offset][1].text)
        leechers = int(column1_tags[8+offset][1].text)
    else:
        rating_str = column2.xpath('dd[@id="rating"]')[0].text[3:-2]
        timestamp = column2_tags[1][1].text
        username = column2_tags[2][1][0].text
        if len(column2_tags[2][1]) == 2:
            usertype = '[' + column2_tags[2][1][1].get('title')[0] + ']'
        else:
            usertype = ''
        seeders = int(column2_tags[3][1].text)
        leechers = int(column2_tags[4][1].text)

    rating_pieces = rating_str.split(' ')
    rating_positive = abs(int(rating_pieces[0]))
    rating_negative = abs(int(rating_pieces[2]))
    del rating_pieces

    iso_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S GMT").isoformat() + "Z"

    btih = details.xpath('div[@class="download"]/a')[0].get('href')[20:60].upper()

    description = unicode(details.xpath('div[@class="nfo"]/pre')[0].text_content()[:-2])    

    open(path + "/description.txt", 'w').write(description.encode('utf-8', 'replace'))

    csv_writer = csv.writer(open(path + "/details.csv", 'w'))

    csv_writer.writerow(['Title', 'Type', 'Files', 'Size', 'IMDB', 'Spoken Languages', 'Texted Languages', 'Tags', 'Quality (+)', 'Quality (-)', 'Uploaded', 'By', 'User Type', 'Seeders', 'Leechers', 'Info Hash', 'Picture', 'Capture Date'])

    cleaned_up_data = []
    for element in [title,category,num_files,size,imdb,spoken,texted,tag_string,rating_positive,rating_negative,iso_timestamp,username,usertype,seeders,leechers,btih,picture,datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")]:
        cleaned_up_data.append(unicode(element).encode('utf-8', 'replace'))

    csv_writer.writerow(cleaned_up_data)
    return 200

if __name__ == '__main__':
	get_torrent_page(sys.argv[1], 'http')
