#x9_fuzz.py
import subprocess
import sys
import os
from urllib.parse import urlparse
from dotenv import load_dotenv  

load_dotenv()

X9_PASSIVE = os.getenv("X9_PASSIVE")

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

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

def split_and_save_urls(urls, base_domain, lines_per_file=1000):
    """Splits a list of URLs into multiple files with a specific number of URLs per file."""
    ensure_directory_exists('fuzz')
    
    total_urls = len(urls)
    print(f"Total URLs to process: {total_urls}")
    
    for i in range(0, total_urls, lines_per_file):
        part_number = (i // lines_per_file) + 1
        chunk = urls[i:i + lines_per_file]
        
        if chunk:  # Only save if we have URLs in this chunk
            part_file_name = os.path.join('fuzz', f"{base_domain}.part{part_number}")
            with open(part_file_name, 'w') as part_file:
                part_file.writelines(url + '\n' for url in chunk)
            print(f"Saved {len(chunk)} URLs to {part_file_name}")

def cleanup_files(domain):
    """Clean up temporary files."""
    passive_file = f"{domain}.passive"
    if os.path.exists(passive_file):
        os.remove(passive_file)
        print(f"Cleaned up {passive_file}")

def main(domain, run_katana):
    urls = []

    # Run X9_PASSIVE to get URLs
    print(f"Running x9_passive for domain: {domain}")
    passive_file = f"{domain}.passive"

    if not os.path.exists(passive_file):
        x9_passive_command = f"python3 {X9_PASSIVE} {domain}"
        run_command_in_zsh(x9_passive_command)

    if os.path.exists(passive_file):
        with open(passive_file, 'r') as file:
            urls.extend(file.read().splitlines())
        print(f"Read {len(urls)} URLs from passive file")

    # Replace 'http' with 'https' in all URLs
    urls = [replace_http_with_https(url) for url in urls]

    # Optionally run nice_katana
    if run_katana.lower() == 'true':
        print(f"Running nice_katana for domain: {domain}")
        katana_command = f"echo {domain} | nice_katana"
        katana_output = run_command_in_zsh(katana_command)
        if katana_output:
            katana_urls = katana_output.splitlines()
            urls.extend(katana_urls)
            print(f"Added {len(katana_urls)} URLs from katana")

    # Remove any duplicate URLs while preserving order
    urls = list(dict.fromkeys(urls))
    print(f"Total unique URLs: {len(urls)}")

    # Split and save URLs
    if urls:
        print("Splitting URLs into parts...")
        split_and_save_urls(urls, domain)
    else:
        print("No URLs found.")

    # Clean up temporary files
    cleanup_files(domain)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python x9_fuzz.py <domain> <true/false>")
        sys.exit(1)

    domain = sys.argv[1]
    run_katana = sys.argv[2]

    main(domain, run_katana)