#!/usr/bin/env python3
"""
Mock transformers module for unit tests
Avoids heavy ML dependencies while enabling test execution
"""

class MockPipeline:
    """Mock transformers pipeline"""
    def __init__(self, task, model=None, **kwargs):
        self.task = task
        self.model = model
    
    def __call__(self, text):
        # Return mock sentiment analysis result
        if isinstance(text, list):
            return [{'label': 'POSITIVE', 'score': 0.85} for _ in text]
        return {'label': 'POSITIVE', 'score': 0.85}

class MockAutoTokenizer:
    """Mock AutoTokenizer"""
    @classmethod
    def from_pretrained(cls, model_name, **kwargs):
        return cls()
    
    def tokenize(self, text):
        return text.split()
    
    def encode(self, text):
        return [1, 2, 3, 4]

class MockAutoModelForSequenceClassification:
    """Mock AutoModelForSequenceClassification"""
    @classmethod
    def from_pretrained(cls, model_name, **kwargs):
        return cls()
    
    def eval(self):
        return self

def pipeline(task, model=None, **kwargs):
    """Mock pipeline function"""
    return MockPipeline(task, model, **kwargs)

# Export mock classes
AutoTokenizer = MockAutoTokenizer
AutoModelForSequenceClassification = MockAutoModelForSequenceClassification