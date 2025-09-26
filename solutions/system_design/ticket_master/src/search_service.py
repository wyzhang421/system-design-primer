"""
Elasticsearch-powered search service for Ticketmaster system.
Handles event search, recommendations, and real-time analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError
import json
import redis
import hashlib
import logging

logger = logging.getLogger(__name__)

class TicketmasterSearchService:
    """
    Main search service for Ticketmaster using Elasticsearch.
    Provides event search, filtering, recommendations, and analytics.
    """

    def __init__(self, es_client: Elasticsearch, redis_client: redis.Redis = None):
        self.es = es_client
        self.redis = redis_client
        self.events_index = "events"
        self.user_behavior_index = "user_behavior"
        self.cache_ttl = 300  # 5 minutes

    def search_events(self,
                     query: str = None,
                     filters: Dict = None,
                     location: Tuple[float, float] = None,
                     distance: str = "50mi",
                     page: int = 0,
                     size: int = 20,
                     sort_by: str = "relevance",
                     user_id: str = None) -> Dict:
        """
        Comprehensive event search with full-text, filters, and geo-location.

        Args:
            query: Search text (artist, event name, venue)
            filters: Dict containing category, date_range, price_range, etc.
            location: Tuple of (lat, lon) for geo search
            distance: Distance radius for geo search
            page: Page number for pagination
            size: Results per page
            sort_by: Sort criteria (relevance, date, price, popularity)
            user_id: User ID for behavior tracking

        Returns:
            Dict containing search results, facets, and metadata
        """
        # Check cache first
        cache_key = self._generate_cache_key("search", query, filters, location,
                                            distance, page, size, sort_by)
        if self.redis:
            cached_result = self.redis.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

        # Build Elasticsearch query
        es_query = self._build_search_query(query, filters, location, distance, sort_by)

        try:
            response = self.es.search(
                index=self.events_index,
                body=es_query,
                from_=page * size,
                size=size
            )

            # Process and format results
            results = self._format_search_results(response)

            # Track user behavior
            if user_id:
                self._track_search_behavior(user_id, query, filters, len(results['events']))

            # Cache results
            if self.redis:
                self.redis.setex(cache_key, self.cache_ttl, json.dumps(results))

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"events": [], "facets": {}, "total": 0, "error": str(e)}

    def autocomplete_suggestions(self, prefix: str, context: Dict = None) -> List[Dict]:
        """
        Provides autocomplete suggestions for search queries.

        Args:
            prefix: Partial text user has typed
            context: Additional context like user location, preferences

        Returns:
            List of suggestion dictionaries with text and metadata
        """
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
                        "size": 5,
                        "skip_duplicates": True
                    }
                }
            }
        }

        try:
            response = self.es.search(index=self.events_index, body=query)
            suggestions = []

            # Process event suggestions
            for option in response.get("suggest", {}).get("event_suggest", [{}])[0].get("options", []):
                suggestions.append({
                    "text": option["text"],
                    "type": "event",
                    "score": option["_score"]
                })

            # Process artist suggestions
            for option in response.get("suggest", {}).get("artist_suggest", [{}])[0].get("options", []):
                suggestions.append({
                    "text": option["text"],
                    "type": "artist",
                    "score": option["_score"]
                })

            # Sort by score and remove duplicates
            unique_suggestions = {}
            for suggestion in suggestions:
                key = suggestion["text"].lower()
                if key not in unique_suggestions or suggestion["score"] > unique_suggestions[key]["score"]:
                    unique_suggestions[key] = suggestion

            return sorted(unique_suggestions.values(), key=lambda x: x["score"], reverse=True)[:8]

        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return []

    def get_event_recommendations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get personalized event recommendations based on user behavior.

        Args:
            user_id: User identifier
            limit: Number of recommendations to return

        Returns:
            List of recommended events with relevance scores
        """
        try:
            # Get user preferences from behavior data
            user_preferences = self._analyze_user_preferences(user_id)

            if not user_preferences:
                # Fallback to popular events
                return self._get_popular_events(limit)

            # Build recommendation query
            query = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "should": [
                                    # Category preferences
                                    {
                                        "terms": {
                                            "category": user_preferences.get("categories", []),
                                            "boost": 2.0
                                        }
                                    },
                                    # Artist preferences
                                    {
                                        "terms": {
                                            "artist.keyword": user_preferences.get("artists", []),
                                            "boost": 3.0
                                        }
                                    },
                                    # Location preferences
                                    {
                                        "terms": {
                                            "venue.city": user_preferences.get("cities", []),
                                            "boost": 1.5
                                        }
                                    }
                                ],
                                "filter": [
                                    {"range": {"date": {"gte": "now"}}},
                                    {"term": {"availability.sold_out": False}}
                                ]
                            }
                        },
                        "functions": [
                            # Boost popular events
                            {
                                "field_value_factor": {
                                    "field": "popularity_score",
                                    "factor": 1.2,
                                    "modifier": "sqrt"
                                }
                            },
                            # Boost events in user's price range
                            {
                                "filter": {
                                    "range": {
                                        "price_range.min": {
                                            "lte": user_preferences.get("max_price", 300)
                                        }
                                    }
                                },
                                "weight": 1.3
                            }
                        ],
                        "score_mode": "multiply",
                        "boost_mode": "sum"
                    }
                },
                "size": limit
            }

            response = self.es.search(index=self.events_index, body=query)
            return [self._format_event(hit) for hit in response["hits"]["hits"]]

        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return self._get_popular_events(limit)

    def update_event_inventory(self, event_id: str, available_seats: int) -> bool:
        """
        Update event inventory in real-time.

        Args:
            event_id: Event identifier
            available_seats: Current number of available seats

        Returns:
            Boolean indicating success
        """
        try:
            update_body = {
                "doc": {
                    "availability.available_seats": available_seats,
                    "availability.sold_out": available_seats == 0,
                    "availability.last_updated": datetime.utcnow().isoformat()
                }
            }

            self.es.update(
                index=self.events_index,
                id=event_id,
                body=update_body,
                refresh="wait_for"  # Ensure immediate availability for search
            )

            # Invalidate related cache entries
            if self.redis:
                cache_pattern = f"search:*{event_id}*"
                for key in self.redis.scan_iter(match=cache_pattern):
                    self.redis.delete(key)

            return True

        except Exception as e:
            logger.error(f"Inventory update error for event {event_id}: {e}")
            return False

    def get_search_analytics(self, date_range: Dict = None) -> Dict:
        """
        Get search analytics and insights.

        Args:
            date_range: Dict with 'start' and 'end' dates

        Returns:
            Dict containing analytics data
        """
        if not date_range:
            date_range = {
                "start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }

        query = {
            "query": {
                "range": {
                    "timestamp": {
                        "gte": date_range["start"],
                        "lte": date_range["end"]
                    }
                }
            },
            "size": 0,
            "aggs": {
                "total_searches": {
                    "value_count": {"field": "search_query.keyword"}
                },
                "popular_queries": {
                    "terms": {"field": "search_query.keyword", "size": 20}
                },
                "searches_by_hour": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "hour"
                    }
                },
                "conversion_rate": {
                    "avg": {"field": "conversion"}
                },
                "popular_categories": {
                    "nested": {"path": "filters_applied"},
                    "aggs": {
                        "category_filters": {
                            "filter": {"term": {"filters_applied.filter_type": "category"}},
                            "aggs": {
                                "categories": {
                                    "terms": {"field": "filters_applied.filter_value", "size": 10}
                                }
                            }
                        }
                    }
                }
            }
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=query)
            return self._format_analytics_response(response)

        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {}

    def _build_search_query(self, query: str, filters: Dict, location: Tuple,
                           distance: str, sort_by: str) -> Dict:
        """Build comprehensive Elasticsearch query based on parameters."""
        es_query = {
            "query": {"bool": {"must": [], "filter": []}},
            "aggs": self._get_search_aggregations()
        }

        # Full-text search
        if query:
            es_query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "artist^2",
                        "venue.name^1.5",
                        "description^1",
                        "category^1.5"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            es_query["query"]["bool"]["must"].append({"match_all": {}})

        # Apply filters
        if filters:
            if "category" in filters:
                es_query["query"]["bool"]["filter"].append({
                    "terms": {"category": filters["category"]}
                })

            if "date_range" in filters:
                date_filter = {"range": {"date": {}}}
                if filters["date_range"].get("start"):
                    date_filter["range"]["date"]["gte"] = filters["date_range"]["start"]
                if filters["date_range"].get("end"):
                    date_filter["range"]["date"]["lte"] = filters["date_range"]["end"]
                es_query["query"]["bool"]["filter"].append(date_filter)

            if "price_range" in filters:
                price_filter = {"range": {"price_range.min": {}}}
                if filters["price_range"].get("min"):
                    price_filter["range"]["price_range.min"]["gte"] = filters["price_range"]["min"]
                if filters["price_range"].get("max"):
                    price_filter["range"]["price_range.min"]["lte"] = filters["price_range"]["max"]
                es_query["query"]["bool"]["filter"].append(price_filter)

            if filters.get("available_only", True):
                es_query["query"]["bool"]["filter"].append({
                    "term": {"availability.sold_out": False}
                })

        # Geo-location search
        if location:
            es_query["query"]["bool"]["filter"].append({
                "geo_distance": {
                    "distance": distance,
                    "venue.location": {"lat": location[0], "lon": location[1]}
                }
            })

        # Sorting
        es_query["sort"] = self._get_sort_criteria(sort_by, location)

        return es_query

    def _get_search_aggregations(self) -> Dict:
        """Define faceted search aggregations."""
        return {
            "categories": {
                "terms": {"field": "category", "size": 20}
            },
            "price_ranges": {
                "range": {
                    "field": "price_range.min",
                    "ranges": [
                        {"key": "under_50", "to": 50},
                        {"key": "50_to_100", "from": 50, "to": 100},
                        {"key": "100_to_200", "from": 100, "to": 200},
                        {"key": "200_to_500", "from": 200, "to": 500},
                        {"key": "over_500", "from": 500}
                    ]
                }
            },
            "cities": {
                "terms": {"field": "venue.city", "size": 15}
            },
            "dates": {
                "date_range": {
                    "field": "date",
                    "ranges": [
                        {"key": "today", "from": "now/d", "to": "now/d+1d"},
                        {"key": "this_week", "from": "now/w", "to": "now/w+7d"},
                        {"key": "this_month", "from": "now/M", "to": "now/M+1M"},
                        {"key": "next_3_months", "from": "now", "to": "now+3M"}
                    ]
                }
            },
            "availability": {
                "terms": {"field": "availability.sold_out"}
            }
        }

    def _get_sort_criteria(self, sort_by: str, location: Tuple) -> List[Dict]:
        """Define sorting criteria based on sort_by parameter."""
        if sort_by == "date":
            return [{"date": {"order": "asc"}}, {"_score": {"order": "desc"}}]
        elif sort_by == "price":
            return [{"price_range.min": {"order": "asc"}}, {"_score": {"order": "desc"}}]
        elif sort_by == "popularity":
            return [{"popularity_score": {"order": "desc"}}, {"_score": {"order": "desc"}}]
        elif sort_by == "distance" and location:
            return [{
                "_geo_distance": {
                    "venue.location": {"lat": location[0], "lon": location[1]},
                    "order": "asc",
                    "unit": "mi"
                }
            }]
        else:  # relevance (default)
            return [{"_score": {"order": "desc"}}, {"popularity_score": {"order": "desc"}}]

    def _format_search_results(self, response: Dict) -> Dict:
        """Format Elasticsearch response for API consumption."""
        return {
            "events": [self._format_event(hit) for hit in response["hits"]["hits"]],
            "facets": self._format_facets(response.get("aggregations", {})),
            "total": response["hits"]["total"]["value"],
            "max_score": response["hits"]["max_score"],
            "took": response["took"]
        }

    def _format_event(self, hit: Dict) -> Dict:
        """Format individual event from Elasticsearch hit."""
        source = hit["_source"]
        return {
            "event_id": source["event_id"],
            "title": source["title"],
            "artist": source["artist"],
            "venue": source["venue"],
            "category": source["category"],
            "date": source["date"],
            "price_range": source["price_range"],
            "availability": source["availability"],
            "popularity_score": source.get("popularity_score", 0),
            "image_url": source.get("image_url"),
            "score": hit["_score"]
        }

    def _format_facets(self, aggregations: Dict) -> Dict:
        """Format aggregations as facets for frontend consumption."""
        facets = {}

        for agg_name, agg_data in aggregations.items():
            if "buckets" in agg_data:
                facets[agg_name] = [
                    {"key": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in agg_data["buckets"]
                ]

        return facets

    def _analyze_user_preferences(self, user_id: str) -> Dict:
        """Analyze user behavior to extract preferences."""
        query = {
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
                "categories": {"terms": {"field": "filters_applied.filter_value", "size": 5}},
                "avg_price": {"avg": {"field": "purchase_amount"}},
                "locations": {"terms": {"field": "location", "size": 3}}
            }
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=query)
            aggs = response.get("aggregations", {})

            return {
                "categories": [b["key"] for b in aggs.get("categories", {}).get("buckets", [])],
                "max_price": aggs.get("avg_price", {}).get("value", 200),
                "cities": [b["key"] for b in aggs.get("locations", {}).get("buckets", [])]
            }
        except:
            return {}

    def _get_popular_events(self, limit: int) -> List[Dict]:
        """Get popular events as fallback recommendations."""
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"date": {"gte": "now"}}},
                        {"term": {"availability.sold_out": False}}
                    ]
                }
            },
            "sort": [{"popularity_score": {"order": "desc"}}],
            "size": limit
        }

        try:
            response = self.es.search(index=self.events_index, body=query)
            return [self._format_event(hit) for hit in response["hits"]["hits"]]
        except:
            return []

    def _track_search_behavior(self, user_id: str, query: str, filters: Dict, result_count: int):
        """Track user search behavior for analytics and recommendations."""
        behavior_doc = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": "search",
            "search_query": query,
            "filters_applied": [
                {"filter_type": k, "filter_value": v}
                for k, v in (filters or {}).items()
            ],
            "result_count": result_count,
            "conversion": False  # Will be updated if user purchases
        }

        try:
            self.es.index(
                index=self.user_behavior_index,
                body=behavior_doc,
                refresh="false"  # Async for performance
            )
        except Exception as e:
            logger.error(f"Behavior tracking error: {e}")

    def _generate_cache_key(self, *args) -> str:
        """Generate cache key for search results."""
        key_string = "|".join(str(arg) for arg in args if arg is not None)
        return f"search:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _format_analytics_response(self, response: Dict) -> Dict:
        """Format analytics response for reporting."""
        aggs = response.get("aggregations", {})
        return {
            "total_searches": aggs.get("total_searches", {}).get("value", 0),
            "popular_queries": [
                {"query": b["key"], "count": b["doc_count"]}
                for b in aggs.get("popular_queries", {}).get("buckets", [])
            ],
            "conversion_rate": aggs.get("conversion_rate", {}).get("value", 0),
            "searches_by_hour": [
                {"timestamp": b["key_as_string"], "count": b["doc_count"]}
                for b in aggs.get("searches_by_hour", {}).get("buckets", [])
            ]
        }


# Example usage
if __name__ == "__main__":
    # Initialize services
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    redis_client = redis.Redis(host='localhost', port=6379, db=0)

    search_service = TicketmasterSearchService(es, redis_client)

    # Example search
    results = search_service.search_events(
        query="Taylor Swift",
        filters={
            "category": ["music"],
            "price_range": {"max": 200},
            "date_range": {"start": "2024-01-01"}
        },
        location=(40.7128, -74.0060),  # NYC coordinates
        distance="50mi",
        sort_by="date"
    )

    print(f"Found {results['total']} events")
    for event in results['events'][:3]:
        print(f"- {event['title']} by {event['artist']} on {event['date']}")