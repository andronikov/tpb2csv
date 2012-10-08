#!/usr/bin/env python

import sys
import os

import requests
import lxml.html
from lxml.html.soupparser import fromstring

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

def get_comments(torrent_id, protocol):
    print "Getting comments:",
    r = requests.get(protocol + "://thepiratebay.se/ajax_details_comments.php?id=" + str(torrent_id), headers={'user-agent': 'Archiving The Pirate Bay!'})
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

    root = fromstring(decode_html(r.content))

    comment_array = root.xpath('.//div[starts-with(@id, "comment-")]')

    for comment in comment_array:
        if comment.find('p/a/img') is None:
            usertype = ''
        else:
            usertype = '[' + comment.find('p/a/img').get('title')[0] + ']'

        try:
            username = comment.find('p/a').get('title')[7:]
            timestamp = comment.find('p').text_content()[-22:-6]
            text = unicode(comment.find('div[@class="comment"]').text_content()[1:-1]).replace(u'\xa0', ' ')
            
            comment_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")

            cleaned_up_data = []
            for i in [usertype, username, comment_date.isoformat()[:-3] + "Z", text]:
                cleaned_up_data.append(i.encode('utf-8', 'replace'))
            csv_writer.writerow(cleaned_up_data)
        except AttributeError:
            pass

if __name__ == '__main__':
	get_comments(sys.argv[1], 'http')
