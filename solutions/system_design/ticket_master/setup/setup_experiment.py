#!/usr/bin/env python3
"""
Setup script for Ticketmaster Elasticsearch experiment.
Creates indices, mappings, and prepares the environment.
"""

import sys
import os

# Add src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
import time
import json

def wait_for_elasticsearch(es, max_retries=30, delay=2):
    """Wait for Elasticsearch to be ready."""
    print("Waiting for Elasticsearch to be ready...")

    for attempt in range(max_retries):
        try:
            health = es.cluster.health(timeout="10s")
            if health['status'] in ['yellow', 'green']:
                print(f"✅ Elasticsearch is ready! Status: {health['status']}")
                return True
        except Exception as e:
            print(f"⏳ Attempt {attempt + 1}/{max_retries}: {str(e)[:100]}")
            time.sleep(delay)

    print("❌ Failed to connect to Elasticsearch")
    return False

def create_indices(es):
    """Create all indices with proper mappings."""

    # Import the mapping configurations
    from elasticsearch_mappings import TicketmasterElasticsearchMappings, create_lifecycle_policies

    mappings_manager = TicketmasterElasticsearchMappings(es)

    print("\n📋 Creating Index Lifecycle Policies...")
    try:
        create_lifecycle_policies(es)
        print("✅ Lifecycle policies created successfully")
    except Exception as e:
        print(f"⚠️  Lifecycle policy creation failed: {e}")

    print("\n🏗️  Creating Index Templates...")
    try:
        mappings_manager.create_index_templates()
        print("✅ Index templates created successfully")
    except Exception as e:
        print(f"⚠️  Template creation failed: {e}")

    print("\n📊 Creating Indices...")
    created_indices = mappings_manager.create_indices()

    if created_indices:
        print(f"✅ Created {len(created_indices)} indices: {', '.join(created_indices)}")
    else:
        print("ℹ️  All indices already exist")

    return True

def verify_setup(es):
    """Verify that the setup was successful."""
    print("\n🔍 Verifying Setup...")

    try:
        # Check cluster health
        health = es.cluster.health()
        print(f"✅ Cluster health: {health['status']}")
        print(f"   - Nodes: {health['number_of_nodes']}")
        print(f"   - Data nodes: {health['number_of_data_nodes']}")

        # List all indices
        indices = es.cat.indices(format='json')
        ticketmaster_indices = [idx for idx in indices if any(
            name in idx['index'] for name in ['events', 'user_behavior', 'fraud_detection', 'analytics']
        )]

        print(f"\n📋 Ticketmaster Indices ({len(ticketmaster_indices)}):")
        for idx in ticketmaster_indices:
            print(f"   - {idx['index']}: {idx['docs.count']} docs, {idx['store.size']}")

        # Test a simple query
        if any('events' in idx['index'] for idx in ticketmaster_indices):
            test_query = es.search(index='events', body={'query': {'match_all': {}}}, size=0)
            print(f"✅ Test query successful: {test_query['hits']['total']['value']} total events")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE! Next Steps:")
    print("="*60)
    print()
    print("1. 📦 Load Sample Data:")
    print("   python ingest_sample_data.py")
    print()
    print("2. 🧪 Run Experiments:")
    print("   python experiments.py --experiment search")
    print("   python experiments.py --experiment geo")
    print("   python experiments.py --experiment fraud")
    print()
    print("3. 🔍 Explore with Kibana:")
    print("   Open: http://localhost:5601")
    print("   Create index patterns for: events*, user_behavior*")
    print()
    print("4. 📊 Direct Elasticsearch Access:")
    print("   curl http://localhost:9200/_cat/indices")
    print("   curl http://localhost:9200/events/_search")
    print()
    print("5. 📚 Read the Setup Guide:")
    print("   cat SETUP_GUIDE.md")
    print()

def main():
    """Main setup function."""
    print("🚀 Ticketmaster Elasticsearch Setup Starting...")
    print("=" * 50)

    # Connect to Elasticsearch
    try:
        es = Elasticsearch(
            hosts=['http://localhost:9200'],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
    except Exception as e:
        print(f"❌ Failed to create Elasticsearch client: {e}")
        sys.exit(1)

    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch(es):
        print("\n❌ Setup failed: Elasticsearch not available")
        print("\n💡 Try:")
        print("   docker compose up -d")
        print("   docker compose logs elasticsearch")
        sys.exit(1)

    # Create indices
    if not create_indices(es):
        print("❌ Setup failed: Could not create indices")
        sys.exit(1)

    # Verify setup
    if not verify_setup(es):
        print("❌ Setup failed: Verification failed")
        sys.exit(1)

    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()