# Metagoofil

## Introduction

One of the best tools for conducting document and metadata reconnaissance during a pen test is
[metagoofil](http://www.edge-security.com/metagoofil.php), written by Christian Martorella
[@laramies](http://twitter.com/laramies) of the [Edge-Security Group](http://www.edge-security.com/).  The source code
can be found here: [https://github.com/laramies/metagoofil](https://github.com/laramies/metagoofil), but it comes with
Kali by default.  The tool hasn't been updated in a couple of years and could use some TLC.

## tl;dr

New code is here, take it for a spin: <https://github.com/opsdisk/metagoofil>

## Installation

Clone the git repository and install the requirements

```bash
git clone https://github.com/opsdisk/metagoofil
cd metagoofil
virtualenv -p python3 .venv  # If using a virtual environment.
source .venv/bin/activate  # If using a virtual environment.
pip install -r requirements.txt
```

## Docker Installation & Usage
```bash
git clone https://github.com/opsdisk/metagoofil
cd metagoofil
docker build -t metagoofil .
# This will save the files in your current directory.
docker run -v $PWD:/data metagoofil -d kali.org -t pdf
```

## metagoofil

There are two parts to Metagoofil.  The first part is the ability to search Google for specific types of files being
publicly hosted on a domain and download them to your local box.  For instance, it uses this Google query to find all
the .pdf files being hosted on example.com and downloads a local copy

```none
site:example.com filetype:pdf
```

The second part of metagoofil is metadata extraction which searches for users, software, file paths, and emails in the
files and documents.

## File Download Rewrite

I rewrote the Google search and download functionality.  The original metagoofil uses a custom `googlesearch.py` module
which does not return legitimate or valid results all the time.  For example, it considers this a URL:

```none
[1/10] /webhp?hl=en
    [x] Error downloading /webhp?hl=en
```

There is a python package, appropriately called "google" (<https://pypi.python.org/pypi/google>) that abstracts the
searching and returning of valid URLs.  

The `googlesearch` package can be installed using pip

```bash
pip3 install -r requirements.txt
```

The full `googlesearch` package documentation can be found [here](http://pythonhosted.org/google/), but the parameters
we care about are:

```none
query (str) - Query string. Must NOT be url-encoded.
num (int) - Number of results per page.
start (int) - First result to retrieve.
stop (int) - Last result to retrieve. Use None to keep searching forever.
pause (float) - Lapse to wait between HTTP requests. A lapse too long will make the search slow, but a lapse too short
    may cause Google to block your IP. Your mileage may vary!
```

The code snippet below from the updated metagoofil.py takes care of searching Google for a specified domain and file
type, and returns a reliable and accurate list of URLs, exactly what we need!

```python
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

# Since googlesearch.search method retrieves URLs in batches of 100, ensure the file list only contains the
# requested amount.
if len(self.files) > self.search_max:
    self.files = self.files[: -(len(self.files) - self.search_max)]
```

I hardcoded the `num` parameter to return the most results per page, and just trim off any extra URLs if the user is
seeking less than 100 results.

This package will handle all the logic and heavy lifting of accurately searching Google, instead of relying on
custom-written search code.

The remaining updates deal with the switches.  The same switches were kept as in the original metagoofil to avoid
confusion, with new ones also added.  

The `-f` switch writes all the links to a date-time stamped .txt file instead of an HTML file.  This allows for quick
copy/paste or as an input file for other downloading binaries like curl or wget.

For grins, another addition is that the `-t` file type switch recognizes "ALL" which will search all 17,576 three-letter
file extensions.  A search would likely take a while and you should plan accordingly.

~~The maximum file download switch, `-m`, allows you to only download files that are less than that maximum value in~~
~~bytes, with 5000000 being the default (about 5 MB).~~ (Removed the switch on July 12, 2016 since it was retrieving the
file twice, once to check the size, then again if it was within the max value...seemed redundant.)

The addition of the `-e` delay switch allows you to specify the time delay in seconds between searches.  If you request
searches too quickly, Google will think you are a script or bot and will block your IP address for a while.  Experiment
to see what works best for you.

Lastly, the `-r` switch allows you to specify the number of threads to use when downloading files.  Note that one
network appliance / DDoS cloud solution detected the script as a bot and returned a 188 byte HTML file stating:

```none
The requested URL was rejected. Please consult with your administrator.

Your support ID is: 1234567890
```

If that happens, just set the number of threads to 1...it will take longer but you will not get blocked.

Added the `-u` user agent switch to customize the User-Agent used to retrieve files.  If no `-u` is provided, then the
User-Agent for every file download is `Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)`.  If
only `-u` is provided, a random User-Agent from user_agents.txt will be picked for **each** file request.  Lastly, a
custom User-Agent can be added by providing a string after the `-u`...for example `-u "My custom user agent 2.0"`.

## Metadata Extraction

Metagoofil is supposed to allow local file metadata analysis, using the `-h yes` switch, but it doesn't usually work for
me if I'm running it after acquiring the files. Currently, I use `exiftool` to extract any metadata I care about in
files and it's good enough.

```bash
exiftool -r *.doc | egrep -i "Author|Creator|Email|Producer|Template" | sort -u
```

## Conclusion

All of the code can be found on the Opsdisk Github repository here: <https://github.com/opsdisk/metagoofil>.  Comments,
suggestions, and improvements are always welcome.  Be sure to follow [@opsdisk](https://twitter.com/opsdisk) on Twitter
for the latest updates.
