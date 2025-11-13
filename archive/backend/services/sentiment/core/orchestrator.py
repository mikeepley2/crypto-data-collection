# backend/core/orchestrator.py
# Orchestrates the trading workflow

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plugins', 'factors'))
from news import schedule_news_processing

class Orchestrator:
    def __init__(self, plugin_manager, portfolio_manager, trade_tracker):
        self.plugin_manager = plugin_manager
        self.portfolio_manager = portfolio_manager
        self.trade_tracker = trade_tracker
        
        # Start automated news sentiment processing
        print("Starting automated news sentiment processing...")
        schedule_news_processing(interval_minutes=30)

    def run(self):
        # 1. Gather factors from plugins
        # 2. Analyze and decide trades
        # 3. Execute trades via plugins
        # 4. Track trades and update portfolio
        pass
