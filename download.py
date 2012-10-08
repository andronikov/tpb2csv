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
import HTMLParser
import torrent_page
import torrent_page_old
import torrent_page_bs
import filelist
import filelist_old
import filelist_bs
import comments
import comments_old
import comments_bs
import requests
import datetime

def main():
    if not os.path.exists("logs/"):
        os.makedirs("logs/")
    if not os.path.exists("logs/" + str(int(torrent_id) / 100000) + "xxxxx/"):
        os.makedirs("logs/" + str(int(torrent_id) / 100000) + "xxxxx/")
    time_log = open("logs/" + str(int(torrent_id) / 100000) + "xxxxx/" + "download.log", 'a')
    error_file = open("logs/" + str(int(torrent_id) / 100000) + "xxxxx/" + "errors.log", 'a')

    while True:
        try:
            try:
                tp_status_code = torrent_page.get_torrent_page(torrent_id, protocol)

            except IndexError:
                print "Falling back to BeautifulSoup for torrent page:"
                tp_status_code = torrent_page_bs.get_torrent_page(torrent_id, protocol)
            if (tp_status_code == 200):
                try:
                    filelist.get_filelist(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for filelist:"
                    filelist_bs.get_filelist(torrent_id, protocol)
                try:
                    comments.get_comments(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for comments:"
                    comments_bs.get_comments(torrent_id, protocol)

            except ValueError:
                print "Falling back to BeautifulSoup for torrent page:"
                tp_status_code = torrent_page_old.get_torrent_page(torrent_id, protocol)
            if (tp_status_code == 200):
                try:
                    filelist.get_filelist(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for filelist:"
                    filelist_old.get_filelist(torrent_id, protocol)
                try:
                    comments.get_comments(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for comments:"
                    comments_old.get_comments(torrent_id, protocol)
            elif (tp_status_code == 404):
                print "Skipping filelist..."
                print "Skipping comments..."
            else:
                print "ERROR: HTTP " + str(tp_status_code)
                error_file.write(datetime.datetime.utcnow().strftime("[%Y-%m-%dT%H:%M:%SZ]") + ' ' + str(torrent_id) + ": ERROR: HTTP " + str(tp_status_code) + '\n')
                error_file.flush()
                sys.exit(1)
            time_log.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " " + str(tp_status_code) + '\n')
            time_log.flush()
            break # Success! Break out of the while loop
        except requests.exceptions.ConnectionError:
            print "Connection error. Retrying..."
            error_file.write(datetime.datetime.utcnow().strftime("[%Y-%m-%dT%H:%M:%SZ]") + ' ' + str(torrent_id) + ": Connection error" + '\n')
            error_file.flush()
            tp_status_code = torrent_page.get_torrent_page(torrent_id, protocol)
            if (tp_status_code == 200):
                filelist.get_filelist(torrent_id, protocol)
                try:
                    comments.get_comments(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for comments:"
                    comments_old.get_comments(torrent_id, protocol)
            else:
                print "Skipping filelist..."
                print "Skipping comments..."
            time_log.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " " + str(tp_status_code) + '\n')
            time_log.flush()
            break # Success! Break out of the while loop
        except AttributeError:
            print "Malformed download. Retrying..."
            error_file.write(datetime.datetime.utcnow().strftime("[%Y-%m-%dT%H:%M:%SZ]") + ' ' + str(torrent_id) + ": Malformed download" + '\n')
            error_file.flush()
            tp_status_code = torrent_page.get_torrent_page(torrent_id, protocol)
            if (tp_status_code == 200):
                filelist.get_filelist(torrent_id, protocol)
                try:
                    comments.get_comments(torrent_id, protocol)
                except ValueError:
                    print "Falling back to BeautifulSoup for comments:"
                    comments_old.get_comments(torrent_id, protocol)
            else:
                print "Skipping filelist..."
                print "Skipping comments..."
            time_log.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " " + str(tp_status_code) + '\n')
            time_log.flush()
            break # Success! Break out of the while loop
        except HTMLParser.HTMLParseError:
            time_log.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + ' ' + str(torrent_id) + " BAD" + '\n')
            time_log.flush()
            break

if (len(sys.argv) == 1):
    print "USAGE: " + sys.argv[0] + " (--https) STARTING_ID ENDING_ID"
    print "USAGE: " + sys.argv[0] + " (--https) SINGLE_ID"
    sys.exit(0)

https = (sys.argv[1] == '--https')

if https:
    offset = 1
    protocol = 'https'
else:
    offset = 0
    protocol = 'http'

if (len(sys.argv) == 2+offset):
    torrent_id = sys.argv[1+offset]
    print torrent_id
    main()
    print str(float(100000 - (torrent_id % 100000) ) / 1000.0) + "%"
    
elif (len(sys.argv) == 3+offset):
    if (int(sys.argv[1+offset]) > (int(sys.argv[2+offset])+1)):
        for torrent_id in range(int(sys.argv[1+offset]),int(sys.argv[2+offset])-1, -1):
            print torrent_id
            main()
            print str(float(100000 - (torrent_id % 100000) ) / 1000.0) + "%"
    else:
        for torrent_id in range(int(sys.argv[1+offset]),int(sys.argv[2+offset])+1):
            print torrent_id
            main()
            print str(float(100000 - (torrent_id % 100000) ) / 1000.0) + "%"
            
elif (len(sys.argv) > 3 and not https):
    print "ERROR: Too many arguments"
