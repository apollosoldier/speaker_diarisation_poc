#!/usr/bin/env bash

sleep 15

python create_db.py
python worker.py &
python app.py
