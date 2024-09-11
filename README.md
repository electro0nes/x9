## Electro0ne x9 Vulnerability Discovery

![Alt text](https://archive.org/download/anonymus-hacker-computer-4k-wallpaper-preview/anonymus-hacker-computer-4k-wallpaper-preview.jpg "hacker")
## Usage
### install requirement's
```py
pip3 install -r requirements.txt
sudo chmod +x x9.py
sudo chmod +x x9_run.py
sudo chmod +x x9_fuzz.py
```

## method
```py
python3 x9.py -l urls.txt -v 'inject' -p file,text -gs generate_strategy -vs value_strategy -o json,text -c chunk -m post,get
```

## Bash Profile

```bash
alias x9_fuzz="python3 $HOME/Projects/automation/x9/x9_fuzz.py"
alias x9_run="python3 $HOME/Projects/automation/x9/x9_fuzz.py"
alias x9="python3 $HOME/Projects/automation/x9/x9.py"
```