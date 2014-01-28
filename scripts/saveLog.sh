#!/bin/sh

LOG_DIR=/home/ec2-user/code-github/totServer
LOG_FILE="$LOG_DIR/nohup.out"

ARCHIVE_DIR=/home/ec2-user/totServerLogs
ARCHIVE_FILE="$ARCHIVE_DIR/"`date +%F`".log"

logger cp "$LOG_FILE" "$ARCHIVE_FILE"
cp "$LOG_FILE" "$ARCHIVE_FILE"

> "$LOG_FILE" # empty the original log file

