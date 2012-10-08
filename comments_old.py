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
import re
from datetime import datetime, date, time
import unicodecsv
import os

def get_comments(torrent_id, protocol):
    print "Getting comments:",
    r = requests.get(protocol + "://thepiratebay.se/ajax_details_comments.php?id=" + str(torrent_id), headers={'user-agent': 'tpb2csv'})
    if (r.status_code == 200):
        if (r.content == ''):
            print str(r.status_code) + ", but no comments"
            return 0
        else:
            print r.status_code

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

    comments_csv = open(path + "/comments.csv", 'w')
    comments_csv.write(u'\ufeff'.encode('utf-8')) # BOM
    csv_writer = unicodecsv.writer(comments_csv, encoding='utf-8')
    csv_writer.writerow(['User Type', 'Username', 'Date', 'Text'])
    soup = BeautifulSoup(r.content)
    comment_array = soup.find_all(id=re.compile("comment-"))
    for comment in comment_array:
        if comment.a.img:
            usertype = '[' + comment.a.img['title'][0] + ']'
        else:
            usertype = ''
        username = re.sub(r'\xa0', '', comment.find(href=re.compile("/user/")).get_text())
        text = unicode(comment.find("div", {"class": "comment"}).get_text())
        timestamp = comment.find(text=re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"))[4:-6] # The [4:-6] is to trim away the cruft from "at YYYY-MM-DD HH:MM CET:" to just "YYYY-MM-DD HH:MM"
        post_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        cleaned_up_data = []
        for i in [usertype, re.sub(r'\s', '', username), post_date.isoformat()[:-3] + "Z", text[1:-1]]:
            cleaned_up_data.append(i.encode('utf-8', 'replace'))
        csv_writer.writerow(cleaned_up_data)

if __name__ == '__main__':
	get_comments(sys.argv[1], 'http')
