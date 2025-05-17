# X9 - Advanced XSS Discovery Suite

![X9 Banner](https://archive.org/download/anonymus-hacker-computer-4k-wallpaper-preview/anonymus-hacker-computer-4k-wallpaper-preview.jpg "X9 Tool Banner")

## Overview

X9 is a powerful automated XSS (Cross-Site Scripting) discovery suite that combines multiple tools to efficiently find XSS vulnerabilities in web applications. The suite uses a pipeline approach:

1. **URL Discovery**: Uses Wayback Machine and GAU for comprehensive URL harvesting
2. **Parameter Analysis**: Processes and analyzes URL parameters
3. **XSS Fuzzing**: Automated testing of potential XSS vectors

## Features

- 🔍 Comprehensive URL discovery using multiple sources
- 🚀 Automated parameter extraction and analysis
- 🎯 Intelligent XSS payload fuzzing
- 📊 Structured output formats (JSON, text)
- ⚡ Parallel processing for faster results

## Installation

### Prerequisites

```bash
# Install required Python packages
pip3 install -r requirements.txt
# Install URO
https://github.com/s0md3v/uro

# Make scripts executable
chmod +x x9.py
chmod +x x9_run.py
chmod +x x9_fuzz.py
```

### Configuration

Create a `.env` file with the following configurations:

```bash
DISCORD_WEBHOOK_URL=""    # For notifications
NUCLEI_ROUTE=""          # Path to nuclei templates
SCRIPT_ROUTE=""          # Path to custom scripts
NICE_PASSIVE_URO=""      # Nice passive configuration
```

## Usage

### 1. URL Discovery and Parameter Extraction

```bash
# Run the fuzzer to gather URLs
python3 x9_fuzz.py example.com  <true/false> # for katana

# This will:
# - Fetch URLs from Wayback Machine
# - Gather URLs using GAU
# - Extract and analyze parameters
```

### 2. XSS Testing

```bash
# Run the main XSS discovery
python3 x9.py -l discovered_urls.txt -v 'xss_payload' -p file,text -gs generate_strategy -vs value_strategy -o json -m get,post

# Parameters:
# -l: List of URLs to test
# -v: XSS payload to test
# -p: Parameters to fuzz
# -gs: Generation strategy
# -vs: Value strategy
# -o: Output format
# -m: HTTP methods to test
```

### 3. Advanced Fuzzing

```bash
# Run advanced fuzzing on discovered endpoints
python3 x9_run.py urls.txt

# This will:
# - Process URLs in batches
# - Apply multiple XSS payloads
# - Test different parameter combinations
```

## Workflow Example

1. **Gather URLs**:
   ```bash
   x9_fuzz target.com <true/false> # for katana
   ```

2. **Initial XSS Scan**:
   ```bash
   x9 -l urls.txt -v '<script>alert(1)</script>' -gs normal -vs replace
   ```


## Best Practices

- Always ensure you have permission to test the target
- Start with small payload sets before large-scale testing
- Monitor system resources during large scans
- Use rate limiting to avoid overwhelming targets

## Output Formats


## Shell Aliases

Add these to your `.bashrc` or `.zshrc` for quick access:

```bash
alias x9_fuzz="python3 $HOME/Projects/automation/x9/x9_fuzz.py"
alias x9_run="python3 $HOME/Projects/automation/x9/x9_run.py"
alias x9="python3 $HOME/Projects/automation/x9/x9.py"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes and authorized testing only. Always obtain proper authorization before testing any systems or applications.

```bash
DISCORD_WEBHOOK_URL=""
NUCLEI_ROUTE=""
SCRIPT_ROUTE=""
NICE_PASSIVE_URO=""
```

## method
```bash
python3 x9.py -l urls.txt -v 'inject' -p file,text -gs generate_strategy -vs value_strategy -o json,text -c chunk -m post,get
```

## Bash Profile

```bash
alias x9_fuzz="python3 $HOME/Projects/automation/x9/x9_fuzz.py"
alias x9_run="python3 $HOME/Projects/automation/x9/x9_fuzz.py"
alias x9="python3 $HOME/Projects/automation/x9/x9.py"
```