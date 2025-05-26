#!/usr/bin/env python3

import os
import sys
import tempfile
import subprocess
from urllib.parse import urlparse, urlsplit

COLOR_GRAY = "\033[90m"

FILTER_EXTS = {
    '.json', '.js', '.css', '.jpg', '.jpeg', '.png', '.svg', '.gif', '.mp4', '.mp3',
    '.pdf', '.doc', '.exe', '.zip', '.xml', '.woff', '.woff2', '.ttf', '.otf', '.ico',
    '.bmp', '.eot', '.flv', '.webm', '.webp', '.ppt', '.pptx', '.scss', '.tif', '.tiff',
    '.m4a', '.m4p', '.fnt', '.ogg', '.ogv', '.wmv', '.mov', '.rtf', '.swf', '.htc',
    '.image', '.rf', '.txt', '.msi'
}

def extract_domain(value):
    """Extract domain or hostname from URL or input."""
    return urlsplit(value).netloc if value.startswith("http") else value

def is_asset_url(url):
    """Return False if URL likely points to a static asset."""
    try:
        parsed = urlparse(url)
        return not any(parsed.path.lower().endswith(ext) for ext in FILTER_EXTS)
    except Exception as err:
        print(f"URL parse error: {err}")
        return False

def execute_zsh(command):
    """Run a command in zsh and return output or False on error."""
    try:
        proc = subprocess.run(["zsh", "-c", command], capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"Command failed: {proc.stderr}")
            return False
        return proc.stdout.strip()
    except subprocess.CalledProcessError as error:
        print(f"Execution error: {error}")
        return False

def temp_file_path():
    """Create and return a path to a temp file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        return temp.name

def filter_and_save(input_file, domain):
    """Filter out static URLs and write valid ones to output."""
    try:
        with open(input_file, "r") as f:
            lines = {line.strip() for line in f if is_asset_url(line.strip())}

        if not lines:
            return False

        with open(f"{domain}.passive", "w") as f:
            f.write("\n".join(sorted(lines)) + "\n")

        return lines
    except Exception as e:
        print(f"File filtering failed: {e}")
        return False

def run_passive_collection(domain):
    """Run passive URL collectors and store results."""
    print(f"{COLOR_GRAY}Starting passive scan for: {domain}{COLOR_GRAY}")
    temp_file = temp_file_path()

    commands = [
        f"echo https://{domain}/ > {temp_file}",
        f"echo {domain} | waybackurls | sort -u | uro >> {temp_file}",
        f"gau {domain} --threads 1 --subs | sort -u | uro >> {temp_file}"
    ]

    for cmd in commands:
        print(f"{COLOR_GRAY}Running: {cmd}{COLOR_GRAY}")
        execute_zsh(cmd)

    print(f"{COLOR_GRAY}Finalizing results for: {domain}{COLOR_GRAY}")
    result = filter_and_save(temp_file, domain)
    count = len(result) if result else 0
    print(f"{COLOR_GRAY}Finished {domain} — {count} URLs saved{COLOR_GRAY}")

def get_input_source():
    """Detect whether input comes from stdin or CLI arg."""
    if not sys.stdin.isatty():
        return sys.stdin.readline().strip()
    elif len(sys.argv) > 1:
        return sys.argv[1]
    return None

def process_input(source):
    """Handle domain(s) depending on source type."""
    if os.path.isfile(source):
        with open(source, "r") as f:
            for line in f:
                domain = extract_domain(line.strip())
                if domain:
                    run_passive_collection(domain)
    else:
        run_passive_collection(extract_domain(source))

if __name__ == "__main__":
    user_input = get_input_source()
    if not user_input:
        print("Usage examples:")
        print("  echo domain.com | python3 x9_passive.py")
        print("  cat domains.txt | python3 x9_passive.py")
        sys.exit(1)

    process_input(user_input)