#!/usr/bin/env python3
"""
Interactive experiments for Ticketmaster Elasticsearch system.
Demonstrates various search patterns and analytics queries.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from tabulate import tabulate

class TicketmasterExperiments:
    """Run various Elasticsearch experiments for learning."""

    def __init__(self):
        try:
            self.es = Elasticsearch(
                hosts=['http://localhost:9200'],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            if not self.es.ping():
                raise Exception("Cannot connect to Elasticsearch")
            print("✅ Connected to Elasticsearch")
        except Exception as e:
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            print("💡 Make sure Elasticsearch is running: docker compose up -d")
            sys.exit(1)

    def print_header(self, title, description=""):
        """Print experiment header."""
        print("\n" + "="*60)
        print(f"🧪 {title}")
        print("="*60)
        if description:
            print(f"📝 {description}")
            print()

    def print_query(self, query_name, query_body):
        """Pretty print the Elasticsearch query."""
        print(f"🔍 {query_name}:")
        print("```json")
        print(json.dumps(query_body, indent=2))
        print("```")
        print()

    def print_results(self, response, show_source=True, max_results=5):
        """Pretty print search results."""
        hits = response.get('hits', {})
        total = hits.get('total', {}).get('value', 0)
        took = response.get('took', 0)

        print(f"📊 Results: {total} total hits ({took}ms)")
        print()

        if hits.get('hits'):
            results_data = []
            for i, hit in enumerate(hits['hits'][:max_results]):
                source = hit['_source']
                score = hit.get('_score', 0)

                if 'title' in source:  # Event document
                    results_data.append([
                        i+1,
                        source.get('title', 'N/A')[:40],
                        source.get('artist', 'N/A')[:20],
                        source.get('venue', {}).get('city', 'N/A'),
                        f"${source.get('price_range', {}).get('min', 0)}",
                        f"{score:.2f}" if score is not None else "N/A"
                    ])
                elif 'search_query' in source:  # Behavior document
                    results_data.append([
                        i+1,
                        source.get('search_query', 'N/A')[:30],
                        source.get('action_type', 'N/A'),
                        source.get('user_id', 'N/A'),
                        source.get('timestamp', 'N/A')[:19],
                        f"{score:.2f}" if score is not None else "N/A"
                    ])
                elif 'risk_score' in source:  # Fraud document
                    results_data.append([
                        i+1,
                        source.get('session_id', 'N/A'),
                        f"{source.get('risk_score', 0):.1f}",
                        source.get('flagged', False),
                        len(source.get('actions', [])),
                        f"{score:.2f}" if score is not None else "N/A"
                    ])

            if 'title' in hits['hits'][0]['_source']:
                headers = ['#', 'Event Title', 'Artist', 'City', 'Price', 'Score']
            elif 'search_query' in hits['hits'][0]['_source']:
                headers = ['#', 'Search Query', 'Action', 'User', 'Timestamp', 'Score']
            elif 'risk_score' in hits['hits'][0]['_source']:
                headers = ['#', 'Session', 'Risk Score', 'Flagged', 'Actions', 'Score']

            print(tabulate(results_data, headers=headers, tablefmt='grid'))
        else:
            print("No results found.")

    def print_aggregations(self, response):
        """Pretty print aggregation results."""
        aggs = response.get('aggregations', {})
        if not aggs:
            return

        print("\n📈 Aggregations:")
        for agg_name, agg_data in aggs.items():
            print(f"\n🔸 {agg_name}:")
            if 'buckets' in agg_data:
                agg_results = []
                for bucket in agg_data['buckets'][:10]:  # Show top 10
                    key = bucket.get('key', 'N/A')
                    if isinstance(key, str) and len(key) > 30:
                        key = key[:30] + "..."
                    agg_results.append([
                        key,
                        bucket.get('doc_count', 0),
                        f"{bucket.get('doc_count', 0) / response['hits']['total']['value'] * 100:.1f}%"
                    ])
                print(tabulate(agg_results, headers=['Value', 'Count', '%'], tablefmt='simple'))
            elif 'value' in agg_data:
                print(f"   Value: {agg_data['value']:.2f}")

    def experiment_search(self):
        """Basic search experiment."""
        self.print_header(
            "Basic Event Search",
            "Demonstrates full-text search, filtering, and sorting"
        )

        # Experiment 1: Simple text search
        query1 = {
            "query": {
                "multi_match": {
                    "query": "Taylor Swift",
                    "fields": ["title^3", "artist^2", "venue.name"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "sort": [
                {"popularity_score": {"order": "desc"}},
                {"_score": {"order": "desc"}}
            ],
            "size": 5
        }

        self.print_query("Simple Text Search for 'Taylor Swift'", query1)
        response1 = self.es.search(index="events", body=query1)
        self.print_results(response1)

        print("\n" + "-"*60)

        # Experiment 2: Search with filters
        query2 = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": "concert",
                                "fields": ["title", "description", "category"]
                            }
                        }
                    ],
                    "filter": [
                        {"range": {"price_range.min": {"lte": 200}}},
                        {"term": {"category": "music"}},
                        {"term": {"availability.sold_out": False}}
                    ]
                }
            },
            "sort": [{"date": {"order": "asc"}}],
            "size": 5
        }

        self.print_query("Filtered Search: Music concerts under $200", query2)
        response2 = self.es.search(index="events", body=query2)
        self.print_results(response2)

    def experiment_facets(self):
        """Faceted search experiment."""
        self.print_header(
            "Faceted Search & Navigation",
            "Shows how to implement search facets for filtering"
        )

        query = {
            "query": {"match_all": {}},
            "size": 3,
            "aggs": {
                "categories": {
                    "terms": {"field": "category", "size": 10}
                },
                "price_ranges": {
                    "range": {
                        "field": "price_range.min",
                        "ranges": [
                            {"key": "Budget (Under $50)", "to": 50},
                            {"key": "Moderate ($50-100)", "from": 50, "to": 100},
                            {"key": "Premium ($100-200)", "from": 100, "to": 200},
                            {"key": "Luxury ($200+)", "from": 200}
                        ]
                    }
                },
                "cities": {
                    "terms": {"field": "venue.city", "size": 8}
                },
                "availability": {
                    "terms": {"field": "availability.sold_out"}
                }
            }
        }

        self.print_query("Faceted Search Query", query)
        response = self.es.search(index="events", body=query)
        self.print_results(response, max_results=3)
        self.print_aggregations(response)

    def experiment_geo(self):
        """Geo-location search experiment."""
        self.print_header(
            "Geo-Location Search",
            "Find events near specific locations using geo queries"
        )

        # NYC coordinates
        nyc_lat, nyc_lon = 40.7128, -73.9934

        query = {
            "query": {
                "bool": {
                    "must": {"match_all": {}},
                    "filter": [
                        {
                            "geo_distance": {
                                "distance": "100mi",
                                "venue.location": {"lat": nyc_lat, "lon": nyc_lon}
                            }
                        },
                        {"term": {"availability.sold_out": False}}
                    ]
                }
            },
            "sort": [
                {
                    "_geo_distance": {
                        "venue.location": {"lat": nyc_lat, "lon": nyc_lon},
                        "order": "asc",
                        "unit": "mi"
                    }
                }
            ],
            "size": 5
        }

        self.print_query("Events within 100 miles of NYC", query)
        response = self.es.search(index="events", body=query)

        # Custom result formatting for geo queries
        hits = response.get('hits', {})
        print(f"📊 Results: {hits.get('total', {}).get('value', 0)} events near NYC")
        print()

        if hits.get('hits'):
            geo_results = []
            for i, hit in enumerate(hits['hits']):
                source = hit['_source']
                distance = hit.get('sort', [0])[0]
                venue = source.get('venue', {})

                geo_results.append([
                    i+1,
                    source.get('title', 'N/A')[:35],
                    venue.get('name', 'N/A')[:25],
                    venue.get('city', 'N/A'),
                    f"{distance:.1f} mi",
                    f"${source.get('price_range', {}).get('min', 0)}"
                ])

            print(tabulate(geo_results,
                         headers=['#', 'Event', 'Venue', 'City', 'Distance', 'Price'],
                         tablefmt='grid'))

    def experiment_autocomplete(self):
        """Auto-complete suggestions experiment."""
        self.print_header(
            "Auto-complete Suggestions",
            "Implement search-as-you-type functionality"
        )

        # Test different prefixes
        test_prefixes = ["taylor", "concert", "new", "basketball"]

        for prefix in test_prefixes:
            query = {
                "suggest": {
                    "event_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "title.suggest",
                            "size": 5,
                            "skip_duplicates": True
                        }
                    },
                    "artist_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "artist.suggest",
                            "size": 3,
                            "skip_duplicates": True
                        }
                    }
                }
            }

            self.print_query(f"Auto-complete for '{prefix}'", query)
            response = self.es.search(index="events", body=query)

            suggestions = []
            # Event suggestions
            for option in response.get("suggest", {}).get("event_suggest", [{}])[0].get("options", []):
                suggestions.append(["Event", option["text"], f"{option['_score']:.2f}"])

            # Artist suggestions
            for option in response.get("suggest", {}).get("artist_suggest", [{}])[0].get("options", []):
                suggestions.append(["Artist", option["text"], f"{option['_score']:.2f}"])

            if suggestions:
                print(tabulate(suggestions, headers=['Type', 'Suggestion', 'Score'], tablefmt='simple'))
            else:
                print("No suggestions found.")
            print()

    def experiment_fraud(self):
        """Fraud detection analytics experiment."""
        self.print_header(
            "Fraud Detection Analytics",
            "Analyze suspicious patterns and risk indicators"
        )

        # High-risk sessions
        query1 = {
            "query": {
                "range": {"risk_score": {"gte": 70}}
            },
            "sort": [{"risk_score": {"order": "desc"}}],
            "size": 5
        }

        self.print_query("High-Risk Sessions (Score >= 70)", query1)
        response1 = self.es.search(index="fraud_detection", body=query1)
        self.print_results(response1)

        print("\n" + "-"*60)

        # Risk indicators analysis
        query2 = {
            "query": {"match_all": {}},
            "size": 0,
            "aggs": {
                "risk_levels": {
                    "range": {
                        "field": "risk_score",
                        "ranges": [
                            {"key": "Low Risk (0-25)", "to": 25},
                            {"key": "Medium Risk (25-50)", "from": 25, "to": 50},
                            {"key": "High Risk (50-75)", "from": 50, "to": 75},
                            {"key": "Critical Risk (75+)", "from": 75}
                        ]
                    }
                },
                "flagged_sessions": {
                    "terms": {"field": "flagged"}
                },
                "avg_risk_score": {
                    "avg": {"field": "risk_score"}
                }
            }
        }

        self.print_query("Risk Distribution Analysis", query2)
        response2 = self.es.search(index="fraud_detection", body=query2)
        self.print_aggregations(response2)

    def experiment_analytics(self):
        """User behavior analytics experiment."""
        self.print_header(
            "User Behavior Analytics",
            "Analyze user patterns and search trends"
        )

        # Popular searches
        query1 = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "search_query"}},
                        {"range": {"timestamp": {"gte": "now-7d"}}}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "popular_searches": {
                    "terms": {"field": "search_query.keyword", "size": 10}
                },
                "search_trends": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "1d"
                    }
                },
                "conversion_rate": {
                    "avg": {"field": "conversion"}
                }
            }
        }

        self.print_query("Popular Searches (Last 7 Days)", query1)
        response1 = self.es.search(index="user_behavior", body=query1)
        self.print_aggregations(response1)

        print("\n" + "-"*60)

        # User action patterns
        query2 = {
            "query": {"match_all": {}},
            "size": 0,
            "aggs": {
                "action_types": {
                    "terms": {"field": "action_type", "size": 10}
                },
                "hourly_activity": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "1h"
                    }
                },
                "top_referrers": {
                    "terms": {"field": "referrer", "size": 5}
                }
            }
        }

        self.print_query("User Activity Patterns", query2)
        response2 = self.es.search(index="user_behavior", body=query2)
        self.print_aggregations(response2)

    def experiment_recommendations(self):
        """Event recommendation experiment."""
        self.print_header(
            "Event Recommendations",
            "Demonstrate personalized recommendations using user behavior"
        )

        # Get user preferences from behavior
        user_id = "user_001"

        # First, analyze user's past behavior
        behavior_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"range": {"timestamp": {"gte": "now-30d"}}}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "search_categories": {
                    "nested": {"path": "filters_applied"},
                    "aggs": {
                        "category_filters": {
                            "filter": {"term": {"filters_applied.filter_type": "category"}},
                            "aggs": {
                                "categories": {"terms": {"field": "filters_applied.filter_value", "size": 5}}
                            }
                        }
                    }
                }
            }
        }

        self.print_query(f"Analyze User {user_id} Preferences", behavior_query)
        behavior_response = self.es.search(index="user_behavior", body=behavior_query)

        print("👤 User Behavior Analysis:")
        self.print_aggregations(behavior_response)

        print("\n" + "-"*60)

        # Generate recommendations based on preferences
        # In a real system, this would use the behavior analysis results
        recommendation_query = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "should": [
                                {"terms": {"category": ["music", "theater"]}},  # User's preferred categories
                                {"range": {"popularity_score": {"gte": 70}}}
                            ],
                            "filter": [
                                {"range": {"date": {"gte": "now"}}},
                                {"term": {"availability.sold_out": False}}
                            ]
                        }
                    },
                    "functions": [
                        {
                            "field_value_factor": {
                                "field": "popularity_score",
                                "factor": 1.2,
                                "modifier": "sqrt"
                            }
                        },
                        {
                            "filter": {"range": {"price_range.min": {"lte": 150}}},
                            "weight": 1.5
                        }
                    ],
                    "score_mode": "multiply",
                    "boost_mode": "sum"
                }
            },
            "size": 5
        }

        self.print_query("Personalized Recommendations", recommendation_query)
        rec_response = self.es.search(index="events", body=recommendation_query)
        print("🎯 Recommended Events:")
        self.print_results(rec_response)

    def run_experiment(self, experiment_name):
        """Run a specific experiment."""
        experiments = {
            'search': self.experiment_search,
            'facets': self.experiment_facets,
            'geo': self.experiment_geo,
            'autocomplete': self.experiment_autocomplete,
            'fraud': self.experiment_fraud,
            'analytics': self.experiment_analytics,
            'recommendations': self.experiment_recommendations
        }

        if experiment_name in experiments:
            experiments[experiment_name]()
        else:
            print(f"❌ Unknown experiment: {experiment_name}")
            print(f"Available experiments: {list(experiments.keys())}")

def main():
    """Main experiment runner."""
    parser = argparse.ArgumentParser(description="Ticketmaster Elasticsearch Experiments")
    parser.add_argument("--experiment", "-e", required=True,
                       choices=["search", "facets", "geo", "autocomplete", "fraud", "analytics", "recommendations", "all"],
                       help="Experiment to run")

    args = parser.parse_args()

    try:
        # Install tabulate if not available
        import tabulate
    except ImportError:
        print("Installing required package: tabulate")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate", "--break-system-packages"])
        import tabulate

    experiments = TicketmasterExperiments()

    print("🚀 Ticketmaster Elasticsearch Experiments")
    print("=" * 50)

    if args.experiment == "all":
        experiment_order = ["search", "facets", "geo", "autocomplete", "fraud", "analytics", "recommendations"]
        for exp in experiment_order:
            experiments.run_experiment(exp)
            print("\nPress Enter to continue to next experiment...")
            input()
    else:
        experiments.run_experiment(args.experiment)

if __name__ == "__main__":
    main()