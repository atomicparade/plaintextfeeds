# Plaintext feeds

This script uses [feedparser](https://github.com/kurtmckee/feedparser) to
retrieve Atom and RSS feeds and print new entries since the last time it was
run to `stdout`. Put the list of feed URLs to check in `~/.plaintextfeeds`.



## Suggested usage

1. Clone the repository.
2. Create and enter a virtual environment.
3. Install the requirements.
4. Add the feeds you wish to subscribe to in `~/.plaintextfeeds`.
5. Create a script to run `plaintextfeeds` and email the output to yourself.
6. Create a `cron` job to run the script periodically.

```bash
git clone https://github.com/atomicparade/plaintextfeeds.git
cd plaintextfeeds
python -m venv .venv
pip install -r requirements.txt

echo >~/.plaintextfeeds <<'FEEDS_END'
# Put the feeds to subscribe to here
# Lines beginning with # are ignored
FEEDS_END

echo >~/bin/run-plaintextfeeds2.sh <<'SCRIPT_END'
#!/bin/bash
cd ~/plaintextfeeds && source .venv/bin/activate && python3 plaintextfeeds.py | mail -s "Plaintext feeds" USER@DOMAIN.com
SCRIPT_END

crontab -e
```
