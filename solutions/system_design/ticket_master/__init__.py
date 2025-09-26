"""
Ticketmaster System Design Implementation

A comprehensive system design example showcasing Elasticsearch integration
for event ticketing, search, fraud detection, and real-time analytics.

This package demonstrates:
- Full-text event search with faceted filtering
- Geo-location based search
- Real-time inventory management
- Fraud detection and bot prevention
- User behavior analytics and recommendations
- Scalable Elasticsearch cluster design

Quick Start:
1. docker compose up -d
2. python setup/setup_experiment.py
3. python setup/ingest_sample_data.py
4. python experiments.py --experiment search

Directory Structure:
- src/: Core implementation modules
- setup/: Setup and data loading scripts
- docs/: Comprehensive documentation
"""

__version__ = "1.0.0"
__author__ = "System Design Primer"

from .src.elasticsearch_mappings import TicketmasterElasticsearchMappings, create_lifecycle_policies
from .src.search_service import TicketmasterSearchService
from .src.fraud_detection import TicketmasterFraudDetection, FraudAssessment, RiskIndicator

__all__ = [
    'TicketmasterElasticsearchMappings',
    'TicketmasterSearchService',
    'TicketmasterFraudDetection',
    'FraudAssessment',
    'RiskIndicator',
    'create_lifecycle_policies'
]