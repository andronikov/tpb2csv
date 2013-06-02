#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 
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
import csv

from datetime import datetime

def get_torrent_page(torrent_id, protocol):
    r = requests.get(protocol + "://thepiratebay.sx/torrent/" + str(torrent_id))
    print "Getting torrent page:",
    print r.status_code

    if (r.status_code != 200):
        return r.status_code

    html = lxml.html.fromstring(unicode(r.content, 'utf-8'))

    first_level  = str(int(torrent_id) / 1000000) + "xxxxxx/"
    second_level = str(int(torrent_id) / 100000) + "xxxxx/"
    third_level  = str(int(torrent_id) / 10000) + "xxxx/"

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
    try:
        title = unicode(html.xpath('//div[@id="detailsframe"]/div[@id="title"]')[0].text).strip()
    except IndexError:
        open("logs/" + str(int(torrent_id) / 100000) + "xxxxx/" + "download.log", 'a').write(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " " + str('BAD') + '\n')
    details = html.xpath('//div[@id="details"]')[0]

    one_column = details.xpath('div[@class="torpicture"]/img') != []
    if one_column:
        picture = details.xpath('div[@class="torpicture"]/img')[0].get('src')
    else:
        picture = ''

    column1 = details.xpath('dl[@class="col1"]')[0]
    column1_tags = zip(column1.findall('dt'), column1.findall('dd'))
    column2_tags = []
    if not one_column:
        column2 = details.xpath('dl[@class="col2"]')[0]
        column2_tags = zip(column2.findall('dt'), column2.findall('dd'))

    imdb = ''
    spoken = ''
    texted = ''
    tags = ''
    for detail in column1_tags + column2_tags:
        if detail[0].text == 'Type:':
            category = detail[1].xpath('a')[0].get('href')[-3:] # href="/browse/000" -> "000"
        if detail[0].text == 'Files:':
            num_files = detail[1].text_content()
        if detail[0].text == 'Size:':
            size = detail[1].text_content().replace(u'\xa0', ' ')
        if detail[0].text == 'Uploaded:':
            iso_timestamp = datetime.strptime(detail[1].text_content(), "%Y-%m-%d %H:%M:%S GMT").isoformat() + "Z"
        if detail[0].text == 'By:':
            username = detail[1].text_content().strip()
            if detail[1].xpath('img') != []:
                usertype = '[' + detail[1].xpath('img')[0].get('title')[0] + ']'
            else:
                usertype = ''
        if detail[0].text == 'Seeders:':
            seeders = detail[1].text_content()
        if detail[0].text == 'Leechers:':
            leechers = detail[1].text_content()

        if detail[0].text == 'Info:':
            imdb = detail[1].xpath('a')[0].get('href')
        if detail[0].text == 'Spoken language(s):':
            spoken = detail[1].text_content().strip()
        if detail[0].text == 'Texted language(s):':
            texted = detail[1].text_content().strip()
        if detail[0].text == 'Tag(s):':
            tags = u','.join([u'"' + unicode(tag.text)+ u'"' for tag in detail[1]])

    btih = details.xpath('div[@class="download"]/a')[0].get('href')[20:60].upper()

    description = unicode(details.xpath('div[@class="nfo"]/pre')[0].text_content()[:-2]) # [:-2] to remove '\t\t' from the end

    open(path + "/description.txt", 'w').write(description.encode('utf-8'))
    details_csv = open(path + "/details.csv", 'w')
    details_csv.write(u'\ufeff'.encode('utf-8')) # BOM
    csv_writer = csv.writer(details_csv)

    # Rating have been removed
    rating_positive = ''
    rating_negative = ''

    csv_writer.writerow(['Title', 'Type', 'Files', 'Size', 'IMDB', 'Spoken Languages', 'Texted Languages', 'Tags', 'Quality (+)', 'Quality (-)', 'Uploaded', 'By', 'User Type', 'Seeders', 'Leechers', 'Info Hash', 'Picture', 'Capture Date'])
    csv_writer.writerow([element.encode('utf-8') for element in [title,category,unicode(num_files),size,imdb,spoken,texted,tags,rating_positive,rating_negative,iso_timestamp,username,usertype,seeders,leechers,btih,picture,datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")]])
    return 200

if __name__ == '__main__':
	get_torrent_page(sys.argv[1], 'http')
