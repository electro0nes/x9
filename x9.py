import argparse
import json
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def print_banner():
    banner = """
    ============================================================
    Electro0ne X9 - Bug Bounty Vulnerability Discovery Tool
    ============================================================
    """
    print(banner)

def read_parameters(param_source):
    if param_source.startswith('file:'):
        # Read parameters from a file
        file_path = param_source[5:]  # Remove the 'file:' prefix
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
    else:
        # Directly use the comma-separated parameters
        return param_source.split(',')

def fuzz_parameters(url, params, chunk_size, value, value_list, strategy, value_strategy):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    generated_urls = set()

    if strategy == 'normal':
        # Normal mode: Generate URLs with parameters in chunks
        if chunk_size > 1:
            # Generate URLs for each chunk of parameters
            for i in range(0, len(params), chunk_size):
                chunk = params[i:i + chunk_size]
                all_params_with_value = [f"{param}={value}" for param in chunk]
                normal_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{'&'.join(all_params_with_value)}"
                generated_urls.add(normal_url)
        else:
            # Generate a single URL with all parameters
            all_params_with_value = [f"{param}={value}" for param in params]
            normal_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{'&'.join(all_params_with_value)}"
            generated_urls.add(normal_url)

    elif strategy == 'combine':
        if value_strategy == 'suffix':
            for param in query_params.keys():
                combined_params = query_params.copy()
                for key in combined_params:
                    if key == param:
                        combined_params[key] = combined_params[key][0] + value
                    else:
                        combined_params[key] = combined_params[key][0]
                combined_url = urlunparse(parsed_url._replace(query=urlencode(combined_params, doseq=True)))
                generated_urls.add(combined_url)

    elif strategy == 'ignore':
        # Ignore mode: Append all parameters from the list with the given value
        if chunk_size > 1:
            for i in range(0, len(params), chunk_size):
                chunk = params[i:i + chunk_size]
                param_pairs = [f"{param}={value}" for param in chunk]
                ignore_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{parsed_url.query}&{'&'.join(param_pairs)}"
                generated_urls.add(ignore_url)
        else:
            param_pairs = [f"{param}={value}" for param in params]
            ignore_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{parsed_url.query}&{'&'.join(param_pairs)}"
            generated_urls.add(ignore_url)

    elif strategy == 'all':
        # Apply all strategies one by one
        generated_urls.update(fuzz_parameters(url, params, chunk_size, value, value_list, 'normal', value_strategy))
        generated_urls.update(fuzz_parameters(url, params, chunk_size, value, value_list, 'combine', value_strategy))
        generated_urls.update(fuzz_parameters(url, params, chunk_size, value, value_list, 'ignore', value_strategy))

    if value_strategy == 'suffix':
        # Apply Suffix strategy on all parameters
        for param in query_params.keys():
            suffix_params = query_params.copy()
            suffix_params[param] = suffix_params[param][0] + value
            suffix_url = urlunparse(parsed_url._replace(query=urlencode(suffix_params, doseq=True)))
            generated_urls.add(suffix_url)

    elif value_strategy == 'replace':
        # Apply Replace strategy on all parameters
        for param in query_params.keys():
            replace_params = query_params.copy()
            replace_params[param] = value
            replace_url = urlunparse(parsed_url._replace(query=urlencode(replace_params, doseq=True)))
            generated_urls.add(replace_url)

    return generated_urls

def format_url(url, params):
    # URL-encode parameters
    encoded_params = urlencode(params, doseq=True)
    return f"{url}?{encoded_params}" if encoded_params else url

def send_get_request(url):
    try:
        response = requests.get(url)
        print(f"GET request to {url} returned status code {response.status_code}")
    except requests.RequestException as e:
        print(f"GET request failed: {e}")

def send_post_request(url, data):
    try:
        response = requests.post(url, data=data)
        print(f"POST request to {url} with data {data} returned status code {response.status_code}")
    except requests.RequestException as e:
        print(f"POST request failed: {e}")

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Electro0ne X9 - Bug Bounty Vulnerability Discovery Tool")

    # Switches
    parser.add_argument('-u', '--url', help="Single URL to target")
    parser.add_argument('-l', '--list', help="List of URLs to target")
    parser.add_argument('-p', '--params', help="File or comma-separated list of parameters to fuzz")
    parser.add_argument('-c', '--chunk', help="Chunk size of parameters", type=int, default=15)
    parser.add_argument('-v', '--value', help="Single value for fuzzing", required=True)
    parser.add_argument('-vf', '--value-list', help="List of values for fuzzing")
    parser.add_argument('-gs', '--generate_strategy', choices=['normal', 'ignore', 'combine', 'all'], default='all', help="""Select the mode strategy from the available choice:
        - Normal: Remove all parameters and put the wordlist
        - Combine: Pitchfork combine on the existing parameters
        - Ignore: Don't touch the URL and put the wordlist
        - All: All in one method""")
    parser.add_argument('-vs', '--value_strategy', choices=['replace', 'suffix'], default='suffix', help="""Select the mode strategy from the available choices:
        - Replace: Replace the value with gathered value
        - Suffix: Append the value to the end of the parameters""")
    parser.add_argument('-s', '--silent', help="Silent mode", action='store_true')
    parser.add_argument('-o', '--output', help="Output format", choices=['text', 'json'], default='text')
    parser.add_argument('-m', '--method', choices=['get', 'post'], help="HTTP method to use for sending requests", default=None)
    parser.add_argument('-d', '--data', help="Data to send with POST requests (only used if method is POST)", default=None)

    args = parser.parse_args()

    # Handle silent mode
    if args.silent:
        import sys
        sys.stdout = open('/dev/null', 'w')

    try:
        params = read_parameters(args.params)
    except Exception as e:
        print(f"Error reading parameters: {e}")
        return

    # Store all generated URLs
    all_generated_urls = []

    # Handle single URL
    if args.url:
        urls = fuzz_parameters(args.url, params, args.chunk, args.value, args.value_list, args.generate_strategy, args.value_strategy)
        for url in urls:
            base_url = urlunparse(urlparse(url)._replace(query=''))
            query = parse_qs(urlparse(url).query)
            all_generated_urls.append({'url': base_url, 'params': query})

    # Handle list of URLs
    if args.list:
        try:
            with open(args.list, 'r') as f:
                urls = f.readlines()
                for url in urls:
                    url = url.strip()
                    generated_urls = fuzz_parameters(url, params, args.chunk, args.value, args.value_list, args.generate_strategy, args.value_strategy)
                    for gen_url in generated_urls:
                        base_url = urlunparse(urlparse(gen_url)._replace(query=''))
                        query = parse_qs(urlparse(gen_url).query)
                        all_generated_urls.append({'url': base_url, 'params': query})
        except FileNotFoundError:
            print(f"File not found: {args.list}")
            return

    # Output results based on format
    if args.output == 'json':
        print(json.dumps(all_generated_urls, indent=2))
    else:
        for item in all_generated_urls:
            url = item['url']
            params = item['params']
            encoded_params = urlencode(params, doseq=True)
            print(f"{url}?{encoded_params}" if encoded_params else url)

    # Send requests based on chosen method
    if args.method:
        for item in all_generated_urls:
            url = item['url']
            params = item['params']
            encoded_params = urlencode(params, doseq=True)
            full_url = f"{url}?{encoded_params}" if encoded_params else url

            if args.method == 'get':
                send_get_request(full_url)
            elif args.method == 'post':
                data = args.data if args.data else params
                send_post_request(url, data)

if __name__ == "__main__":
    main()
