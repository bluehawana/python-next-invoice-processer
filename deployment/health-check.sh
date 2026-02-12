#!/bin/bash
# Health check script - restarts nginx and invoice-backend if down
# Runs via cron every 2 minutes

LOG="/var/log/invoice-health-check.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Check nginx
if ! systemctl is-active --quiet nginx; then
    echo "$TIMESTAMP - nginx is down, restarting..." >> "$LOG"
    systemctl start nginx
    if systemctl is-active --quiet nginx; then
        echo "$TIMESTAMP - nginx restarted successfully" >> "$LOG"
    else
        echo "$TIMESTAMP - ERROR: nginx failed to restart" >> "$LOG"
    fi
fi

# Check invoice-backend
if ! systemctl is-active --quiet invoice-backend; then
    echo "$TIMESTAMP - invoice-backend is down, restarting..." >> "$LOG"
    systemctl start invoice-backend
    if systemctl is-active --quiet invoice-backend; then
        echo "$TIMESTAMP - invoice-backend restarted successfully" >> "$LOG"
    else
        echo "$TIMESTAMP - ERROR: invoice-backend failed to restart" >> "$LOG"
    fi
fi

# Trim log to last 500 lines if it gets too big
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 500 ]; then
    tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
