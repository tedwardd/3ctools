# 3C Tools

This repository is a collection of tools, mostly Python command line tools, for doing some extra stuff
with the 3commas.io API. Please read the global setup instructions below before running anything here.

I provide no warranty with any of this. If you find a bug or feature request, please submit it. But also please understand that this is a side hobby project for me and I can't or won't implement everything there. The best way to see your feature added or bug fix is to do it yourself and submit a PR.

# Global Setup
## Summary
You will need Python 3 installed to run the tools here. At the time of writing this, I'm using Python 3.7.1. Newer may work but YMMV. I recommend using pyenv, if you don't have it already, [read this first](https://github.com/pyenv/pyenv-virtualenv) and set it up. I've included a `.python-version` file in this repo which will make sure you're using the right version if you have pyenv installed.

### Requirements

* Python 3 (pyenv recommended)

### Setup

`pip install -r requirements.txt`

Once all dependencies are installed and `python --version` returns 3.7.1, proceed to setting up anything additional that is noted at the top of the specific tool you want to use.

### Config

There is an `example_config.ini`, Make a copy of this file and name it `config.ini`. Open the file and edit the values with your information.