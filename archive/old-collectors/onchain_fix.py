# Onchain Collector Value Validation Fix
# This adds bounds checking for percentage fields to prevent MySQL range errors

# Add this validation function
def validate_percentage(value, field_name="percentage", min_val=-999999.99, max_val=999999.99):
    """Validate and bound percentage values to prevent MySQL range errors"""
    if value is None:
        return None
    
    try:
        val = float(value)
        if val < min_val:
            return min_val
        elif val > max_val:
            return max_val
        return val
    except (ValueError, TypeError):
        return None

# Replace the problematic line in the onchain collector:
# coin.get("atl_change_percentage"),
# WITH:
# validate_percentage(coin.get("atl_change_percentage"), "atl_change_percentage"),

# This will cap extreme values to prevent database range errors