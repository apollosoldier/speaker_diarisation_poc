#!/usr/bin/env bash

sleep 10
python create_db.py
python worker.py &
python app.py
