#!/usr/bin/env python3
"""
Sample data ingestion script for Ticketmaster Elasticsearch experiment.
Creates realistic event data, user behavior, and fraud detection records.
"""

import random
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
import sys

# Sample data for realistic event generation
ARTISTS = [
    "Taylor Swift", "Ed Sheeran", "Adele", "Bruno Mars", "Coldplay", "The Weeknd",
    "Billie Eilish", "Drake", "Ariana Grande", "Post Malone", "Dua Lipa", "Harry Styles",
    "Beyoncé", "Justin Bieber", "Imagine Dragons", "Maroon 5", "OneRepublic", "Shawn Mendes"
]

VENUES = [
    {"name": "Madison Square Garden", "city": "New York", "state": "NY", "capacity": 20000, "lat": 40.7505, "lon": -73.9934},
    {"name": "Staples Center", "city": "Los Angeles", "state": "CA", "capacity": 21000, "lat": 34.0430, "lon": -118.2673},
    {"name": "United Center", "city": "Chicago", "state": "IL", "capacity": 23500, "lat": 41.8807, "lon": -87.6742},
    {"name": "TD Garden", "city": "Boston", "state": "MA", "capacity": 19580, "lat": 42.3662, "lon": -71.0621},
    {"name": "American Airlines Arena", "city": "Miami", "state": "FL", "capacity": 19600, "lat": 25.7814, "lon": -80.1870},
    {"name": "Oracle Arena", "city": "Oakland", "state": "CA", "capacity": 19596, "lat": 37.7503, "lon": -122.2011},
    {"name": "Pepsi Center", "city": "Denver", "state": "CO", "capacity": 20000, "lat": 39.7487, "lon": -105.0077},
    {"name": "AT&T Center", "city": "San Antonio", "state": "TX", "capacity": 18500, "lat": 29.4270, "lon": -98.4375},
    {"name": "KeyArena", "city": "Seattle", "state": "WA", "capacity": 17100, "lat": 47.6221, "lon": -122.3540},
    {"name": "Philips Arena", "city": "Atlanta", "state": "GA", "capacity": 21000, "lat": 33.7573, "lon": -84.3963}
]

CATEGORIES = ["music", "sports", "theater", "comedy", "family", "festivals"]
SUBCATEGORIES = {
    "music": ["pop", "rock", "hip-hop", "country", "electronic", "jazz"],
    "sports": ["basketball", "football", "baseball", "hockey", "soccer"],
    "theater": ["musical", "drama", "comedy", "opera"],
    "comedy": ["stand-up", "improv", "sketch"],
    "family": ["children", "circus", "magic"],
    "festivals": ["music-festival", "food", "cultural", "arts"]
}

def generate_events(num_events=50):
    """Generate sample events with realistic data."""
    events = []

    for i in range(num_events):
        venue = random.choice(VENUES)
        category = random.choice(CATEGORIES)
        subcategory = random.choice(SUBCATEGORIES[category])

        # Generate realistic dates (next 6 months)
        start_date = datetime.now() + timedelta(days=random.randint(1, 180))

        # Create event
        if category == "music":
            artist = random.choice(ARTISTS)
            title = f"{artist} - {random.choice(['World Tour', 'Live Concert', 'Unplugged', 'Greatest Hits Tour'])}"
        elif category == "sports":
            teams = ["Lakers vs Warriors", "Yankees vs Red Sox", "Cowboys vs Giants", "Celtics vs Heat"]
            title = random.choice(teams)
            artist = "Sports Event"
        else:
            title = f"{category.title()} Event {i+1}"
            artist = f"Performer {random.randint(1, 100)}"

        # Pricing based on venue size and artist popularity
        base_price = random.randint(30, 150)
        if artist in ["Taylor Swift", "Beyoncé", "Ed Sheeran"]:
            base_price *= 2  # Premium pricing for popular artists

        min_price = base_price
        max_price = base_price + random.randint(100, 500)

        # Availability
        total_seats = venue["capacity"]
        sold_percentage = random.uniform(0.1, 0.95)
        available_seats = int(total_seats * (1 - sold_percentage))
        sold_out = available_seats == 0

        # Popularity score based on artist and sales
        popularity_base = 50
        if artist in ["Taylor Swift", "Beyoncé", "Ed Sheeran", "Drake"]:
            popularity_base = 90
        elif artist in ["Billie Eilish", "The Weeknd", "Harry Styles"]:
            popularity_base = 75

        popularity_score = popularity_base + random.randint(-10, 10)

        event = {
            "event_id": f"event_{i+1:03d}",
            "title": title,
            "artist": artist,
            "venue": {
                "name": venue["name"],
                "location": {"lat": venue["lat"], "lon": venue["lon"]},
                "city": venue["city"],
                "state": venue["state"],
                "capacity": venue["capacity"],
                "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Broadway', 'Park Ave', 'Stadium Way'])}"
            },
            "category": category,
            "subcategory": subcategory,
            "date": start_date.isoformat(),
            "end_date": (start_date + timedelta(hours=3)).isoformat(),
            "price_range": {
                "min": min_price,
                "max": max_price,
                "currency": "USD"
            },
            "availability": {
                "total_seats": total_seats,
                "available_seats": available_seats,
                "sold_out": sold_out,
                "last_updated": datetime.now().isoformat()
            },
            "popularity_score": popularity_score,
            "ratings": {
                "average": round(random.uniform(3.5, 4.9), 1),
                "count": random.randint(50, 1000)
            },
            "tags": [category, subcategory, venue["city"].lower()],
            "description": f"Don't miss {artist} live at {venue['name']}! An unforgettable {category} experience in {venue['city']}.",
            "image_url": f"https://ticketmaster.com/images/event_{i+1:03d}.jpg",
            "external_urls": {
                "official": f"https://{artist.lower().replace(' ', '')}.com",
                "social": f"https://twitter.com/{artist.lower().replace('', '')}"
            },
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "indexed_at": datetime.now().isoformat()
        }

        events.append(event)

    return events

def generate_user_behavior(num_records=500):
    """Generate sample user behavior data."""
    behaviors = []
    user_ids = [f"user_{i:03d}" for i in range(1, 101)]  # 100 users
    session_ids = [f"session_{i:05d}" for i in range(1, num_records//5)]  # ~5 actions per session

    action_types = ["search", "view_event", "add_to_cart", "purchase", "remove_from_cart", "filter_apply"]
    search_queries = [
        "Taylor Swift", "concerts near me", "basketball games", "theater shows",
        "Ed Sheeran tour", "New York events", "weekend shows", "cheap tickets",
        "Madison Square Garden", "family events", "comedy shows", "festivals"
    ]

    for i in range(num_records):
        user_id = random.choice(user_ids)
        session_id = random.choice(session_ids)
        action_type = random.choice(action_types)

        # Generate timestamp within last 30 days
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        behavior = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "action_type": action_type,
            "user_agent": random.choice([
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            ]),
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "location": {
                "lat": random.uniform(25.0, 49.0),
                "lon": random.uniform(-125.0, -66.0)
            },
            "referrer": random.choice([
                "https://google.com", "https://facebook.com", "direct",
                "https://twitter.com", "email_campaign"
            ])
        }

        # Add action-specific data
        if action_type == "search":
            behavior["search_query"] = random.choice(search_queries)
        elif action_type in ["view_event", "add_to_cart", "purchase"]:
            behavior["event_id"] = f"event_{random.randint(1, 50):03d}"

        # Add filters for search actions
        if action_type in ["search", "filter_apply"]:
            filters = []
            if random.random() < 0.3:  # 30% chance of category filter
                filters.append({"filter_type": "category", "filter_value": random.choice(CATEGORIES)})
            if random.random() < 0.2:  # 20% chance of location filter
                filters.append({"filter_type": "location", "filter_value": random.choice([v["city"] for v in VENUES])})
            if random.random() < 0.15:  # 15% chance of price filter
                filters.append({"filter_type": "price", "filter_value": f"under_{random.choice([50, 100, 200])}"})

            behavior["filters_applied"] = filters

        # Conversion tracking
        behavior["conversion"] = action_type == "purchase"
        if behavior["conversion"]:
            behavior["purchase_amount"] = random.uniform(50, 400)

        behaviors.append(behavior)

    return behaviors

def generate_fraud_data(num_records=20):
    """Generate sample fraud detection records."""
    fraud_records = []

    # Generate some high-risk scenarios
    risk_scenarios = [
        {"type": "bot_behavior", "base_score": 80},
        {"type": "high_quantity", "base_score": 60},
        {"type": "rapid_fire", "base_score": 70},
        {"type": "ip_anomaly", "base_score": 50},
        {"type": "multiple_events", "base_score": 40}
    ]

    for i in range(num_records):
        scenario = random.choice(risk_scenarios)
        session_id = f"session_{random.randint(10000, 99999)}"
        user_id = f"user_{random.randint(1, 100):03d}" if random.random() > 0.2 else None

        # Generate actions based on scenario
        actions = []
        if scenario["type"] == "rapid_fire":
            # Rapid consecutive actions
            base_time = datetime.now() - timedelta(hours=random.randint(1, 24))
            for j in range(random.randint(10, 20)):
                action_time = base_time + timedelta(seconds=j * random.uniform(0.5, 2.0))
                actions.append({
                    "action_type": random.choice(["search", "view_event", "add_to_cart"]),
                    "timestamp": action_time.isoformat(),
                    "event_id": f"event_{random.randint(1, 50):03d}",
                    "quantity": random.randint(1, 4),
                    "price": random.uniform(50, 200),
                    "speed": 60 / max(0.5, random.uniform(0.5, 2.0))  # actions per minute
                })
        elif scenario["type"] == "high_quantity":
            # High quantity purchases
            for j in range(random.randint(3, 8)):
                actions.append({
                    "action_type": "add_to_cart",
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 30))).isoformat(),
                    "event_id": f"event_{random.randint(1, 50):03d}",
                    "quantity": random.randint(15, 50),  # Unusually high
                    "price": random.uniform(100, 300),
                    "speed": random.uniform(5, 15)
                })
        else:
            # Normal actions with some suspicious indicators
            for j in range(random.randint(5, 15)):
                actions.append({
                    "action_type": random.choice(["search", "view_event", "add_to_cart", "purchase"]),
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                    "event_id": f"event_{random.randint(1, 50):03d}",
                    "quantity": random.randint(1, 8),
                    "price": random.uniform(50, 250),
                    "speed": random.uniform(2, 20)
                })

        # Risk indicators based on scenario
        risk_indicators = {
            "multiple_events": len(set(a["event_id"] for a in actions)) > 5,
            "high_quantity": max(a["quantity"] for a in actions) > 10,
            "rapid_fire": min(a["speed"] for a in actions) > 10,
            "suspicious_ip": random.random() < 0.3,
            "bot_like_behavior": scenario["type"] == "bot_behavior"
        }

        # Calculate risk score
        risk_score = scenario["base_score"] + random.randint(-15, 15)
        risk_score = max(0, min(100, risk_score))  # Clamp between 0-100

        fraud_record = {
            "session_id": session_id,
            "user_id": user_id,
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (compatible; Googlebot/2.1)",  # Bot user agent
                "Python-requests/2.25.1",  # Script user agent
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # Normal browser
            ]),
            "device_fingerprint": f"fp_{random.randint(100000, 999999)}",
            "actions": actions,
            "risk_indicators": risk_indicators,
            "risk_score": risk_score,
            "flagged": risk_score > 60,
            "reviewed": random.random() < 0.3,
            "timestamp": datetime.now().isoformat()
        }

        fraud_records.append(fraud_record)

    return fraud_records

def ingest_data(es, index_name, documents, doc_type="doc"):
    """Bulk ingest documents into Elasticsearch."""
    print(f"📦 Ingesting {len(documents)} documents into {index_name}...")

    def doc_generator():
        for i, doc in enumerate(documents):
            yield {
                "_index": index_name,
                "_id": doc.get("event_id") or doc.get("session_id") or f"{doc_type}_{i+1}",
                "_source": doc
            }

    try:
        success, failed = bulk(es, doc_generator(), chunk_size=100, request_timeout=60)
        print(f"✅ Successfully indexed {success} documents")
        if failed:
            print(f"⚠️  {len(failed)} documents failed to index")
        return success
    except Exception as e:
        print(f"❌ Bulk indexing failed: {e}")
        return 0

def main():
    """Main data ingestion function."""
    print("📊 Ticketmaster Sample Data Ingestion Starting...")
    print("=" * 50)

    # Connect to Elasticsearch
    try:
        es = Elasticsearch(
            hosts=['http://localhost:9200'],
            request_timeout=60,
            max_retries=3,
            retry_on_timeout=True
        )

        # Test connection
        if not es.ping():
            raise Exception("Could not connect to Elasticsearch")

        print("✅ Connected to Elasticsearch")

    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")
        print("💡 Make sure Elasticsearch is running: docker compose up -d")
        sys.exit(1)

    total_ingested = 0

    # Generate and ingest events
    print("\n🎭 Generating Events...")
    events = generate_events(50)
    total_ingested += ingest_data(es, "events", events, "event")

    # Generate and ingest user behavior
    print("\n👥 Generating User Behavior...")
    behaviors = generate_user_behavior(500)
    total_ingested += ingest_data(es, "user_behavior", behaviors, "behavior")

    # Generate and ingest fraud data
    print("\n🚨 Generating Fraud Detection Data...")
    fraud_data = generate_fraud_data(20)
    total_ingested += ingest_data(es, "fraud_detection", fraud_data, "fraud")

    # Generate some analytics data (simplified)
    print("\n📈 Generating Analytics Data...")
    analytics_data = []
    for i in range(30):  # 30 days of analytics
        date = datetime.now() - timedelta(days=i)
        analytics_data.append({
            "date": date.date().isoformat(),
            "event_id": f"event_{random.randint(1, 50):03d}",
            "metrics": {
                "page_views": random.randint(100, 10000),
                "searches": random.randint(50, 5000),
                "clicks": random.randint(25, 2500),
                "purchases": random.randint(5, 250),
                "revenue": round(random.uniform(500, 25000), 2),
                "conversion_rate": round(random.uniform(0.02, 0.15), 3)
            },
            "dimensions": {
                "category": random.choice(CATEGORIES),
                "artist": random.choice(ARTISTS),
                "venue": random.choice(VENUES)["name"],
                "city": random.choice(VENUES)["city"],
                "price_tier": random.choice(["budget", "mid-tier", "premium", "vip"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "traffic_source": random.choice(["organic", "paid", "social", "email", "direct"])
            },
            "timestamp": date.isoformat()
        })

    total_ingested += ingest_data(es, "analytics", analytics_data, "analytics")

    # Refresh indices to make data immediately searchable
    print("\n🔄 Refreshing indices...")
    for index in ["events", "user_behavior", "fraud_detection", "analytics"]:
        try:
            es.indices.refresh(index=index)
            print(f"✅ Refreshed {index}")
        except Exception as e:
            print(f"⚠️  Failed to refresh {index}: {e}")

    # Summary
    print("\n" + "="*50)
    print("🎉 DATA INGESTION COMPLETE!")
    print("="*50)
    print(f"📊 Total documents ingested: {total_ingested}")
    print("\n📋 Sample Data Summary:")
    print(f"   • 50 Events (concerts, sports, theater)")
    print(f"   • 500 User Behavior records (30 days)")
    print(f"   • 20 Fraud detection records")
    print(f"   • 30 Analytics records")
    print("\n🔍 Quick Verification:")
    print("   curl http://localhost:9200/_cat/indices")
    print("   curl 'http://localhost:9200/events/_search?size=1&pretty'")
    print("\n🧪 Ready for Experiments:")
    print("   python experiments.py --experiment search")

if __name__ == "__main__":
    main()