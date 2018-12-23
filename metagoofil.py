#!/usr/bin/env python

# Standard Python libraries.
import argparse
import os
import queue
import random
import sys
import threading
import time

# Third party Python libraries.
# google == 2.0.1, module author changed import name to googlesearch
# https://github.com/MarioVilas/googlesearch/commit/92309f4f23a6334a83c045f7c51f87b904e7d61d
import googlesearch
import requests

# https://stackoverflow.com/questions/27981545/suppress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class DownloadWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            # Grab URL off the queue.
            url = mg.queue.get()

            try:
                headers = {}

                # Assign a User-Agent for each file request.
                # No -u
                if mg.user_agent == "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)":
                    headers["User-Agent"] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
                # -u
                elif mg.user_agent is None:
                    user_agent_choice = random.choice(mg.random_user_agents).strip()
                    headers["User-Agent"] = f"{user_agent_choice}"
                # -u "My custom user agent 2.0"
                else:
                    headers["User-Agent"] = mg.user_agent

                response = requests.get(url, headers=headers, verify=False, timeout=mg.url_timeout, stream=True)

                # Download the file.
                if response.status_code == 200:
                    try:
                        size = int(response.headers["Content-Length"])

                    except KeyError as e:
                        print(
                            f"[-] Exception for url: {url} -- {e} does not exist.  Extracting file size from response.content length."
                        )
                        size = len(response.content)

                    mg.total_bytes += size

                    print(f"[+] Downloading file - [{size} bytes] {url}")

                    # Strip any trailing /'s before extracting file name.
                    filename = str(url.strip("/").split("/")[-1])

                    with open(os.path.join(mg.save_directory, filename), "wb") as fh:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:  # Filter out keep-alive new chunks.
                                fh.write(chunk)

                else:
                    print(f"[-] URL {url} returned HTTP code {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"[-] Exception for url: {url} -- {e}")

            mg.queue.task_done()


class Metagoofil:
    """The Metagoofil Class"""

    def __init__(
        self,
        domain,
        delay,
        save_links,
        url_timeout,
        search_max,
        download_file_limit,
        save_directory,
        number_of_threads,
        file_types,
        user_agent,
        download_files,
    ):
        self.domain = domain
        self.delay = delay
        self.save_links = save_links
        if self.save_links:
            self.html_links = open(f"html_links_{get_timestamp()}.txt", "a")
        self.url_timeout = url_timeout
        self.search_max = search_max
        self.download_file_limit = download_file_limit
        self.save_directory = save_directory

        # Create queue and specify the number of worker threads.
        self.queue = queue.Queue()
        self.number_of_threads = number_of_threads

        self.file_types = file_types

        self.user_agent = user_agent
        # Populate a list of random User-Agents.
        if self.user_agent is None:
            with open("user_agents.txt") as fp:
                self.random_user_agents = fp.readlines()

        self.download_files = download_files
        self.total_bytes = 0

    def go(self):
        # Kickoff the threadpool.
        for i in range(self.number_of_threads):
            thread = DownloadWorker()
            thread.daemon = True
            thread.start()

        if "ALL" in self.file_types:
            from itertools import product
            from string import ascii_lowercase

            # Generate all three letter combinations.
            self.file_types = ["".join(i) for i in product(ascii_lowercase, repeat=3)]

        for filetype in self.file_types:
            # Stores URLs with files, clear out for each filetype.
            self.files = []

            # Search for the files to download.
            print(
                f"[*] Searching for {self.search_max} .{filetype} files and waiting {self.delay} seconds between searches"
            )
            query = f"filetype:{filetype} site:{self.domain}"
            for url in googlesearch.search(
                query,
                start=0,
                stop=self.search_max,
                num=100,
                pause=self.delay,
                extra_params={"filter": "0"},
                user_agent=self.user_agent,
            ):
                self.files.append(url)

            # Since googlesearch.search method retrieves URLs in batches of 100, ensure the file list only contains the requested amount.
            if len(self.files) > self.search_max:
                self.files = self.files[: -(len(self.files) - self.search_max)]

            # Download files if specified with -w switch.
            if self.download_files:
                self.download()

            # Otherwise, just display them.
            else:
                print(f"[*] Results: {len(self.files)} .{filetype} files found")
                for file_name in self.files:
                    print(file_name)

            # Save links to output to file.
            if self.save_links:
                for f in self.files:
                    self.html_links.write(f"{f}\n")
        if self.save_links:
            self.html_links.close()

        if self.download_files:
            print(
                "[+] Total download: {} bytes / {:.2f} KB / {:.2f} MB".format(
                    self.total_bytes, self.total_bytes / 1024, self.total_bytes / (1024 * 1024)
                )
            )

    def download(self):
        self.counter = 1
        for url in self.files:
            if self.counter <= self.download_file_limit:
                self.queue.put(url)
                self.counter += 1

        self.queue.join()


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime("%Y%m%d_%H%M%S", now)
    return timestamp


def csv_list(string):
    return string.split(",")


# http://stackoverflow.com/questions/3853722/python-argparse-how-to-insert-newline-in-the-help-text
class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith("R|"):
            return text[2:].splitlines()
        # This is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Metagoofil - Search and download specific filetypes", formatter_class=SmartFormatter
    )
    parser.add_argument("-d", dest="domain", action="store", required=True, help="Domain to search.")
    parser.add_argument(
        "-e",
        dest="delay",
        action="store",
        type=float,
        default=30.0,
        help="Delay (in seconds) between searches.  If it's too small Google may block your IP, too big and your search may take a while.  DEFAULT: 30.0",
    )
    parser.add_argument(
        "-f",
        dest="save_links",
        action="store_true",
        default=False,
        help="Save the html links to html_links_<TIMESTAMP>.txt file.",
    )
    parser.add_argument(
        "-i",
        dest="url_timeout",
        action="store",
        type=int,
        default=15,
        help="Number of seconds to wait before timeout for unreachable/stale pages.  DEFAULT: 15",
    )
    parser.add_argument(
        "-l", dest="search_max", action="store", type=int, default=100, help="Maximum results to search.  DEFAULT: 100"
    )
    parser.add_argument(
        "-n",
        dest="download_file_limit",
        default=100,
        action="store",
        type=int,
        help="Maximum number of files to download per filetype.  DEFAULT: 100",
    )
    parser.add_argument(
        "-o",
        dest="save_directory",
        action="store",
        default=os.getcwd(),
        help='Directory to save downloaded files.  DEFAULT is cwd, "."',
    )
    parser.add_argument(
        "-r",
        dest="number_of_threads",
        action="store",
        type=int,
        default=8,
        help="Number of search threads.  DEFAULT: 8",
    )
    parser.add_argument(
        "-t",
        dest="file_types",
        action="store",
        required=True,
        type=csv_list,
        help='file_types to download (pdf,doc,xls,ppt,odp,ods,docx,xlsx,pptx).  To search all 17,576 three-letter file extensions, type "ALL"',
    )
    parser.add_argument(
        "-u",
        dest="user_agent",
        nargs="?",
        default="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        help="R|User-Agent for file retrieval against -d domain.\n"
        'no -u = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"\n'
        "-u = Randomize User-Agent\n"
        '-u "My custom user agent 2.0" = Your customized User-Agent',
    )
    parser.add_argument(
        "-w",
        dest="download_files",
        action="store_true",
        default=False,
        help="Download the files, instead of just viewing search results.",
    )
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
        print(f"[*] Downloaded files will be saved here: {args.save_directory}")
        if not os.path.exists(args.save_directory):
            print(f"[+] Creating folder: {args.save_directory}")
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

    # print(vars(args))
    mg = Metagoofil(**vars(args))
    mg.go()

    print("[+] Done!")
