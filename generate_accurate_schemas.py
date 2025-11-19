#!/usr/bin/env python3
"""
Generate Accurate Database Schema Definitions
Creates schema files that match the actual production database structure
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()

def load_actual_schema():
    """Load the actual database schema from JSON file"""
    schema_file = PROJECT_ROOT / "actual_database_schema.json"
    
    if not schema_file.exists():
        print("❌ actual_database_schema.json not found. Run check_actual_schema.py first.")
        return None
    
    with open(schema_file, 'r') as f:
        return json.load(f)

def generate_create_table_sql(table_name, table_info):
    """Generate CREATE TABLE SQL from schema info"""
    
    # Skip views and backup/archive tables
    if (table_name.endswith('_view') or 
        table_name.endswith('_working') or 
        'archive' in table_name.lower() or
        'backup' in table_name.lower() or
        '_old' in table_name.lower()):
        return None
    
    # Skip specific utility tables for now
    skip_tables = [
        'assets_archived_archive_old',
        'crypto_derivatives_ml', 
        'crypto_news_archive_20251107_100457_old',
        'crypto_onchain_data_old',
        'market_conditions_history_archive_20251107_100457_old',
        'social_sentiment_metrics_final_archive_20251107_113856_old',
        'sentiment_aggregation_final_archive_20251107_113856_old'
    ]
    
    if table_name in skip_tables:
        return None
    
    columns = table_info['columns']
    
    sql_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
    
    column_definitions = []
    indexes = []
    
    for col in columns:
        field, type_, null, key, default, extra = col
        
        col_def = f"    {field} {type_}"
        
        # Handle NULL/NOT NULL
        if null == 'NO':
            col_def += " NOT NULL"
        
        # Handle default values
        if default is not None:
            if default == 'CURRENT_TIMESTAMP':
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif default != 'None':
                col_def += f" DEFAULT {default}"
        
        # Handle extra attributes
        if extra:
            if 'auto_increment' in extra:
                col_def += " AUTO_INCREMENT"
            if 'on update CURRENT_TIMESTAMP' in extra:
                col_def += " ON UPDATE CURRENT_TIMESTAMP"
        
        # Handle primary key
        if key == 'PRI':
            col_def += " PRIMARY KEY"
        
        column_definitions.append(col_def)
    
    sql_parts.extend(column_definitions)
    sql_parts.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci")
    
    return ",\n".join(sql_parts)

def generate_accurate_create_missing_tables():
    """Generate accurate create_missing_tables.py file"""
    
    schema_data = load_actual_schema()
    if not schema_data:
        return False
    
    # Focus on core tables that are commonly used
    core_tables = [
        'crypto_assets',
        'price_data_real', 
        'technical_indicators',
        'macro_indicators',
        'crypto_news',
        'real_time_sentiment_signals',
        'trading_signals',
        'trade_recommendations',
        'backtesting_results',
        'backtesting_trades'
    ]
    
    # Generate new create_missing_tables.py content
    content = '''#!/usr/bin/env python3
"""
Create Missing Database Tables - ACCURATE PRODUCTION SCHEMAS
Creates all tables required by the integration test suite using EXACT production schemas
Generated from actual database structure analysis
"""

import mysql.connector
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from shared.database_config import get_db_connection

def create_missing_tables():
    """Create missing tables with EXACT production schemas"""
    
    print("🔧 Creating tables with accurate production schemas...")
    
    # EXACT schemas from production database analysis
    table_schemas = {
'''
    
    # Generate table schemas
    for table_name in core_tables:
        if table_name in schema_data:
            table_info = schema_data[table_name]
            create_sql = table_info.get('create_sql', '')
            
            # Clean up the CREATE SQL for readability  
            if create_sql.startswith('CREATE TABLE'):
                # Extract just the CREATE TABLE portion, remove extra details
                lines = create_sql.split('\n')
                clean_lines = []
                for line in lines:
                    if 'AUTO_INCREMENT=' in line or 'DEFAULT CHARSET=' in line:
                        # Keep these but clean them up
                        if 'ENGINE=InnoDB' in line:
                            clean_lines.append(') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci')
                            break
                    else:
                        clean_lines.append(line)
                
                clean_sql = '\n'.join(clean_lines)
                # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
                clean_sql = clean_sql.replace('CREATE TABLE `', 'CREATE TABLE IF NOT EXISTS `')
                
                content += f'        "{table_name}": """\n        {clean_sql}\n        """,\n\n'
    
    content += '''    }
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print(f"📊 Creating {len(table_schemas)} core tables...")
        
        created_tables = []
        failed_tables = []
        
        for table_name, schema_sql in table_schemas.items():
            try:
                print(f"🔨 Creating table: {table_name}")
                cursor.execute(schema_sql)
                created_tables.append(table_name)
            except Exception as e:
                print(f"❌ Failed to create {table_name}: {e}")
                failed_tables.append(table_name)
        
        # Verify tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\\n✅ Tables created successfully: {created_tables}")
        if failed_tables:
            print(f"⚠️ Failed to create tables: {failed_tables}")
        print(f"📋 Total tables in database: {len(existing_tables)}")
        
        cursor.close()
        connection.close()
        
        return len(failed_tables) == 0
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating Missing Tables - Production Schemas")
    print("=" * 55)
    
    success = create_missing_tables()
    
    if success:
        print("\\n🎉 All tables created successfully!")
        print("✅ Database schema now matches production structure")
    else:
        print("\\n❌ Some tables failed to create")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
    
    # Save the new file
    new_file = PROJECT_ROOT / "create_missing_tables_accurate.py"
    with open(new_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Generated accurate schema file: {new_file}")
    return True

def generate_schema_documentation():
    """Generate comprehensive schema documentation"""
    
    schema_data = load_actual_schema()
    if not schema_data:
        return False
    
    doc_content = "# Complete Database Schema Documentation\n\n"
    doc_content += "## Production Database Tables\n\n"
    doc_content += f"**Total Tables:** {len(schema_data)}\n\n"
    
    # Categorize tables
    categories = {
        'Core Data Tables': [],
        'Price & Market Data': [],
        'Technical Analysis': [],
        'Sentiment & News': [],
        'Trading & Signals': [],
        'ML & Analytics': [],
        'System & Monitoring': [],
        'Archive & Backup': []
    }
    
    for table_name in schema_data.keys():
        if any(x in table_name for x in ['backup', 'archive', '_old']):
            categories['Archive & Backup'].append(table_name)
        elif any(x in table_name for x in ['price', 'crypto_prices']):
            categories['Price & Market Data'].append(table_name)
        elif 'technical' in table_name:
            categories['Technical Analysis'].append(table_name)
        elif any(x in table_name for x in ['sentiment', 'news']):
            categories['Sentiment & News'].append(table_name)
        elif any(x in table_name for x in ['trading', 'signal', 'recommendation']):
            categories['Trading & Signals'].append(table_name)
        elif any(x in table_name for x in ['ml', 'derivatives', 'backtesting']):
            categories['ML & Analytics'].append(table_name)
        elif any(x in table_name for x in ['monitoring', 'service']):
            categories['System & Monitoring'].append(table_name)
        else:
            categories['Core Data Tables'].append(table_name)
    
    for category, tables in categories.items():
        if tables:
            doc_content += f"\n### {category}\n\n"
            for table in tables:
                table_info = schema_data[table]
                column_count = len(table_info['columns'])
                doc_content += f"- **{table}** ({column_count} columns)\n"
    
    # Add detailed schema for key tables
    key_tables = ['crypto_assets', 'price_data_real', 'technical_indicators', 'crypto_news', 'trading_signals']
    
    doc_content += "\n## Key Table Schemas\n\n"
    
    for table_name in key_tables:
        if table_name in schema_data:
            table_info = schema_data[table_name]
            doc_content += f"### {table_name}\n\n"
            doc_content += "| Column | Type | Null | Key | Default | Extra |\n"
            doc_content += "|--------|------|------|-----|---------|-------|\n"
            
            for col in table_info['columns']:
                field, type_, null, key, default, extra = col
                default_str = str(default) if default else ''
                doc_content += f"| {field} | {type_} | {null} | {key} | {default_str} | {extra} |\n"
            
            doc_content += "\n"
    
    # Save documentation
    doc_file = PROJECT_ROOT / "DATABASE_SCHEMA_DOCUMENTATION.md"
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"✅ Generated schema documentation: {doc_file}")
    return True

def main():
    """Main function"""
    print("🚀 Generating Accurate Database Schemas")
    print("=" * 50)
    
    # Generate accurate create_missing_tables.py
    success1 = generate_accurate_create_missing_tables()
    
    # Generate comprehensive documentation
    success2 = generate_schema_documentation()
    
    if success1 and success2:
        print("\n🎉 Schema generation complete!")
        print("✅ Accurate schema files created")
        print("✅ Comprehensive documentation generated")
    else:
        print("\n❌ Some generation steps failed")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)