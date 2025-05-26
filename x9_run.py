#x9_run.py
import os
import subprocess
import sys
import json
import requests
import datetime
from collections import defaultdict
from dotenv import load_dotenv  

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NUCLEI_ROUTE = os.getenv("NUCLEI_ROUTE")
SCRIPT_ROUTE = os.getenv("SCRIPT_ROUTE")

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def is_json_response(url):
    """Check if the URL returns a JSON response by inspecting the Content-Type header."""
    try:
        response = requests.get(url, timeout=5)  # Make a request to get headers
        content_type = response.headers.get("Content-Type", "").lower()
        return (
            "application/json" in content_type or
            "text/javascript" in content_type
        )
    except Exception as e:
        print(f"⚠️ Error checking Content-Type: {str(e)}")
        return False 

def send_discord_alert(nuclei_output, part_file):
    """Send a Discord notification with ANSI-colored output inside a code block."""
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL is not set or is empty!")
        return

    now_timestamp = datetime.datetime.utcnow().isoformat()
    formatted_output = f"```ansi\n{nuclei_output}\n```"

    embed = {
        "title": "🚨 XSS Detected via X9!",
        "description": formatted_output,  
        "color": 16711680,  
        "footer": {
            "text": "XSS Alert | Automated System",
            "icon_url": "https://cdn-icons-png.flaticon.com/512/6192/6192510.png"
        },
        "timestamp": now_timestamp
    }

    message = {
        "username": "XSS Scanner",
        "embeds": [embed]
    }

    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, headers=headers)
        if response.status_code in [200, 204]:  
            print("✅ Discord alert sent successfully!")
        else:
            print(f"⚠️ Failed to send Discord alert: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Error sending Discord alert: {str(e)}")

def run_command_in_zsh(command):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(["zsh", "-c", command], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error occurred: {result.stderr}")
            return None
        return result.stdout
    except subprocess.CalledProcessError as exc:
        print(f"Status: FAIL {exc.returncode}, {exc.output}")
        return None

def group_files_by_domain():
    """Group part files by their domain or subdomain."""
    fuzz_dir = 'fuzz'
    if not os.path.exists(fuzz_dir):
        print(f"⚠️ Directory '{fuzz_dir}' not found!")
        return {}

    files = sorted([f for f in os.listdir(fuzz_dir) if f.count('.') >= 2 and '.part' in f])
    domain_files = defaultdict(list)

    for part_file in files:
        domain_prefix = part_file.split('.part')[0]
        domain_files[domain_prefix].append(os.path.join(fuzz_dir, part_file))

    return domain_files

def run_x9_on_files(domain_files, output_file):
    """Run X9 and check for XSS detections."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            with open(part_file, 'r') as file:
                urls = [url.strip() for url in file.readlines()]

            urls = filter_urls(urls)

            for url in urls:
                if is_json_response(url):
                    print(f"❌ Skipping {url} (JSON response, no XSS possible)")
                    continue  # Skip URLs with JSON responses

                print(f"Running X9 on {url} from {part_file}")
                x9_command = f"python3 {SCRIPT_ROUTE} -u '{url}' -gs all -vs suffix -v '<b/electro0neinject,\"electro0neinject\"',\'electro0neinject\''' -p parameters/top_xss_parameter.txt --rate-limit 1 | nuclei -t {NUCLEI_ROUTE} -silent"
                output = run_command_in_zsh(x9_command)

                if output and "electro0neinject" in output: 
                    send_discord_alert(output, part_file)

                if output_file:
                    with open(output_file, 'a') as log_file:
                        log_file.write(f"--- Running X9 on {url} from {part_file} ---\n{output}\n")

            os.remove(part_file)
            print(f"Removed processed file: {part_file}")

def run_fallparams_on_files(domain_files, output_file):
    """Run fallparams on each URL in each file one by one and process them individually."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            with open(part_file, 'r') as file:
                urls = [url.strip() for url in file.readlines()]

            urls = filter_urls(urls)

            for url in urls:
                if is_json_response(url):
                    print(f"❌ Skipping {url} (JSON response, no XSS possible)")
                    continue  # Skip URLs with JSON responses

                print(f"Running fallparams on {url} from {part_file}")

                fallparams_command = f"fallparams -u '{url}' -o parameters.txt"
                run_command_in_zsh(fallparams_command)

                parameters_path = 'parameters.txt'
                if os.path.exists(parameters_path) and os.path.getsize(parameters_path) > 0:
                    with open(parameters_path, 'r') as param_file:
                        params = [param.strip() for param in param_file.readlines()]
                else:
                    print(f"parameters.txt is missing or empty after running fallparams on {url} from {part_file}")
                    params = []

                json_output = {
                    "urls": [url],
                    "params": params
                }

                x9_command = f"python3 {SCRIPT_ROUTE} -j '{json.dumps(json_output)}' -gs all -vs suffix -v '<b/electro0neinject,\"electro0neinject\"',\'electro0neinject\''' -p parameters/top_xss_parameter.txt --rate-limit 1 | nuclei -t {NUCLEI_ROUTE} -silent"
                output_j = run_command_in_zsh(x9_command)

                if output_j and "electro0neinject" in output_j: 
                    send_discord_alert(output_j, part_file)

                if output_file:
                    with open(output_file, 'a') as log_file:
                        log_file.write(f"--- Processed {url} from {part_file} with fallparams ---\n{output_j}\n")

            os.remove(part_file)
            print(f"Removed processed file: {part_file}")

def filter_urls(urls):
    """Filter out URLs that end with unwanted file extensions."""
    extensions = ['.m4v','.json', '.js', '.fnt', '.ogg', '.css', '.jpg', '.jpeg',
                  '.png', '.svg', '.img', '.gif', '.exe', '.mp4', '.flv',
                  '.pdf', '.doc', '.ogv', '.webm', '.wmv', '.webp', '.mov',
                  '.mp3', '.m4a', '.m4p', '.ppt', '.pptx', '.scss', '.tif',
                  '.tiff', '.ttf', '.otf', '.woff', '.woff2', '.bmp', '.ico',
                  '.eot', '.htc', '.swf', '.rtf', '.image', '.rf', '.txt',
                  '.xml', '.zip', '.msi', '.tar', '.gz', '.GZ', '.rar' , '.pdf%20' , '.pdf ']

    filtered_urls = []
    for url in urls:
        if not any(url.lower().endswith(ext) for ext in extensions):
            filtered_urls.append(url)

    return filtered_urls

def main(parameter_discovery=False):
    """Main function to run the attack based on input."""
    output_file = os.path.join('fuzz', 'x9.res')

    domain_files = group_files_by_domain()
    if not domain_files:
        print("No files to process in the fuzz directory!")
        return

    if parameter_discovery:
        print("Running parameter discovery with fallparams.")
        run_fallparams_on_files(domain_files, output_file)
    else:
        print("Running X9 directly on part files.")
        run_x9_on_files(domain_files, output_file)

    print(f"Results saved in {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python3 x9_run.py [true]")
        sys.exit(1)

    parameter_discovery = len(sys.argv) == 2 and sys.argv[1].lower() == 'true'

    main(parameter_discovery)