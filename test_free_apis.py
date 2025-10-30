"""
Test Free APIs to see what data is actually available
"""

import requests
import time


def test_blockchain_info():
    """Test blockchain.info API"""
    print("Testing Blockchain.info API...")
    try:
        url = "https://api.blockchain.info/charts/active-addresses?timespan=1day&format=json"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            if "values" in data and data["values"]:
                print(f"Latest value: {data['values'][-1]}")
            else:
                print("No values in response")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_coingecko():
    """Test CoinGecko API"""
    print("\nTesting CoinGecko API...")
    try:
        url = "https://api.coingecko.com/api/v3/coins/ethereum"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", {})
            print(f"Price change 7d: {market_data.get('price_change_percentage_7d')}")
            print(f"Available keys: {list(market_data.keys())[:10]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_etherscan():
    """Test Etherscan API"""
    print("\nTesting Etherscan API...")
    try:
        url = "https://api.etherscan.io/api?module=stats&action=ethsupply"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_blockchain_info()
    test_coingecko()
    test_etherscan()


