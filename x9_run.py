import os
import subprocess
import sys
import json
from collections import defaultdict

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

def run_x9_on_files(domain_files, output_log):
    """Run X9 on all grouped files."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            print(f"Running X9 on {part_file}")
            x9_command = f"python3 x9.py -l {part_file} -gs all -vs suffix -v 'moein' -p parameters/top_xss_parameter.txt"
            output = run_command_in_zsh(x9_command)
            if output_log:
                with open(output_log, 'a') as log_file:
                    log_file.write(f"--- Running X9 on {part_file} ---\n{output}\n")

def run_fallparams_on_files(domain_files, output_log):
    """Run fallparams on all grouped files and print JSON output."""
    for domain_prefix, files in domain_files.items():
        for part_file in files:
            print(f"Running fallparams on {part_file}")
            fallparams_command = f"fallparams -u {part_file} -o parameters.txt"
            run_command_in_zsh(fallparams_command)

            if os.path.exists('parameters.txt'):
                with open('parameters.txt', 'r') as param_file:
                    params = [param.strip() for param in param_file.readlines()]

                with open(part_file, 'r') as file:
                    urls = [url.strip() for url in file.readlines()]

                # Construct JSON output for x9
                json_output = {
                    "urls": urls,
                    "params": params
                }

                # Print JSON output
                # print(json.dumps(json_output))
#
                # Optionally, run x9 with the JSON output if needed
                x9_command = f"python3 x9.py -j '{json.dumps(json_output)}' -gs all -vs suffix -v '\'electro0neinject\',<b/electro0neinject' -p parameters/top_xss_parameter.txt | nuclei -t ~/Projects/nuclei-templates/xss-discovery.yaml"
                output_j = run_command_in_zsh(x9_command)
                print(x9_command)

                if output_log:
                    with open(output_log, 'a') as log_file:
                        log_file.write(f"--- Processed {part_file} with fallparams ---{output_j} \n")
            else:
                print(f"parameters.txt not found after running fallparams on {part_file}")

def main(parameter_discovery=False):
    """Main function to run the attack based on input."""
    output_log = "x9.res"

    # Group files by their domain or subdomain
    domain_files = group_files_by_domain()

    if parameter_discovery:
        print("Running parameter discovery with fallparams.")
        run_fallparams_on_files(domain_files, output_log)
    else:
        print("Running X9 directly on part files.")
        run_x9_on_files(domain_files, output_log)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python3 attack.py [true]")
        sys.exit(1)

    parameter_discovery = len(sys.argv) == 2 and sys.argv[1].lower() == 'true'

    main(parameter_discovery)
