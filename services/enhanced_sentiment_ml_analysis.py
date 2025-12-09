#!/usr/bin/env python3
"""
Enhanced ML Sentiment Collector - Template Compliant Version
Migrated from legacy implementation to standardized collector template
"""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import mysql.connector
from mysql.connector import pooling
import numpy as np
import re

from services.base_collector import (
    BaseCollector, CollectorConfig, DataQualityReport, AlertRequest
)
from shared.smart_model_manager import get_model_manager, ModelSource, ModelLoadingError

class MLSentimentCollectorConfig(CollectorConfig):
    """Extended configuration for ML sentiment collector"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ML-specific configuration
        self.batch_processing_size = 5
        self.processing_interval = 300  # 5 minutes
        self.model_cache_size = 2
        self.max_text_length = 512 * 4  # Roughly 512 tokens
        self.device = -1  # Force CPU usage
        
        # Model configuration
        self.crypto_model = "kk08/CryptoBERT"
        self.stock_model = "ProsusAI/finbert"
        self.fallback_confidence = 0.5
        
        # Data processing configuration
        self.days_lookback = 7
        self.min_confidence_threshold = 0.1

    @classmethod
    def from_env(cls) -> 'MLSentimentCollectorConfig':
        """Load configuration from environment variables"""
        config = super().from_env()
        # Convert to MLSentimentCollectorConfig
        ml_config = cls(**config.__dict__)
        ml_config.service_name = "enhanced-sentiment-ml"
        return ml_config

class EnhancedMLSentimentCollector(BaseCollector):
    """
    Enhanced ML Sentiment Collector implementing the standardized collector template
    Provides advanced sentiment analysis using specialized ML models for crypto and stock market news
    """
    
    def __init__(self):
        config = MLSentimentCollectorConfig.from_env()
        super().__init__(config)
        
        # Initialize smart model manager
        self.model_manager = get_model_manager()
        
        # ML model pipelines
        self.crypto_sentiment_pipeline = None
        self.stock_sentiment_pipeline = None
        self.model_loading_status = {
            "crypto": False,
            "stock": False
        }
        
        self.logger.info(f"Initialized sentiment collector for environment: {self.model_manager.environment.value}")

    async def collect_data(self) -> int:
        """
        Collect and process sentiment data for news articles
        Returns number of articles processed
        """
        self.logger.info("ml_sentiment_processing_started")
        
        # Ensure models are loaded
        await self._ensure_models_loaded()
        
        # Process pending articles
        processed_count = await self._process_pending_articles(
            limit=self.config.batch_processing_size
        )
        
        self.logger.info("ml_sentiment_processing_completed", 
                        processed=processed_count)
        return processed_count

    async def _ensure_models_loaded(self):
        """Ensure ML models are loaded and ready"""
        
        if not self.crypto_sentiment_pipeline:
            self.logger.info("loading_crypto_model", model=self.config.crypto_model, 
                           environment=self.model_manager.environment.value)
            try:
                # Use smart model manager for environment-aware loading
                self.crypto_sentiment_pipeline = self.model_manager.load_model(
                    self.config.crypto_model, "sentiment"
                )
                self.model_loading_status["crypto"] = True
                self.logger.info("crypto_model_loaded_successfully", 
                               environment=self.model_manager.environment.value)
            except ModelLoadingError as e:
                self.logger.error("crypto_model_loading_failed", error=str(e))
                
                # Only send alerts in production
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    if self.config.enable_alerting:
                        await self._send_alert(AlertRequest(
                            alert_type="model_loading_failure",
                            severity="critical",
                            message=f"Failed to load CryptoBERT model in production: {str(e)}",
                            service=self.config.service_name,
                            additional_data={"model": "CryptoBERT", "error": str(e), "environment": "production"}
                        ))
                    raise
                else:
                    # Use fallback in non-production environments
                    self.logger.warning("using_fallback_crypto_model")
                    self.model_loading_status["crypto"] = True
            except Exception as e:
                self.logger.error("unexpected_crypto_model_error", error=str(e))
                # Fallback handling for unexpected errors
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    raise
                else:
                    self.model_loading_status["crypto"] = True

        if not self.stock_sentiment_pipeline:
            self.logger.info("loading_stock_model", model=self.config.stock_model,
                           environment=self.model_manager.environment.value)
            try:
                # Use smart model manager for environment-aware loading
                self.stock_sentiment_pipeline = self.model_manager.load_model(
                    self.config.stock_model, "sentiment"
                )
                self.model_loading_status["stock"] = True
                self.logger.info("stock_model_loaded_successfully",
                               environment=self.model_manager.environment.value)
            except ModelLoadingError as e:
                self.logger.error("stock_model_loading_failed", error=str(e))
                
                # Only send alerts in production
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    if self.config.enable_alerting:
                        await self._send_alert(AlertRequest(
                            alert_type="model_loading_failure",
                            severity="critical",
                            message=f"Failed to load FinBERT model in production: {str(e)}",
                            service=self.config.service_name,
                            additional_data={"model": "FinBERT", "error": str(e), "environment": "production"}
                        ))
                    raise
                else:
                    # Use fallback in non-production environments
                    self.logger.warning("using_fallback_stock_model")
                    self.model_loading_status["stock"] = True
            except Exception as e:
                self.logger.error("unexpected_stock_model_error", error=str(e))
                # Fallback handling for unexpected errors
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    raise
                else:
                    self.model_loading_status["stock"] = True

    # Model loading is now handled by SmartModelManager
    # Old _load_crypto_model and _load_stock_model methods removed

    async def _process_pending_articles(self, limit: int) -> int:
        """Process pending articles for ML sentiment analysis"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Get articles that need ML sentiment analysis
                cursor.execute("""
                    SELECT id FROM crypto_news 
                    WHERE (ml_sentiment_score IS NULL OR ml_sentiment_score = 0)
                    AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (self.config.days_lookback, limit))
                
                article_ids = [row[0] for row in cursor.fetchall()]
                
                if not article_ids:
                    self.logger.info("no_pending_articles")
                    return 0
                
                self.logger.info("processing_articles", count=len(article_ids))
                
                processed = 0
                errors = 0
                
                # Process articles with rate limiting
                for article_id in article_ids:
                    try:
                        # Rate limiting
                        if self.rate_limiter:
                            await self.rate_limiter.wait_for_token()
                        
                        success = await self._process_single_article(article_id)
                        if success:
                            processed += 1
                            self.metrics['records_processed_total'].labels(operation='sentiment_analysis').inc()
                        else:
                            errors += 1
                            
                    except Exception as e:
                        self.logger.error("article_processing_error", 
                                         article_id=article_id, error=str(e))
                        errors += 1
                        self.collection_errors += 1
                
                # Send alert if too many errors
                if errors > 0 and self.config.enable_alerting and errors >= self.config.alert_error_threshold:
                    await self._send_alert(AlertRequest(
                        alert_type="sentiment_processing_errors",
                        severity="warning",
                        message=f"Multiple sentiment processing failures: {errors}/{len(article_ids)}",
                        service=self.config.service_name,
                        additional_data={"errors": errors, "total": len(article_ids)}
                    ))
                
                self.logger.info("batch_processing_completed",
                                processed=processed, errors=errors, total=len(article_ids))
                return processed
                
        except Exception as e:
            self.logger.error("batch_processing_error", error=str(e))
            self.metrics['database_operations_total'].labels(operation='batch_read', status='error').inc()
            raise

    async def _process_single_article(self, article_id: int) -> bool:
        """Process a single news article for ML sentiment analysis"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Get article data
                cursor.execute("""
                    SELECT id, title, content, market_type, ml_sentiment_score, ml_sentiment_confidence
                    FROM crypto_news 
                    WHERE id = %s
                """, (article_id,))
                
                article = cursor.fetchone()
                if not article:
                    self.logger.warning("article_not_found", article_id=article_id)
                    return False
                
                # Skip if already processed with good confidence
                if (article["ml_sentiment_score"] is not None 
                    and article["ml_sentiment_score"] != 0
                    and article["ml_sentiment_confidence"] > self.config.min_confidence_threshold):
                    return True
                
                # Prepare text for analysis
                text = f"{article['title']}"
                if article["content"]:
                    text += f" {article['content']}"
                
                # Truncate text if too long
                if len(text) > self.config.max_text_length:
                    text = text[:self.config.max_text_length]
                
                # Detect market type if not set
                market_type = article["market_type"] or self._detect_market_type(text)
                
                # Validate data if enabled
                if self.config.enable_data_validation:
                    article_data = {
                        "id": article_id,
                        "title": article['title'],
                        "content": article['content'],
                        "text_length": len(text)
                    }
                    validation_result = await self._validate_data(article_data)
                    if not validation_result["is_valid"]:
                        self.logger.warning("article_validation_failed",
                                          article_id=article_id,
                                          errors=validation_result["errors"])
                        return False
                
                # Analyze sentiment with ML
                ml_score, ml_confidence, ml_analysis = await self._analyze_sentiment_with_ml(
                    text, market_type
                )
                
                # For stock market articles, also analyze as stock sentiment
                stock_score, stock_confidence, stock_analysis = 0.0, 0.0, None
                if market_type == "stock":
                    stock_score, stock_confidence, stock_analysis = (
                        ml_score, ml_confidence, ml_analysis
                    )
                
                # Update database
                cursor.execute("""
                    UPDATE crypto_news 
                    SET ml_sentiment_score = %s,
                        ml_sentiment_confidence = %s,
                        ml_sentiment_analysis = %s,
                        market_type = %s,
                        stock_sentiment_score = %s,
                        stock_sentiment_confidence = %s,
                        stock_sentiment_analysis = %s,
                        sentiment_updated_at = NOW()
                    WHERE id = %s
                """, (
                    ml_score, ml_confidence, ml_analysis, market_type,
                    stock_score, stock_confidence, stock_analysis, article_id
                ))
                
                conn.commit()
                self.metrics['database_operations_total'].labels(operation='update', status='success').inc()
                
                self.logger.debug("article_processed_successfully",
                                 article_id=article_id, market_type=market_type, 
                                 score=ml_score, confidence=ml_confidence)
                return True
                
        except Exception as e:
            self.logger.error("single_article_processing_error", 
                             article_id=article_id, error=str(e))
            self.metrics['database_operations_total'].labels(operation='update', status='error').inc()
            raise

    def _detect_market_type(self, text: str) -> str:
        """Detect if the text is about crypto or stock market"""
        
        text_lower = text.lower()
        
        # Crypto keywords
        crypto_keywords = [
            "bitcoin", "btc", "ethereum", "eth", "cryptocurrency", "crypto", 
            "blockchain", "altcoin", "defi", "nft", "mining", "wallet",
            "exchange", "binance", "coinbase", "dogecoin", "doge", "solana",
            "sol", "cardano", "ada", "polkadot", "dot", "chainlink", "link",
            "uniswap", "pancakeswap", "yield farming", "staking", "metamask",
            "ledger", "trezor", "hodl", "diamond hands", "moon", "pump",
            "dump", "fud", "fomo", "rekt", "rug pull", "whale"
        ]
        
        # Stock market keywords  
        stock_keywords = [
            "stock", "stocks", "equity", "equities", "nasdaq", "nyse", 
            "s&p", "dow jones", "trading", "investor", "portfolio",
            "dividend", "earnings", "revenue", "profit", "market cap",
            "pe ratio", "analyst", "upgrade", "downgrade", "buy", "sell",
            "hold", "bull market", "bear market", "recession", "inflation",
            "fed", "federal reserve", "interest rate", "bond", "bonds",
            "treasury", "etf", "mutual fund", "hedge fund"
        ]
        
        # Count keyword matches
        crypto_count = sum(1 for keyword in crypto_keywords if keyword in text_lower)
        stock_count = sum(1 for keyword in stock_keywords if keyword in text_lower)
        
        # Determine market type based on keyword density
        if crypto_count > stock_count:
            return "crypto"
        elif stock_count > crypto_count:
            return "stock"
        else:
            # Default to crypto for this system
            return "crypto"

    async def _analyze_sentiment_with_ml(self, text: str, market_type: str) -> Tuple[float, float, str]:
        """Analyze sentiment using specialized ML models"""
        
        try:
            # Select appropriate model based on market type
            if market_type == "crypto" and self.crypto_sentiment_pipeline:
                pipeline = self.crypto_sentiment_pipeline
                model_name = "CryptoBERT"
            elif market_type == "stock" and self.stock_sentiment_pipeline:
                pipeline = self.stock_sentiment_pipeline
                model_name = "FinBERT"
            else:
                # Fallback to available model
                if self.crypto_sentiment_pipeline:
                    pipeline = self.crypto_sentiment_pipeline
                    model_name = "CryptoBERT (fallback)"
                elif self.stock_sentiment_pipeline:
                    pipeline = self.stock_sentiment_pipeline
                    model_name = "FinBERT (fallback)"
                else:
                    raise Exception("No ML models available")
            
            # Analyze sentiment (ensure tokenizer truncates to model max length)
            results = pipeline(text, truncation=True, max_length=512)
            
            # Extract sentiment scores - handle different result formats
            sentiment_score, confidence = await self._extract_sentiment_from_results(
                results, model_name
            )
            
            # Ensure score is in [-1, 1] range
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            # Ensure confidence is in [0, 1] range  
            confidence = max(0.0, min(1.0, confidence))
            
            analysis = f"Analyzed using {model_name}: sentiment {sentiment_score:.3f}"
            
            self.logger.debug("ml_sentiment_analysis_completed",
                             model=model_name, score=sentiment_score, confidence=confidence)
            return sentiment_score, confidence, analysis
            
        except Exception as e:
            self.logger.error("ml_sentiment_analysis_failed", error=str(e))
            # Return neutral sentiment with low confidence as fallback
            return 0.0, self.config.fallback_confidence, f"ML analysis failed: {str(e)}"

    async def _extract_sentiment_from_results(self, results, model_name: str) -> Tuple[float, float]:
        """Extract sentiment score and confidence from ML model results"""
        
        try:
            if isinstance(results, list) and len(results) > 0:
                # HuggingFace with return_all_scores=True often returns [[{label,score}...]]
                candidates = None
                if isinstance(results[0], list):
                    candidates = results[0]
                else:
                    candidates = results
                
                scores = {}
                for item in candidates:
                    if isinstance(item, dict) and "label" in item and "score" in item:
                        label = str(item["label"]).lower()
                        score = float(item["score"])
                        scores[label] = score
                
                # Normalize common label variants
                pos = scores.get("positive", scores.get("pos", scores.get("label_2", 0.0)))
                neg = scores.get("negative", scores.get("neg", scores.get("label_0", 0.0)))
                neu = scores.get("neutral", scores.get("neu", scores.get("label_1", 0.0)))
                
                # Compute sentiment score
                if pos or neg:
                    sentiment_score = float(pos) - float(neg)
                    confidence = max(float(pos), float(neg))
                elif neu:
                    sentiment_score = 0.0
                    confidence = float(neu)
                else:
                    # Fallback if labels are unexpected
                    sentiment_score = 0.0
                    confidence = max(scores.values()) if scores else self.config.fallback_confidence
            
            elif isinstance(results, dict) and "label" in results:
                # Handle single result format
                label = results["label"].lower()
                score = results["score"]
                
                # Convert to sentiment score
                if "positive" in label:
                    sentiment_score = score
                elif "negative" in label:
                    sentiment_score = -score
                else:
                    sentiment_score = 0.0
                
                confidence = score
            else:
                # Handle unknown format
                self.logger.warning("unknown_ml_result_format", results=str(results)[:100])
                sentiment_score = 0.0
                confidence = self.config.fallback_confidence
            
            return sentiment_score, confidence
            
        except Exception as e:
            self.logger.error("sentiment_extraction_error", error=str(e))
            return 0.0, self.config.fallback_confidence

    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """
        Backfill missing sentiment analysis for historical articles
        """
        
        self.logger.info("sentiment_backfill_started", periods=len(missing_periods), force=force)
        
        total_processed = 0
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                for period in missing_periods:
                    try:
                        # Get articles in this period that need sentiment analysis
                        if "start_date" in period and "end_date" in period:
                            cursor.execute("""
                                SELECT id FROM crypto_news
                                WHERE created_at BETWEEN %s AND %s
                                AND (ml_sentiment_score IS NULL OR ml_sentiment_score = 0)
                                ORDER BY created_at DESC
                                LIMIT 100
                            """, (period["start_date"], period["end_date"]))
                        else:
                            # Single date period
                            cursor.execute("""
                                SELECT id FROM crypto_news
                                WHERE DATE(created_at) = %s
                                AND (ml_sentiment_score IS NULL OR ml_sentiment_score = 0)
                                ORDER BY created_at DESC
                                LIMIT 50
                            """, (period.get("date"),))
                        
                        article_ids = [row[0] for row in cursor.fetchall()]
                        
                        # Process articles in this period
                        for article_id in article_ids:
                            if self.rate_limiter:
                                await self.rate_limiter.wait_for_token()
                            
                            success = await self._process_single_article(article_id)
                            if success:
                                total_processed += 1
                            
                            # Small delay to prevent overload
                            await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        self.logger.error("backfill_period_error", period=period, error=str(e))
        
        except Exception as e:
            self.logger.error("sentiment_backfill_error", error=str(e))
            raise
        
        self.logger.info("sentiment_backfill_completed", processed=total_processed)
        return total_processed

    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """Get status of sentiment analysis in crypto_news table"""
        
        try:
            # Check sentiment analysis coverage
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN ml_sentiment_score IS NOT NULL AND ml_sentiment_score != 0 THEN 1 END) as analyzed_articles,
                    AVG(CASE WHEN ml_sentiment_score IS NOT NULL AND ml_sentiment_score != 0 THEN ml_sentiment_confidence END) as avg_confidence,
                    MAX(sentiment_updated_at) as last_analysis,
                    COUNT(DISTINCT market_type) as market_types
                FROM crypto_news
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            
            result = cursor.fetchone()
            
            # Get market type breakdown
            cursor.execute("""
                SELECT market_type, COUNT(*) as count,
                       AVG(ml_sentiment_score) as avg_sentiment
                FROM crypto_news 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND ml_sentiment_score IS NOT NULL
                GROUP BY market_type
            """)
            
            market_breakdown = {row[0]: {"count": row[1], "avg_sentiment": row[2]} 
                              for row in cursor.fetchall()}
            
            total = result[0] if result else 0
            analyzed = result[1] if result else 0
            coverage = (analyzed / max(total, 1)) * 100
            
            return {
                "sentiment_analysis": {
                    "total_articles_7d": total,
                    "analyzed_articles": analyzed,
                    "coverage_percentage": round(coverage, 2),
                    "avg_confidence": result[2] if result and result[2] else 0,
                    "last_analysis": result[3] if result and result[3] else None,
                    "market_types": result[4] if result else 0,
                    "market_breakdown": market_breakdown,
                    "models_loaded": self.model_loading_status
                }
            }
            
        except mysql.connector.Error as e:
            return {"error": str(e)}

    async def _analyze_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Analyze missing sentiment analysis data
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Find articles without sentiment analysis
                cursor.execute("""
                    SELECT DATE(created_at) as analysis_date,
                           COUNT(*) as total_articles,
                           COUNT(CASE WHEN ml_sentiment_score IS NULL OR ml_sentiment_score = 0 THEN 1 END) as missing_sentiment
                    FROM crypto_news
                    WHERE created_at BETWEEN %s AND %s
                    GROUP BY DATE(created_at)
                    HAVING missing_sentiment > 0
                    ORDER BY analysis_date
                """, (start_date, end_date))
                
                results = cursor.fetchall()
                
                missing_periods = []
                for analysis_date, total_articles, missing_sentiment in results:
                    if missing_sentiment > 0:
                        missing_periods.append({
                            "date": analysis_date,
                            "total_articles": total_articles,
                            "missing_sentiment": missing_sentiment,
                            "coverage_percentage": ((total_articles - missing_sentiment) / total_articles) * 100,
                            "reason": "missing_ml_sentiment"
                        })
                
                return missing_periods
                
        except Exception as e:
            self.logger.error("missing_sentiment_analysis_error", error=str(e))
            return []

    async def _estimate_backfill_records(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> int:
        """
        Estimate number of articles that would be backfilled for sentiment analysis
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM crypto_news
                    WHERE created_at BETWEEN %s AND %s
                    AND (ml_sentiment_score IS NULL OR ml_sentiment_score = 0)
                """, (start_date, end_date))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error("sentiment_backfill_estimation_error", error=str(e))
            return 0

    async def _get_required_fields(self) -> List[str]:
        """Get required fields for data validation"""
        return ["id", "title", "text_length"]

    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Generate comprehensive data quality report for sentiment analysis"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Get total records needing sentiment analysis
                cursor.execute("""
                    SELECT COUNT(*) FROM crypto_news 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """)
                total_records = cursor.fetchone()[0]
                
                # Get records with valid sentiment analysis
                cursor.execute("""
                    SELECT COUNT(*) FROM crypto_news 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    AND ml_sentiment_score IS NOT NULL 
                    AND ml_sentiment_score != 0
                    AND ml_sentiment_confidence > %s
                """, (self.config.min_confidence_threshold,))
                valid_records = cursor.fetchone()[0]
                
                # Get records with low confidence
                cursor.execute("""
                    SELECT COUNT(*) FROM crypto_news 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    AND ml_sentiment_confidence IS NOT NULL
                    AND ml_sentiment_confidence <= %s
                """, (self.config.min_confidence_threshold,))
                low_confidence_records = cursor.fetchone()[0]
                
                invalid_records = total_records - valid_records
                data_quality_score = (valid_records / max(total_records, 1)) * 100
                
                validation_errors = []
                if invalid_records > 0:
                    validation_errors.append(f"{invalid_records} records missing sentiment analysis")
                if low_confidence_records > 0:
                    validation_errors.append(f"{low_confidence_records} records with low confidence")
                if not self.model_loading_status["crypto"]:
                    validation_errors.append("CryptoBERT model not loaded")
                if not self.model_loading_status["stock"]:
                    validation_errors.append("FinBERT model not loaded")
                
                return DataQualityReport(
                    total_records=total_records,
                    valid_records=valid_records,
                    invalid_records=invalid_records,
                    duplicate_records=0,  # Not applicable for sentiment analysis
                    validation_errors=validation_errors,
                    data_quality_score=data_quality_score
                )
                
        except Exception as e:
            self.logger.error("sentiment_quality_report_error", error=str(e))
            return DataQualityReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                duplicate_records=0,
                validation_errors=[f"Error generating report: {str(e)}"],
                data_quality_score=0.0
            )

async def main():
    """Main function to run the enhanced ML sentiment collector"""
    collector = EnhancedMLSentimentCollector()
    
    # Start the collection loop
    collection_task = asyncio.create_task(collector.run_collection_loop())
    
    # Start the web server for API endpoints
    server_task = asyncio.create_task(
        asyncio.to_thread(collector.run_server, host="0.0.0.0", port=8000)
    )
    
    # Wait for either task to complete (or shutdown signal)
    try:
        await asyncio.gather(collection_task, server_task, return_exceptions=True)
    except KeyboardInterrupt:
        collector.logger.info("shutdown_requested", signal="SIGINT")
        collector._shutdown_event.set()

if __name__ == "__main__":
    asyncio.run(main())