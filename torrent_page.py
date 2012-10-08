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
from lxml.html.soupparser import fromstring
from lxml.html import tostring


from datetime import datetime
import unicodecsv

from BeautifulSoup import UnicodeDammit

def decode_html(html_string):
    converted = UnicodeDammit(html_string, isHTML=True)
    if not converted.unicode:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.triedEncodings))
    # print converted.originalEncoding
    return converted.unicode


def get_torrent_page(torrent_id, protocol):
    r = requests.get(protocol + "://thepiratebay.se/torrent/" + str(torrent_id))
    print "Getting torrent page:",
    print r.status_code

    if (r.status_code != 200):
        return r.status_code

    html = fromstring(decode_html(r.content))

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
        title = unicode(html.xpath('//div[@id="detailsframe"]/div[@id="title"]')[0].text[3:-1])
    except IndexError:
        open("logs/" + str(int(torrent_id) / 100000) + "xxxxx/" + "download.log", 'a').write(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " " + str('BAD') + '\n')
    details = html.xpath('//div[@id="details"]')[0]

    one_column = details.xpath('div[@class="torpicture"]/img') != []
    if one_column:
        picture = details.xpath('div[@class="torpicture"]/img')[0].get('src')
    else:
        picture = ''

#    column1 = fromstring(tostring(details.xpath('dl[@class="col1"]')[0]).replace('<br>', ''))[0]
    column1 = details.xpath('dl[@class="col1"]')[0]
    column1_tags = zip(column1.findall('dt'), column1.findall('dd'))
    if not one_column:
#        column2 = fromstring(tostring(details.xpath('dl[@class="col2"]')[0]).replace('<br>', ''))[0]
        column2 = details.xpath('dl[@class="col2"]')[0]
        column2_tags = zip(column2.findall('dt'), column2.findall('dd'))

    category = column1_tags[0][1][0].get('href')[-3:]

    size = column1_tags[2][1].text.replace(u'\xa0', ' ')

    num_files = int(column1_tags[1][1][0].text)

    offset = 0
    has_imdb = False
    has_spoken = False
    has_texted = False
    has_tags = False

    try:
        if column1_tags[3+offset][0].text == 'Info:':
            imdb = column1_tags[3+offset][1][0].get('href')
            offset += 1
            has_imdb = True
        else:
            imdb = ''
    except IndexError:
        imdb = ''

    try:
        if column1_tags[3+offset][0].text == 'Spoken language(s):':
            spoken = column1_tags[3+offset][1].text
            offset += 1
            has_spoken = True
        else:
            spoken = ''
    except IndexError:
        spoken = ''

    try:
        if column1_tags[3+offset][0].text == 'Texted language(s):':
            texted = column1_tags[3+offset][1].text
            offset += 1
            has_texted = True
        else:
            texted = ''
    except IndexError:
        texted = ''

    try:
        tags = [tag.text for tag in column1_tags[3+offset][1]]
        tag_string = u','.join([u'"' + unicode(tag)+ u'"' for tag in tags])
        if tag_string != '':
            offset += 1
            has_tags = True
    except IndexError:
        tag_string = u''

#    print 'Has Picture:', one_column
#    print 'Has IMDB:   ', has_imdb#, '(' + offset + ')'
#    print 'Has Spoken: ', has_spoken#, '(' + offset + ')'
#    print 'Has Texted: ', has_texted#, '(' + offset + ')'
#    print 'Has Tags:   ', has_tags#, '(' + offset + ')'

    if one_column:
        rating_str = column1.xpath('dd[@id="rating"]')[0].text[3:-2]
        timestamp = column1_tags[4+offset][1].text
        username = column1_tags[5+offset][1][0].text # Syntax: [row][column (title or data)][0 (for selecting user <a> tag)]
        if len(column1_tags[5+offset][1]) == 2:
            usertype = '[' + column1_tags[5+offset][1][1].get('title')[0] + ']'
        else:
            usertype = ''
        seeders = int(column1_tags[6+offset][1].text)
        leechers = int(column1_tags[7+offset][1].text)
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
    details_csv = open(path + "/details.csv", 'w')
    details_csv.write(u'\ufeff'.encode('utf-8')) # BOM
    csv_writer = unicodecsv.writer(details_csv, encoding='utf-8')

    csv_writer.writerow(['Title', 'Type', 'Files', 'Size', 'IMDB', 'Spoken Languages', 'Texted Languages', 'Tags', 'Quality (+)', 'Quality (-)', 'Uploaded', 'By', 'User Type', 'Seeders', 'Leechers', 'Info Hash', 'Picture', 'Capture Date'])

    cleaned_up_data = []
    for element in [title,category,num_files,size,imdb,spoken,texted,tag_string,rating_positive,rating_negative,iso_timestamp,username,usertype,seeders,leechers,btih,picture,datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")]:
        cleaned_up_data.append(unicode(element).encode('utf-8', 'replace'))

    csv_writer.writerow(cleaned_up_data)
    return 200

if __name__ == '__main__':
	get_torrent_page(sys.argv[1], 'http')
