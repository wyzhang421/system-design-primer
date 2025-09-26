"""
Elasticsearch mappings and index configurations for Ticketmaster system.
"""

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
import json

class TicketmasterElasticsearchMappings:
    """
    Manages Elasticsearch mappings and index configurations for Ticketmaster.
    """

    def __init__(self, es_client: Elasticsearch):
        self.es = es_client

    def get_events_mapping(self):
        """
        Returns the mapping configuration for the events index.
        Optimized for full-text search, geo queries, and faceted search.
        """
        return {
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "event_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "snowball"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "event_id": {
                        "type": "keyword",
                        "index": True
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "event_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {
                                "type": "completion",
                                "analyzer": "simple",
                                "preserve_separators": True,
                                "preserve_position_increments": True,
                                "max_input_length": 50
                            }
                        }
                    },
                    "artist": {
                        "type": "text",
                        "analyzer": "event_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {
                                "type": "completion",
                                "analyzer": "simple"
                            }
                        }
                    },
                    "venue": {
                        "properties": {
                            "name": {
                                "type": "text",
                                "analyzer": "event_analyzer",
                                "fields": {"keyword": {"type": "keyword"}}
                            },
                            "location": {
                                "type": "geo_point"
                            },
                            "city": {"type": "keyword"},
                            "state": {"type": "keyword"},
                            "country": {"type": "keyword"},
                            "capacity": {"type": "integer"},
                            "address": {"type": "text"}
                        }
                    },
                    "category": {
                        "type": "keyword",
                        "fields": {
                            "text": {"type": "text", "analyzer": "event_analyzer"}
                        }
                    },
                    "subcategory": {"type": "keyword"},
                    "date": {"type": "date"},
                    "end_date": {"type": "date"},
                    "price_range": {
                        "properties": {
                            "min": {"type": "float"},
                            "max": {"type": "float"},
                            "currency": {"type": "keyword"}
                        }
                    },
                    "availability": {
                        "properties": {
                            "total_seats": {"type": "integer"},
                            "available_seats": {"type": "integer"},
                            "sold_out": {"type": "boolean"},
                            "last_updated": {"type": "date"}
                        }
                    },
                    "popularity_score": {
                        "type": "float",
                        "index": True
                    },
                    "ratings": {
                        "properties": {
                            "average": {"type": "float"},
                            "count": {"type": "integer"}
                        }
                    },
                    "tags": {"type": "keyword"},
                    "description": {
                        "type": "text",
                        "analyzer": "event_analyzer"
                    },
                    "image_url": {"type": "keyword"},
                    "external_urls": {
                        "properties": {
                            "official": {"type": "keyword"},
                            "social": {"type": "keyword"}
                        }
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "indexed_at": {"type": "date"}
                }
            }
        }

    def get_user_behavior_mapping(self):
        """
        Returns mapping for user behavior tracking and recommendations.
        """
        return {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "action_type": {
                        "type": "keyword",
                        "fields": {"text": {"type": "text"}}
                    },
                    "event_id": {"type": "keyword"},
                    "search_query": {"type": "text"},
                    "filters_applied": {
                        "type": "nested",
                        "properties": {
                            "filter_type": {"type": "keyword"},
                            "filter_value": {"type": "keyword"}
                        }
                    },
                    "user_agent": {"type": "text"},
                    "ip_address": {"type": "ip"},
                    "location": {"type": "geo_point"},
                    "referrer": {"type": "keyword"},
                    "conversion": {"type": "boolean"},
                    "purchase_amount": {"type": "float"}
                }
            }
        }

    def get_fraud_detection_mapping(self):
        """
        Returns mapping for fraud detection and security analytics.
        """
        return {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "session_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "ip_address": {"type": "ip"},
                    "user_agent": {"type": "text"},
                    "device_fingerprint": {"type": "keyword"},
                    "actions": {
                        "type": "nested",
                        "properties": {
                            "action_type": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "event_id": {"type": "keyword"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "float"},
                            "speed": {"type": "float"}  # actions per minute
                        }
                    },
                    "risk_indicators": {
                        "properties": {
                            "multiple_events": {"type": "boolean"},
                            "high_quantity": {"type": "boolean"},
                            "rapid_fire": {"type": "boolean"},
                            "suspicious_ip": {"type": "boolean"},
                            "bot_like_behavior": {"type": "boolean"}
                        }
                    },
                    "risk_score": {"type": "float"},
                    "flagged": {"type": "boolean"},
                    "reviewed": {"type": "boolean"},
                    "timestamp": {"type": "date"}
                }
            }
        }

    def get_analytics_mapping(self):
        """
        Returns mapping for business analytics and reporting.
        """
        return {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "index.refresh_interval": "30s"  # Optimize for bulk writes
            },
            "mappings": {
                "properties": {
                    "event_id": {"type": "keyword"},
                    "date": {"type": "date"},
                    "metrics": {
                        "properties": {
                            "page_views": {"type": "long"},
                            "searches": {"type": "long"},
                            "clicks": {"type": "long"},
                            "purchases": {"type": "long"},
                            "revenue": {"type": "double"},
                            "conversion_rate": {"type": "float"}
                        }
                    },
                    "dimensions": {
                        "properties": {
                            "category": {"type": "keyword"},
                            "artist": {"type": "keyword"},
                            "venue": {"type": "keyword"},
                            "city": {"type": "keyword"},
                            "state": {"type": "keyword"},
                            "price_tier": {"type": "keyword"},
                            "device_type": {"type": "keyword"},
                            "traffic_source": {"type": "keyword"}
                        }
                    },
                    "timestamp": {"type": "date"}
                }
            }
        }

    def create_indices(self):
        """
        Creates all necessary indices for the Ticketmaster system.
        """
        indices_config = {
            "events": self.get_events_mapping(),
            "user_behavior": self.get_user_behavior_mapping(),
            "fraud_detection": self.get_fraud_detection_mapping(),
            "analytics": self.get_analytics_mapping()
        }

        created_indices = []

        for index_name, mapping in indices_config.items():
            try:
                if not self.es.indices.exists(index=index_name):
                    self.es.indices.create(
                        index=index_name,
                        body=mapping
                    )
                    created_indices.append(index_name)
                    print(f"Created index: {index_name}")
                else:
                    print(f"Index {index_name} already exists")
            except RequestError as e:
                print(f"Error creating index {index_name}: {e}")

        return created_indices

    def create_index_templates(self):
        """
        Creates index templates for time-based indices.
        """
        templates = {
            "user_behavior_template": {
                "index_patterns": ["user_behavior_*"],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "index.lifecycle.name": "user_behavior_policy",
                        "index.lifecycle.rollover_alias": "user_behavior"
                    },
                    "mappings": self.get_user_behavior_mapping()["mappings"]
                }
            },
            "analytics_template": {
                "index_patterns": ["analytics_*"],
                "template": {
                    "settings": {
                        "number_of_shards": 2,
                        "number_of_replicas": 1,
                        "index.lifecycle.name": "analytics_policy",
                        "index.lifecycle.rollover_alias": "analytics"
                    },
                    "mappings": self.get_analytics_mapping()["mappings"]
                }
            }
        }

        for template_name, template_config in templates.items():
            try:
                self.es.indices.put_template(
                    name=template_name,
                    body=template_config
                )
                print(f"Created template: {template_name}")
            except RequestError as e:
                print(f"Error creating template {template_name}: {e}")


def create_lifecycle_policies(es_client: Elasticsearch):
    """
    Creates Index Lifecycle Management policies for time-based indices.
    """
    policies = {
        "user_behavior_policy": {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_size": "5gb",
                                "max_age": "1d"
                            }
                        }
                    },
                    "warm": {
                        "min_age": "1d",
                        "actions": {
                            "allocate": {
                                "number_of_replicas": 0
                            }
                        }
                    },
                    "cold": {
                        "min_age": "7d",
                        "actions": {
                            "allocate": {
                                "number_of_replicas": 0
                            }
                        }
                    },
                    "delete": {
                        "min_age": "90d"
                    }
                }
            }
        },
        "analytics_policy": {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_size": "10gb",
                                "max_age": "1d"
                            }
                        }
                    },
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "allocate": {
                                "number_of_replicas": 0
                            },
                            "forcemerge": {
                                "max_num_segments": 1
                            }
                        }
                    },
                    "cold": {
                        "min_age": "30d"
                    },
                    "delete": {
                        "min_age": "365d"
                    }
                }
            }
        }
    }

    for policy_name, policy_config in policies.items():
        try:
            es_client.ilm.put_lifecycle(
                policy=policy_name,
                body=policy_config
            )
            print(f"Created lifecycle policy: {policy_name}")
        except RequestError as e:
            print(f"Error creating policy {policy_name}: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize Elasticsearch client
    es = Elasticsearch(
        hosts=['http://localhost:9200'],
        request_timeout=30,
        max_retries=10,
        retry_on_timeout=True
    )

    # Create mappings manager
    mappings_manager = TicketmasterElasticsearchMappings(es)

    # Create lifecycle policies
    create_lifecycle_policies(es)

    # Create index templates
    mappings_manager.create_index_templates()

    # Create indices
    created = mappings_manager.create_indices()
    print(f"Created {len(created)} indices: {created}")