#!/usr/bin/env bash

sleep 15

python3 create_db.py
celery -A tasks worker --loglevel=info -Q lopri &
flower  --broker=amqp://guest:guest@rabitmq:5672// &
#python3 worker.py &
python3 app.py
