import os
import subprocess
import sys
import json
from collections import defaultdict

# List of unwanted extensions
bad_extensions = ['.json', '.js', '.fnt', '.ogg', '.css', '.jpg', '.jpeg', '.png', '.svg', 
                  '.img', '.gif', '.exe', '.mp4', '.flv', '.pdf', '.doc', '.ogv', '.webm', 
                  '.wmv', '.webp', '.mov', '.mp3', '.m4a', '.m4p', '.ppt', '.pptx', '.scss', 
                  '.tif', '.tiff', '.ttf', '.otf', '.woff', '.woff2', '.bmp', '.ico', '.eot', 
                  '.htc', '.swf', '.rtf', '.image', '.rf', '.txt', 'xml', 'zip', 'msi']

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
    files = sorted([f for f in os.listdir('.') if f.count('.') >= 2 and '.part' in f])
    domain_files = defaultdict(list)

    for part_file in files:
        # Extract domain prefix (e.g., icollab.info from icollab.info.part1)
        domain_prefix = part_file.split('.part')[0]
        domain_files[domain_prefix].append(part_file)
    
    return domain_files

def filter_urls(urls):
    """Filter out URLs that end with any of the bad extensions."""
    filtered_urls = []
    for url in urls:
        if not any(url.lower().endswith(ext) for ext in bad_extensions):
            filtered_urls.append(url)
    return filtered_urls

def run_x9_on_files(domain_files, output_log):
    """Run X9 on each URL in each file one by one."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            with open(part_file, 'r') as file:
                urls = [url.strip() for url in file.readlines()]
            
            # Filter URLs
            urls = filter_urls(urls)
            
            for url in urls:
                print(f"Running X9 on {url} from {part_file}")
                x9_command = f"python3 ~/project/automation/x9/x9.py -u '{url}' -gs all -vs suffix -v '<b/electro0neinject,\"electro0neinject\"',\'electro0neinject\''' -p parameters/top_xss_parameter.txt | nuclei -t ~/project/nuclei-templates/xss-discovery.yaml"
                output = run_command_in_zsh(x9_command)
                if output_log:
                    with open(output_log, 'a') as log_file:
                        log_file.write(f"--- Running X9 on {url} from {part_file} ---\n{output}\n")

def run_fallparams_on_files(domain_files, output_log):
    """Run fallparams on each URL in each file one by one and process them individually."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            with open(part_file, 'r') as file:
                urls = [url.strip() for url in file.readlines()]
            
            # Filter URLs
            urls = filter_urls(urls)
            
            for url in urls:
                print(f"Running fallparams on {url} from {part_file}")

                # Run fallparams command
                fallparams_command = f"fallparams -u '{url}' -o parameters.txt"
                run_command_in_zsh(fallparams_command)

                # Check if parameters.txt exists and is non-empty
                parameters_path = 'parameters.txt'
                if os.path.exists(parameters_path) and os.path.getsize(parameters_path) > 0:
                    with open(parameters_path, 'r') as param_file:
                        params = [param.strip() for param in param_file.readlines()]
                else:
                    # If parameters.txt is missing or empty, continue with empty parameters
                    print(f"parameters.txt is missing or empty after running fallparams on {url} from {part_file}")
                    params = []

                # Construct JSON output for x9
                json_output = {
                    "urls": [url],
                    "params": params
                }

                # Run x9 with the JSON output for this specific URL
                x9_command = f"python3 ~/project/automation/x9/x9.py -j '{json.dumps(json_output)}' -gs all -vs suffix -v '<b/electro0neinject,\"electro0neinject\"',\'electro0neinject\''' -p parameters/top_xss_parameter.txt | nuclei -t ~/project/nuclei-templates/xss-discovery.yaml"
                output_j = run_command_in_zsh(x9_command)
                print(x9_command)

                if output_log:
                    with open(output_log, 'a') as log_file:
                        log_file.write(f"--- Processed {url} from {part_file} with fallparams ---\n{output_j}\n")

def main(parameter_discovery=False):
    """Main function to run the attack based on input."""
    output_log = "x9.res"

    # Group files by their domain or subdomain
    domain_files = group_files_by_domain()

    if parameter_discovery:
        print("Running parameter discovery with fallparams.")
        run_fallparams_on_files(domain_files, output_log)
    else:
        print("Running X9 directly on URLs in part files.")
        run_x9_on_files(domain_files, output_log)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python3 x9_run.py [true]")
        sys.exit(1)

    parameter_discovery = len(sys.argv) == 2 and sys.argv[1].lower() == 'true'

    main(parameter_discovery)
