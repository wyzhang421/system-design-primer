"""
Elasticsearch-powered fraud detection system for Ticketmaster.
Detects bot activity, scalping attempts, and suspicious purchasing patterns.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

@dataclass
class RiskIndicator:
    """Risk indicator with score and description."""
    indicator: str
    score: float
    description: str
    evidence: Dict[str, Any]

@dataclass
class FraudAssessment:
    """Complete fraud assessment result."""
    session_id: str
    user_id: str
    total_risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    indicators: List[RiskIndicator]
    recommended_action: str
    timestamp: datetime

class TicketmasterFraudDetection:
    """
    Real-time fraud detection using Elasticsearch analytics.
    Identifies suspicious patterns and bot behavior.
    """

    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.fraud_index = "fraud_detection"
        self.user_behavior_index = "user_behavior"

        # Risk scoring thresholds
        self.risk_thresholds = {
            "LOW": 25,
            "MEDIUM": 50,
            "HIGH": 75,
            "CRITICAL": 90
        }

    def assess_session_risk(self, session_id: str, user_id: str = None) -> FraudAssessment:
        """
        Assess fraud risk for a user session in real-time.

        Args:
            session_id: Current session identifier
            user_id: User identifier (if authenticated)

        Returns:
            FraudAssessment with risk score and recommended actions
        """
        indicators = []

        # Collect session data
        session_data = self._get_session_data(session_id)
        if not session_data:
            return self._create_low_risk_assessment(session_id, user_id)

        # Run fraud detection algorithms
        indicators.extend(self._detect_rapid_fire_behavior(session_data))
        indicators.extend(self._detect_high_quantity_purchases(session_data))
        indicators.extend(self._detect_multiple_event_targeting(session_data))
        indicators.extend(self._detect_bot_patterns(session_data))
        indicators.extend(self._detect_ip_anomalies(session_data))

        if user_id:
            indicators.extend(self._detect_user_anomalies(user_id, session_data))

        # Calculate total risk score
        total_score = sum(indicator.score for indicator in indicators)
        risk_level = self._calculate_risk_level(total_score)
        recommended_action = self._get_recommended_action(risk_level, indicators)

        assessment = FraudAssessment(
            session_id=session_id,
            user_id=user_id,
            total_risk_score=total_score,
            risk_level=risk_level,
            indicators=indicators,
            recommended_action=recommended_action,
            timestamp=datetime.utcnow()
        )

        # Store assessment for tracking
        self._store_fraud_assessment(assessment)

        return assessment

    def detect_scalping_networks(self, event_id: str, time_window_minutes: int = 60) -> Dict:
        """
        Detect coordinated scalping attacks on specific events.

        Args:
            event_id: Event being targeted
            time_window_minutes: Time window to analyze

        Returns:
            Dict containing detected scalping networks and evidence
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event_id": event_id}},
                        {"range": {
                            "timestamp": {
                                "gte": f"now-{time_window_minutes}m"
                            }
                        }}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "ip_analysis": {
                    "terms": {"field": "ip_address", "size": 100},
                    "aggs": {
                        "unique_users": {"cardinality": {"field": "user_id"}},
                        "total_quantity": {"sum": {"field": "actions.quantity"}},
                        "user_agents": {"terms": {"field": "user_agent.keyword", "size": 5}},
                        "purchase_timeline": {
                            "date_histogram": {
                                "field": "timestamp",
                                "calendar_interval": "1m"
                            }
                        }
                    }
                },
                "user_agent_analysis": {
                    "terms": {"field": "user_agent.keyword", "size": 50},
                    "aggs": {
                        "unique_ips": {"cardinality": {"field": "ip_address"}},
                        "total_purchases": {"sum": {"field": "actions.quantity"}}
                    }
                }
            }
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=query)
            return self._analyze_scalping_patterns(response, event_id)

        except Exception as e:
            logger.error(f"Scalping detection error: {e}")
            return {"networks_detected": [], "risk_level": "UNKNOWN"}

    def get_real_time_threat_dashboard(self) -> Dict:
        """
        Get real-time fraud detection dashboard data.

        Returns:
            Dict containing current threat levels and statistics
        """
        query = {
            "query": {
                "range": {"timestamp": {"gte": "now-1h"}}
            },
            "size": 0,
            "aggs": {
                "risk_levels": {
                    "terms": {"field": "risk_level.keyword"}
                },
                "flagged_sessions": {
                    "filter": {"term": {"flagged": True}},
                    "aggs": {
                        "by_risk_type": {
                            "nested": {"path": "risk_indicators"},
                            "aggs": {
                                "indicator_types": {
                                    "terms": {"field": "risk_indicators.indicator.keyword"}
                                }
                            }
                        }
                    }
                },
                "blocked_ips": {
                    "cardinality": {"field": "ip_address"}
                },
                "threat_timeline": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "5m"
                    },
                    "aggs": {
                        "high_risk": {
                            "filter": {
                                "terms": {"risk_level.keyword": ["HIGH", "CRITICAL"]}
                            }
                        }
                    }
                }
            }
        }

        try:
            response = self.es.search(index=self.fraud_index, body=query)
            return self._format_threat_dashboard(response)

        except Exception as e:
            logger.error(f"Threat dashboard error: {e}")
            return {}

    def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Retrieve comprehensive session data from Elasticsearch."""
        query = {
            "query": {"term": {"session_id": session_id}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": 100
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=query)
            if response["hits"]["total"]["value"] > 0:
                return {
                    "actions": [hit["_source"] for hit in response["hits"]["hits"]],
                    "session_start": response["hits"]["hits"][-1]["_source"]["timestamp"],
                    "latest_action": response["hits"]["hits"][0]["_source"]["timestamp"]
                }
            return None

        except Exception as e:
            logger.error(f"Session data retrieval error: {e}")
            return None

    def _detect_rapid_fire_behavior(self, session_data: Dict) -> List[RiskIndicator]:
        """Detect unusually fast clicking/purchasing patterns."""
        indicators = []
        actions = session_data["actions"]

        if len(actions) < 2:
            return indicators

        # Calculate time between actions
        time_gaps = []
        for i in range(1, len(actions)):
            prev_time = datetime.fromisoformat(actions[i-1]["timestamp"].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(actions[i]["timestamp"].replace('Z', '+00:00'))
            gap = (curr_time - prev_time).total_seconds()
            time_gaps.append(gap)

        # Detect rapid-fire patterns
        rapid_actions = [gap for gap in time_gaps if gap < 2.0]  # Less than 2 seconds
        if len(rapid_actions) > 5:
            indicators.append(RiskIndicator(
                indicator="rapid_fire_clicks",
                score=30.0,
                description=f"Detected {len(rapid_actions)} rapid-fire actions (< 2s intervals)",
                evidence={
                    "rapid_action_count": len(rapid_actions),
                    "avg_gap": sum(time_gaps) / len(time_gaps),
                    "min_gap": min(time_gaps)
                }
            ))

        # Detect superhuman speed (< 0.5 seconds consistently)
        superhuman_actions = [gap for gap in time_gaps if gap < 0.5]
        if len(superhuman_actions) > 3:
            indicators.append(RiskIndicator(
                indicator="superhuman_speed",
                score=50.0,
                description=f"Detected {len(superhuman_actions)} superhuman-speed actions",
                evidence={
                    "superhuman_count": len(superhuman_actions),
                    "fastest_action": min(time_gaps)
                }
            ))

        return indicators

    def _detect_high_quantity_purchases(self, session_data: Dict) -> List[RiskIndicator]:
        """Detect attempts to purchase unusually large quantities."""
        indicators = []
        actions = session_data["actions"]

        # Check for high quantity in single transaction
        for action in actions:
            if action.get("action_type") == "add_to_cart":
                quantity = action.get("quantity", 1)
                if quantity > 10:  # More than 10 tickets
                    indicators.append(RiskIndicator(
                        indicator="high_quantity_single",
                        score=25.0 + min(quantity * 2, 50),  # Scale with quantity
                        description=f"Attempted to purchase {quantity} tickets in single transaction",
                        evidence={
                            "quantity": quantity,
                            "event_id": action.get("event_id"),
                            "timestamp": action["timestamp"]
                        }
                    ))

        # Check for cumulative high quantity across session
        total_quantity = sum(
            action.get("quantity", 1)
            for action in actions
            if action.get("action_type") == "add_to_cart"
        )

        if total_quantity > 20:
            indicators.append(RiskIndicator(
                indicator="high_quantity_cumulative",
                score=20.0 + min(total_quantity, 60),
                description=f"Attempted to purchase {total_quantity} total tickets in session",
                evidence={
                    "total_quantity": total_quantity,
                    "unique_events": len(set(
                        action.get("event_id") for action in actions
                        if action.get("event_id")
                    ))
                }
            ))

        return indicators

    def _detect_multiple_event_targeting(self, session_data: Dict) -> List[RiskIndicator]:
        """Detect targeting of multiple high-demand events."""
        indicators = []
        actions = session_data["actions"]

        # Get unique events targeted
        targeted_events = set(
            action.get("event_id")
            for action in actions
            if action.get("event_id") and action.get("action_type") in ["search", "view", "add_to_cart"]
        )

        if len(targeted_events) > 5:
            indicators.append(RiskIndicator(
                indicator="multiple_event_targeting",
                score=15.0 + min(len(targeted_events) * 3, 45),
                description=f"Targeted {len(targeted_events)} different events in single session",
                evidence={
                    "event_count": len(targeted_events),
                    "events": list(targeted_events)[:10]  # Limit for storage
                }
            ))

        return indicators

    def _detect_bot_patterns(self, session_data: Dict) -> List[RiskIndicator]:
        """Detect automated bot behavior patterns."""
        indicators = []
        actions = session_data["actions"]

        if not actions:
            return indicators

        # Check for consistent timing patterns (bot-like)
        time_gaps = []
        for i in range(1, len(actions)):
            prev_time = datetime.fromisoformat(actions[i-1]["timestamp"].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(actions[i]["timestamp"].replace('Z', '+00:00'))
            gap = (curr_time - prev_time).total_seconds()
            time_gaps.append(gap)

        if len(time_gaps) > 5:
            # Check for suspiciously consistent timing
            avg_gap = sum(time_gaps) / len(time_gaps)
            variance = sum((gap - avg_gap) ** 2 for gap in time_gaps) / len(time_gaps)

            if variance < 0.5 and avg_gap < 5.0:  # Very consistent, fast timing
                indicators.append(RiskIndicator(
                    indicator="consistent_timing_pattern",
                    score=35.0,
                    description="Detected bot-like consistent timing pattern",
                    evidence={
                        "avg_gap": avg_gap,
                        "variance": variance,
                        "action_count": len(actions)
                    }
                ))

        # Check for missing typical user behaviors
        action_types = set(action.get("action_type") for action in actions)
        human_behaviors = {"scroll", "hover", "back_button", "page_refresh"}
        missing_behaviors = human_behaviors - action_types

        if len(missing_behaviors) >= 3 and len(actions) > 10:
            indicators.append(RiskIndicator(
                indicator="missing_human_behaviors",
                score=25.0,
                description="Missing typical human browsing behaviors",
                evidence={
                    "missing_behaviors": list(missing_behaviors),
                    "present_behaviors": list(action_types)
                }
            ))

        return indicators

    def _detect_ip_anomalies(self, session_data: Dict) -> List[RiskIndicator]:
        """Detect IP-based anomalies and suspicious networks."""
        indicators = []
        actions = session_data["actions"]

        if not actions:
            return indicators

        # Get IP address from first action
        ip_address = actions[0].get("ip_address")
        if not ip_address:
            return indicators

        # Check for known suspicious IP ranges or VPN/Proxy usage
        # This would typically involve external IP reputation services
        # For demo purposes, we'll check against common patterns

        # Check for multiple sessions from same IP recently
        recent_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"ip_address": ip_address}},
                        {"range": {"timestamp": {"gte": "now-1h"}}}
                    ]
                }
            },
            "aggs": {
                "unique_sessions": {"cardinality": {"field": "session_id"}},
                "unique_users": {"cardinality": {"field": "user_id"}}
            },
            "size": 0
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=recent_query)
            aggs = response.get("aggregations", {})

            unique_sessions = aggs.get("unique_sessions", {}).get("value", 0)
            unique_users = aggs.get("unique_users", {}).get("value", 0)

            if unique_sessions > 10:  # More than 10 sessions from same IP in 1 hour
                indicators.append(RiskIndicator(
                    indicator="high_ip_activity",
                    score=20.0 + min(unique_sessions * 2, 40),
                    description=f"High activity from IP: {unique_sessions} sessions in 1 hour",
                    evidence={
                        "ip_address": ip_address,
                        "session_count": unique_sessions,
                        "user_count": unique_users
                    }
                ))

        except Exception as e:
            logger.error(f"IP anomaly detection error: {e}")

        return indicators

    def _detect_user_anomalies(self, user_id: str, session_data: Dict) -> List[RiskIndicator]:
        """Detect anomalies in user behavior patterns."""
        indicators = []

        # Get user's historical behavior
        historical_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {"range": {"timestamp": {"gte": "now-30d", "lt": "now-1d"}}}
                    ]
                }
            },
            "aggs": {
                "avg_session_length": {"avg": {"script": "doc['session_end'].value - doc['session_start'].value"}},
                "typical_quantity": {"avg": {"field": "actions.quantity"}},
                "common_categories": {"terms": {"field": "category", "size": 5}}
            },
            "size": 0
        }

        try:
            response = self.es.search(index=self.user_behavior_index, body=historical_query)
            # Compare current session with historical patterns
            # Implementation would analyze deviation from normal behavior

        except Exception as e:
            logger.error(f"User anomaly detection error: {e}")

        return indicators

    def _analyze_scalping_patterns(self, response: Dict, event_id: str) -> Dict:
        """Analyze aggregation results to identify scalping networks."""
        networks = []
        aggs = response.get("aggregations", {})

        # Analyze IP-based patterns
        for ip_bucket in aggs.get("ip_analysis", {}).get("buckets", []):
            ip = ip_bucket["key"]
            unique_users = ip_bucket["unique_users"]["value"]
            total_quantity = ip_bucket["total_quantity"]["value"]

            # Suspicious if many users from same IP purchasing high quantities
            if unique_users > 3 and total_quantity > 20:
                networks.append({
                    "type": "ip_based",
                    "identifier": ip,
                    "evidence": {
                        "unique_users": unique_users,
                        "total_quantity": total_quantity,
                        "user_agents": [b["key"] for b in ip_bucket["user_agents"]["buckets"]]
                    },
                    "risk_score": min(unique_users * total_quantity / 10, 100)
                })

        # Analyze User-Agent patterns
        for ua_bucket in aggs.get("user_agent_analysis", {}).get("buckets", []):
            user_agent = ua_bucket["key"]
            unique_ips = ua_bucket["unique_ips"]["value"]
            total_purchases = ua_bucket["total_purchases"]["value"]

            # Suspicious if same User-Agent from many IPs
            if unique_ips > 5 and total_purchases > 15:
                networks.append({
                    "type": "user_agent_based",
                    "identifier": user_agent,
                    "evidence": {
                        "unique_ips": unique_ips,
                        "total_purchases": total_purchases
                    },
                    "risk_score": min(unique_ips * total_purchases / 5, 100)
                })

        # Determine overall risk level
        max_risk = max([n["risk_score"] for n in networks], default=0)
        risk_level = "LOW"
        if max_risk > 75:
            risk_level = "CRITICAL"
        elif max_risk > 50:
            risk_level = "HIGH"
        elif max_risk > 25:
            risk_level = "MEDIUM"

        return {
            "event_id": event_id,
            "networks_detected": networks,
            "risk_level": risk_level,
            "total_networks": len(networks),
            "max_network_risk": max_risk
        }

    def _calculate_risk_level(self, total_score: float) -> str:
        """Calculate risk level based on total score."""
        if total_score >= self.risk_thresholds["CRITICAL"]:
            return "CRITICAL"
        elif total_score >= self.risk_thresholds["HIGH"]:
            return "HIGH"
        elif total_score >= self.risk_thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommended_action(self, risk_level: str, indicators: List[RiskIndicator]) -> str:
        """Get recommended action based on risk level and indicators."""
        if risk_level == "CRITICAL":
            return "BLOCK_IMMEDIATELY"
        elif risk_level == "HIGH":
            return "REQUIRE_VERIFICATION"
        elif risk_level == "MEDIUM":
            return "ADD_FRICTION"
        else:
            return "MONITOR"

    def _create_low_risk_assessment(self, session_id: str, user_id: str) -> FraudAssessment:
        """Create a low-risk assessment for sessions with no data."""
        return FraudAssessment(
            session_id=session_id,
            user_id=user_id,
            total_risk_score=0.0,
            risk_level="LOW",
            indicators=[],
            recommended_action="ALLOW",
            timestamp=datetime.utcnow()
        )

    def _store_fraud_assessment(self, assessment: FraudAssessment):
        """Store fraud assessment in Elasticsearch for tracking and analytics."""
        doc = {
            "session_id": assessment.session_id,
            "user_id": assessment.user_id,
            "risk_score": assessment.total_risk_score,
            "risk_level": assessment.risk_level,
            "risk_indicators": [
                {
                    "indicator": ind.indicator,
                    "score": ind.score,
                    "description": ind.description,
                    "evidence": ind.evidence
                }
                for ind in assessment.indicators
            ],
            "recommended_action": assessment.recommended_action,
            "flagged": assessment.risk_level in ["HIGH", "CRITICAL"],
            "timestamp": assessment.timestamp.isoformat()
        }

        try:
            self.es.index(
                index=self.fraud_index,
                body=doc,
                refresh="false"
            )
        except Exception as e:
            logger.error(f"Error storing fraud assessment: {e}")

    def _format_threat_dashboard(self, response: Dict) -> Dict:
        """Format threat dashboard response."""
        aggs = response.get("aggregations", {})

        return {
            "current_threat_level": "MEDIUM",  # Would be calculated from recent data
            "active_threats": {
                "total_flagged": aggs.get("flagged_sessions", {}).get("doc_count", 0),
                "by_type": [
                    {
                        "type": bucket["key"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in aggs.get("flagged_sessions", {})
                    .get("by_risk_type", {})
                    .get("indicator_types", {})
                    .get("buckets", [])
                ]
            },
            "blocked_ips": aggs.get("blocked_ips", {}).get("value", 0),
            "threat_timeline": [
                {
                    "timestamp": bucket["key_as_string"],
                    "total_events": bucket["doc_count"],
                    "high_risk_events": bucket["high_risk"]["doc_count"]
                }
                for bucket in aggs.get("threat_timeline", {}).get("buckets", [])
            ]
        }


# Example usage
if __name__ == "__main__":
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    fraud_detector = TicketmasterFraudDetection(es)

    # Assess session risk
    assessment = fraud_detector.assess_session_risk("session_123", "user_456")
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Risk Score: {assessment.total_risk_score}")
    print(f"Recommended Action: {assessment.recommended_action}")

    for indicator in assessment.indicators:
        print(f"- {indicator.indicator}: {indicator.score} ({indicator.description})")