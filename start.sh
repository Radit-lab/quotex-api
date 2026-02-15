#!/bin/bash
uvicorn live_api:app --host 0.0.0.0 --port $PORT
