#!/usr/bin/env bash

sleep 15

python3 create_db.py
python3 worker.py &
python3 app.py
