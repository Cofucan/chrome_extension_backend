#!/usr/bin/env bash

if [ -d "media" ]; then
    echo "Removing media directory"
    rm -rf media
fi
if [ -f "screen_recording_app.db" ]; then
    echo "Removing database"
    rm screen_recording_app.db
fi
