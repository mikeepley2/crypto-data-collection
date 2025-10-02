#!/bin/bash
# Database backup script before cleanup
# Generated on 2025-09-30 14:26:52

echo 'Creating database backup before cleanup...'
mysqldump -h 192.168.230.162 -u news_collector -p99Rules! crypto_prices > crypto_prices_backup_$(date +%Y%m%d_%H%M%S).sql
echo 'Backup completed!'
