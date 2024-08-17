#!/usr/bin/env python3

# Import necessary modules
from argparse import ArgumentParser, RawTextHelpFormatter
import sys, tldextract
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Initialize argument parser
parser = ArgumentParser(add_help=False, formatter_class=RawTextHelpFormatter)

# Define command-line arguments
parser.add_argument('-u', '--url', nargs='?', type=str, default='', help="Single URL to edit")
parser.add_argument('-l', '--list', nargs='?', type=str, default='', help="List of URLs to edit")
parser.add_argument('-p', '--parameters', nargs='?', type=str, default='', help="Parameter wordlist to fuzz")
parser.add_argument('-c', '--chunk', type=int, default=15, help="Chunk to fuzz the parameters. [default: 15]")
parser.add_argument('-v', '--value', action='append', help='Value for parameters to fuzz')
parser.add_argument('-vf', '--value_file', nargs='?', type=str, default='', help="List of Values for parameters to fuzz")
parser.add_argument('-gs', '--generate_strategy', choices=['normal', 'ignore', 'combine', 'all'], default='all', help="""Select the mode strategy from the available choice:
        - Normal: Remove all parameters and put the wordlist
        - Combine: Pitchfork combine on the existing parameters
        - Ignore: Don't touch the URL and put the wordlist
        - All: All in one method""")
parser.add_argument('-vs', '--value_strategy', choices=['replace', 'suffix'], default='replace', help="""Select the mode strategy from the available choices:
        - Replace: Replace the value with gathered value
        - Suffix: Append the value to the end of the parameters""")
parser.add_argument('-o', '--output', type=str, default='', help="Output results")
parser.add_argument('-s', '--silent', help="Silent mode", action="store_true")
parser.add_argument('-h', '--help', action='store_true', help='Display help message')

# Parse command-line arguments
args = parser.parse_args()

# Define color class for output
class colors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    NOCOLOR = '\033[0m'

# Show help message and exit if help flag is set
if args.help:
    parser.print_help()
    sys.exit()

# Function to display banner
def banner(colors):
    bannerm = """
   _____ ____ _____ ____   ___   ___  _   _ _____  __  _____  
| ____| |   | ____/ ___|_   _|  _ \ / _ \ / _ \| \ | | ____| \ \/ / _ \ 
|  _| | |   |  _|| |     | | | |_) | | | | | | |  \| |  _|    \  / (_) |
| |___| |___| |__| |___  | | |  _ <| |_| | |_| | |\  | |___   /  \\__, |
|_____|_____|_____\____| |_| |_| \_\\___/ \___/|_| \_|_____| /_/\_\ /_/ 
    """
    print(bannerm)



# Check if value or value_file is provided, else show an error and exit
if not args.value and not args.value_file:
    print()
    banner(colors)
    print(colors.RED + "[-] Program exiting: no input provided" + colors.NOCOLOR)
    print(colors.RED + "[+] Please use --help/-h for the list of available options." + colors.NOCOLOR)
    print()
    print()
    sys.exit()

# Display banner if silent mode is not enabled
if not args.silent:
    banner(colors)

# Define Ignore class for 'ignore' strategy
class Ignore:
    def __init__(self, urls, payload, wordlist):
        self.urls = urls
        self.payload = payload
        self.parameters = wordlist

    # Update URL parameters by removing and adding specified parameters
    def update_url_parameters(self, url, payload):
        url_parts = urlparse(url)
        query_params = parse_qs(url_parts.query)

        for param in self.parameters:
            if param in query_params:
                del query_params[param]

        start = 0
        end = len(self.parameters)
        step = args.chunk
        for i in range(start, end, step):
            x = i

            for param in self.parameters[x:x+step]:
                query_params[param] = [payload]

            encoded_params = urlencode(query_params, doseq=True)
            updated_url_parts = list(url_parts)
            updated_url_parts[4] = encoded_params

            print(urlunparse(updated_url_parts))
            if not args.output == '':
                with open(args.output, 'a') as f:
                    f.write(urlunparse(updated_url_parts)+'\n')
            query_params.clear()
            query_params = parse_qs(url_parts.query)

    # Method for 'ignore' mode
    def ignore_mode(self):
        try:
            if self.parameters:
                for url in self.urls:
                    for payload in self.payload:
                        self.update_url_parameters(url, payload)
            else:
                print()
                print(colors.RED + "Please enter your parameter list as a text file !!!" + colors.NOCOLOR)
                print()
                print()
                print()
                parser.print_help()
                sys.exit()
        except Exception as e:
            print(e)

# Define Normal class for 'normal' strategy
class Normal:
    def __init__(self, urls, payloads, parameters=None):
        self.urls = urls
        self.payload = payloads
        self.wordlist = parameters

    # Replace URL parameters with payload
    def replace_parameters(self, url, payload):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        query_params_copy = query_params.copy()

        if self.wordlist:
            for param in query_params_copy.keys():
                del query_params[param]

            start = 0
            end = len(self.wordlist)
            step = args.chunk
            for i in range(start, end, step):
                x = i
                for param in self.wordlist[x:x+step]:
                    query_params[param] = payload

                new_query = urlencode(query_params, doseq=True)
                new_parsed_url = parsed_url._replace(query=new_query)
                new_url = urlunparse(new_parsed_url)

                print(new_url)
                if not args.output == '':
                    with open(args.output, 'a') as f:
                        f.write(new_url+'\n')
                query_params.clear()
        else:
            for param in query_params:
                query_params[param] = payload

            new_query = urlencode(query_params, doseq=True)
            new_parsed_url = parsed_url._replace(query=new_query)
            new_url = urlunparse(new_parsed_url)

            print(new_url)
            if not args.output == '':
                with open(args.output, 'a') as f:
                    f.write(new_url+'\n')

    # Method for 'normal' mode
    def normal_mode(self):
        try:
            for url in self.urls:
                for payload in self.payload:
                    self.replace_parameters(url, payload)
        except Exception as e:
            print(e)

# Define Combine class for 'combine' strategy
class Combine:
    def __init__(self, urls, payloads, parameters=None):
        self.urls = urls
        self.payload = payloads
        self.parameters = parameters

    # Update URL parameters by combining with payload
    def update_url_parameters(self, url, payload):
        res = []
        start = 0
        end = len(self.parameters)
        step = args.chunk
        query_params = {}
        query_params.clear()
        for i in range(start, end, step):
            url_parts = urlparse(url)
            query_params = parse_qs(url_parts.query)
            x = i
            for param in self.parameters[x:x+step]:
                query_params.update({param: payload})
            res.append(query_params)
            query_params = parse_qs(url_parts.query)

        for r in res:
            encoded_params = urlencode(r, doseq=True)
            updated_url_parts = list(url_parts)
            updated_url_parts[4] = encoded_params
            print(urlunparse(updated_url_parts))

            if not args.output == '':
                with open(args.output, 'a') as f:
                    f.write(urlunparse(updated_url_parts)+'\n')

    # Replace or suffix URL parameters
    def replace_suffix(self, url, param, payload):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        for key, values in query_params.items():
            for i in range(len(values)):
                if values[i] == param[0]:
                    if args.value_strategy == "suffix":
                        values[i] = param[0] + payload
                    else:
                        values[i] = payload

        new_query_string = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=new_query_string))

        if self.parameters:
            for payload in self.payload:
                self.update_url_parameters(new_url, payload)
                break

    # Method for 'combine' mode
    def combine(self):
        try:
            for url in self.urls:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query, keep_blank_values=True)
                for keys, values in query_params.items():
                    for payload in self.payload:
                        self.replace_suffix(url, values, payload)
        except Exception as e:
            print(e)

# Initialize list to store results
results = []

# Generate URLs based on selected strategy
def generators(url, values, parameters):
    if args.generate_strategy == "normal":
        normal = Normal(url, values, parameters)
        normal.normal_mode()
    elif args.generate_strategy == "ignore":
        ignore = Ignore(url, values, parameters)
        ignore.ignore_mode()
    elif args.generate_strategy == "combine":
        combine = Combine(url, values, parameters)
        combine.combine()
    else:
        normal = Normal(url, values, parameters)
        normal.normal_mode()
        ignore = Ignore(url, values, parameters)
        ignore.ignore_mode()
        combine = Combine(url, values, parameters)
        combine.combine()

# Clean and standardize URL
def clean_url(url):
    full_url = ""
    ext = tldextract.extract(url)

    if ext.subdomain:
        ext_url = ext.subdomain + '.' + ext.domain + '.' + ext.suffix
    else:
        ext_url = ext.domain + '.' + ext.suffix

    if not url.startswith("http://") and not url.startswith("https://"):
        full_url = "https://{}".format(url)
    else:
        full_url = url

    if not "?" in full_url or not "%3F" in full_url or not "%3f" in full_url:
        if 'https:' in full_url:
            if full_url == 'https://'+ext_url:
                if not full_url.endswith('/'):
                    full_url = "{}/".format('https://'+ext_url)
                else:
                    pass
            else:
                pass
        else:
            if full_url == 'http://'+ext_url:
                if not full_url.endswith('/'):
                    full_url = "{}/".format('http://'+ext_url)
                else:
                    pass
            else:
                pass
    else:
        pass
    return full_url

# Retrieve payloads from file or argument
def get_payloads():
    payloads = []
    if args.value_file:
        with open(args.value_file, 'r') as file:
            payloads = file.readlines()
        payloads = [line.replace('\n', '') for line in payloads]

    if args.value:
        for payload in args.value:
            payloads.append(payload)

    return payloads

# Retrieve parameters from file
def get_parameters():
    with open(args.parameters, 'r') as file:
        parameters = file.readlines()
    parameters = [line.replace('\n', '') for line in parameters]
    return parameters

# Run the main process
def run(complete_urls):
    payloads = get_payloads()
    parameters = []
    if args.parameters != "":
        parameters = get_parameters()
        generators(complete_urls, payloads, parameters)
    else:
        generators(complete_urls, payloads, parameters)

# Handle different input options (list, url, or stdin)
if args.list != '':
    try:
        urls = [line.strip() for line in open(args.list)]
        urls = list(set(urls))

        complete_urls = []

        for url in urls:
            full_url = clean_url(url)
            complete_urls.append(full_url)

        run(complete_urls)

    except Exception as e:
        print(e)

elif args.url != '':
    try:
        url = args.url
        complete_urls = []
        full_url = clean_url(url)
        complete_urls.append(full_url)

        run(complete_urls)

    except Exception as e:
        print(e)

else:
    if not sys.stdin.isatty():
        input_urls = [line.strip() for line in sys.stdin.readlines()]
        if len(input_urls) == 1:
            try:
                complete_urls = []

                url = input_urls[0]
                if url:
                    if ',' in url:
                        url = url.split(',')[0]

                    full_url = clean_url(url)
                    complete_urls.append(full_url)

                    run(complete_urls)
                else:
                    parser.print_help()
                    sys.exit()
            except Exception as e:
                print(e)
        else:
            try:
                input_urls = list(set(input_urls))
                complete_urls = []

                for url in input_urls:
                    full_url = clean_url(url)
                    complete_urls.append(full_url)

                run(complete_urls)
            except Exception as e:
                print(e)
    else:
        print()
        print(colors.RED + '[-] ' + colors.NOCOLOR + 'Provide an URL or a file')