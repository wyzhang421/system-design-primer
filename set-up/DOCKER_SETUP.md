# Elasticsearch & Kibana Docker Setup

## Quick Start
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down
```

## Access URLs
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

## Useful Commands

### Container Management
```bash
# Check running containers
docker ps

# View logs
docker-compose logs elasticsearch
docker-compose logs kibana

# Restart services
docker-compose restart

# Stop and remove containers + data
docker-compose down -v
```

### Test Elasticsearch
```bash
# Check cluster health
curl http://localhost:9200/_cluster/health

# Add sample document
curl -X POST "localhost:9200/books/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "year": 1925,
  "team": "orca"
}'

# Search documents
curl "localhost:9200/books/_search?pretty"


{
  "took" : 2,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "skipped" : 0,
    "failed" : 0
  },
  "hits" : {
    "total" : {
      "value" : 1,
      "relation" : "eq"
    },
    "max_score" : 1.0,
    "hits" : [
      {
        "_index" : "books",
        "_id" : "1",
        "_score" : 1.0,
        "_source" : {
          "title" : "The Great Gatsby",
          "author" : "F. Scott Fitzgerald",
          "year" : 1925,
          "team" : "orca"
        }
      }
    ]
  }
}
```

### Kibana Setup
1. Go to http://localhost:5601
2. Navigate to Stack Management > Index Patterns
3. Create index pattern (e.g., "books*")
4. Go to Discover to explore your data

## Configuration Notes
- Security disabled for development
- Single-node setup
- Data persisted in Docker volume `elasticsearch-data`
- Memory limit set to 512MB for each service