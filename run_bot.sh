#!/bin/bash

# Make sure pyenv is loaded
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PYTHONPATH="$HOME/firefeed/apps/telegram_bot:$PYTHONPATH"
eval "$(pyenv init -)"

# Set Python version
pyenv shell 3.13.6

# Start Telegram Bot
python -m telegram_bot