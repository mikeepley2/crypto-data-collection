# Note: Database deployments removed - using existing Windows databases

The dedicated data collection node now connects to your existing Windows databases via `host.docker.internal`.

## Database Configuration

All data collection services connect to:
- **MySQL**: Windows MySQL via `host.docker.internal:3306`
- **Redis**: Existing Redis service (crypto-collectors namespace or Windows)
- **Databases**: crypto_prices, crypto_transactions, stock_market_news

## Files Removed

The following database deployment files are not needed:
- `mysql.yaml` - Using Windows MySQL instead
- `redis.yaml` - Using existing Redis setup  
- `influxdb.yaml` - Not required for current setup
- `minio.yaml` - Can be added later if needed

## Benefits

✅ **No Data Migration**: All your existing data remains intact
✅ **No Risk**: Live trading system continues uninterrupted
✅ **Proven Setup**: Keep your working Windows database configuration
✅ **Simple Deployment**: Only deploy collection services and API gateway