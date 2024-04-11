#!/bin/sh
mv api/main.py main.py
alembic upgrade heads
uvicorn main:app --host 0.0.0.0 --port 88
