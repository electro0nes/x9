import subprocess
import sys
import os
from urllib.parse import urlparse

def run_command_in_zsh(command):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(["zsh", "-c", command], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error occurred:", result.stderr)
            return None
        return result.stdout
    except subprocess.CalledProcessError as exc:
        print("Status: FAIL", exc.returncode, exc.output)
        return None

def parse_domain(url):
    """Extract the domain from a URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def replace_http_with_https(url):
    """Replace 'http' with 'https' in the URL."""
    if url.startswith('http://'):
        return 'https://' + url[7:]
    return url

def save_urls(urls_by_domain):
    """Saves URLs grouped by their domains/subdomains into separate files."""
    for domain, urls in urls_by_domain.items():
        split_urls(urls, domain)

def split_urls(urls, domain, lines_per_file=1000):
    """Splits a list of URLs into multiple files with a specific number of URLs per file."""
    part_number = 1
    current_part = []
    for i, url in enumerate(urls, 1):
        current_part.append(url + '\n')
        if i % lines_per_file == 0:
            save_part(current_part, domain, part_number)
            part_number += 1
            current_part = []
    if current_part:
        save_part(current_part, domain, part_number)

def save_part(urls, domain, part_number):
    """Saves a part of the split URLs."""
    part_file_name = f"{domain}.part{part_number}"
    with open(part_file_name, 'w') as part_file:
        part_file.writelines(urls)
    print(f"Saved {part_file_name}")

def main(domain, run_katana):
    urls = []

    # Run nice_passive to get URLs
    print(f"Running nice_passive for domain: {domain}")
    passive_file = f"{domain}.passive"

    if not os.path.exists(passive_file):
        nice_passive_command = f"python3 ~/Projects/Scripts/nice_passive.py {domain}"
        run_command_in_zsh(nice_passive_command)

    if os.path.exists(passive_file):
        with open(passive_file, 'r') as file:
            urls.extend(file.read().splitlines())

    # Replace 'http' with 'https' in all URLs
    urls = [replace_http_with_https(url) for url in urls]

    # Optionally run nice_katana
    if run_katana.lower() == 'true':
        print(f"Running nice_katana for domain: {domain}")
        katana_command = f"echo {domain} | nice_katana"
        katana_output = run_command_in_zsh(katana_command)

    # Group URLs by their domain
    urls_by_domain = {}
    for url in urls:
        domain = parse_domain(url)
        if domain not in urls_by_domain:
            urls_by_domain[domain] = []
        urls_by_domain[domain].append(url)

    # Save URLs grouped by domain/subdomain
    if urls_by_domain:
        print("Splitting URLs into parts by domain/subdomain.")
        save_urls(urls_by_domain)
    else:
        print("No URLs found.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python x9_fuzz.py <domain> <true/false>")
        sys.exit(1)

    domain = sys.argv[1]
    run_katana = sys.argv[2]

    main(domain, run_katana)