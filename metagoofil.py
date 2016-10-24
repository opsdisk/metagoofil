#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import google  # google >= 1.9.3, https://pypi.python.org/pypi/google
import os
import Queue
import random
import sys
import threading
import time
import urllib2


class Worker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            # Grab URL off the queue
            url = mg.queue.get()
            try:
                request = urllib2.Request(url)

                # Assign a User-Agent
                # No -u
                if mg.user_agent == 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)':
                    request.add_header('User-Agent', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
                # -u
                elif mg.user_agent is None:
                    request.add_header('User-Agent', random.choice(mg.random_user_agents))
                # -u "My custom user agent 2.0"
                else:
                    request.add_header('User-Agent', mg.user_agent)

                response = urllib2.urlopen(request, timeout=mg.url_timeout)

                # Download the file
                size = int(response.headers["Content-Length"])
                print("[+] Downloading file - [" + str(size) + " bytes] " + url)
                filename = str(url.split("/")[-1])
                with open(os.path.join(mg.save_directory, filename), 'wb') as fp:
                    fp.write(response.read())
                    fp.close()

                mg.total_bytes += size

            except:
                print("[-] Timed out after " + str(mg.url_timeout) + " seconds...can't reach url: " + url)

            mg.queue.task_done()


class Metagoofil:

    def __init__(self, domain, delay, save_links, url_timeout, search_max, download_file_limit, save_directory, number_of_threads, file_types, user_agent, download_files):
        self.domain = domain
        self.delay = delay
        self.save_links = save_links
        if self.save_links:
            self.html_links = open('html_links_' + get_timestamp() + '.txt', 'a')
        self.url_timeout = url_timeout
        self.search_max = search_max
        self.download_file_limit = download_file_limit
        self.save_directory = save_directory

        # Create queue and specify the number of worker threads.
        self.queue = Queue.Queue()
        self.number_of_threads = number_of_threads

        self.file_types = file_types

        self.user_agent = user_agent
        # Populate a list of random User-Agents
        if self.user_agent is None:
            with open('user_agents.txt') as fp:
                self.random_user_agents = fp.readlines()

        self.download_files = download_files
        self.total_bytes = 0

    def go(self):
        # Kickoff the threadpool.
        for i in range(self.number_of_threads):
            thread = Worker()
            thread.daemon = True
            thread.start()

        if "ALL" in self.file_types:
            from itertools import product
            from string import ascii_lowercase
            # Generate all three letter combinations
            self.file_types = [''.join(i) for i in product(ascii_lowercase, repeat=3)]

        for filetype in self.file_types:
            self.files = []  # Stores URLs with files, clear out for each filetype

            # Search for the files to download
            print("[*] Searching for " + str(self.search_max) + " ." + filetype + " files and waiting " + str(self.delay) + " seconds between searches")
            query = "filetype:" + filetype + " site:" + self.domain
            for url in google.search(query, start=0, stop=self.search_max, num=100, pause=self.delay, extra_params={'filter': '0'}, user_agent=google.get_random_user_agent()):
                self.files.append(url)

            # Since google.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount
            if len(self.files) > self.search_max:
                self.files = self.files[:-(len(self.files) - self.search_max)]

            # Download files if specified with -w switch
            if self.download_files:
                self.download()

            # Otherwise, just display them
            else:
                print("[*] Results: " + str(len(self.files)) + " ." + filetype + " files found")
                for file in self.files:
                    print(file)

            # Save links to output to file
            if self.save_links:
                for f in self.files:
                    self.html_links.write(f + "\n")

        self.html_links.close()

        if self.download_files:
            print("[+] Total download: " + str(self.total_bytes) + " bytes / " + str(self.total_bytes / 1024) + " KB / " + str(self.total_bytes / (1024 * 1024)) + " MB")

    def download(self):
        self.counter = 1
        for url in self.files:
            if self.counter <= self.download_file_limit:
                self.queue.put(url)
                self.counter += 1

        self.queue.join()


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp


def csv_list(string):
    return string.split(',')


# http://stackoverflow.com/questions/3853722/python-argparse-how-to-insert-newline-in-the-help-text
class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # This is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Metagoofil - Search and Download file_types', formatter_class=SmartFormatter)
    parser.add_argument('-d', dest='domain', action='store', required=True, help='Domain to search')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=7.0, help='Delay (in seconds) between searches.  If it\'s too small Google may block your IP, too big and your search may take a while.')
    parser.add_argument('-f', dest='save_links', action='store_true', default=False, help='Save the html links to html_links_<TIMESTAMP>.txt file')
    parser.add_argument('-i', dest='url_timeout', action='store', type=int, default=15, help='Number of seconds to wait before timeout for unreachable/stale pages (default 15)')
    parser.add_argument('-l', dest='search_max', action='store', type=int, default=100, help='Maximum results to search (default 100)')
    parser.add_argument('-n', dest='download_file_limit', default=100, action='store', type=int, help='Maximum number of files to download per filetype (default is 100)')
    parser.add_argument('-o', dest='save_directory', action='store', default=os.getcwd(), help='Directory to save downloaded files (default is cwd, ".")')
    parser.add_argument('-r', dest='number_of_threads', action='store', type=int, default=8, help='Number of search threads (default is 8)')
    parser.add_argument('-t', dest='file_types', action='store', required=True, type=csv_list, help='file_types to download (pdf,doc,xls,ppt,odp,ods,docx,xlsx,pptx).  To search all 17,576 three-letter file extensions, type "ALL"')
    parser.add_argument('-u', dest='user_agent', nargs='?', default='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', help='R|User-Agent for file retrieval against -d domain.\n'
                                                                                                                                                     'no -u = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"\n'
                                                                                                                                                     '-u = Randomize User-Agent\n'
                                                                                                                                                     '-u "My custom user agent 2.0" = Your customized User-Agent')
    parser.add_argument('-w', dest='download_files', action='store_true', default=False, help='Download the files, instead of just viewing search results')
    args = parser.parse_args()

    if not args.domain:
        print("[!] Specify a domain with -d")
        sys.exit()
    if not args.file_types:
        print("[!] Specify file types with -t")
        sys.exit()
    if (args.download_file_limit > 0) and (args.download_files is False):
        print("[+] Adding -w for you")
        args.download_files = True
    if args.save_directory:
        print("[*] Downloaded files will be saved here: " + args.save_directory)
        if not os.path.exists(args.save_directory):
            print("[+] Creating folder: " + args.save_directory)
            os.mkdir(args.save_directory)
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()
    if args.url_timeout < 0:
        print("[!] URL timeout (-i) must be greater than 0")
        sys.exit()
    if args.number_of_threads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit()

    #print(vars(args))
    mg = Metagoofil(**vars(args))
    mg.go()

    print("[+] Done!")
