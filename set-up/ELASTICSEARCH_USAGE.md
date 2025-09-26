# Elasticsearch Usage Guide

## Basic Operations

### Check Cluster Health
```bash
curl http://localhost:9200/_cluster/health
```

### Create/Index a Document
```bash
curl -X POST "localhost:9200/books/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "year": 1925,
  "team": "orca"
}'
```

## Search Operations

### 1. Search All Documents
```bash
curl "localhost:9200/books/_search?pretty"
```

### 2. Simple Field Search
```bash
curl "localhost:9200/books/_search?q=team:orca&pretty"
```

### 3. Match Query (JSON Body)
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "team": "orca"
    }
  }
}'
```

### 4. Exact Term Match
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "team.keyword": "orca"
    }
  }
}'
```

### 5. Multiple Conditions (Bool Query)
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"team": "orca"}},
        {"range": {"year": {"gte": 1900}}}
      ]
    }
  }
}'
```

## Fuzzy Search

### 1. Fuzzy Query (Handle Typos)
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "title": {
        "value": "Gatsby",
        "fuzziness": "AUTO"
      }
    }
  }
}'
```

### 2. Match Query with Fuzziness
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": {
        "query": "Gret Gatby",
        "fuzziness": "AUTO"
      }
    }
  }
}'
```

### 3. Multi-field Fuzzy Search
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "Gatby Fitzgerald",
      "fields": ["title", "author"],
      "fuzziness": "AUTO"
    }
  }
}'
```

### 4. Wildcard Search
```bash
curl -X GET "localhost:9200/books/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "wildcard": {
      "title": "*Gats*"
    }
  }
}'
```

## Understanding Search Results

### Response Structure
```json
{
  "took": 2,                    // Query execution time (ms)
  "timed_out": false,           // Whether query timed out
  "_shards": {                  // Shard information
    "total": 1,                 // Total shards searched
    "successful": 1,            // Successful shards
    "failed": 0                 // Failed shards
  },
  "hits": {                     // Search results
    "total": {"value": 1},      // Number of matching documents
    "max_score": 1.0,           // Highest relevance score
    "hits": [                   // Array of matching documents
      {
        "_index": "books",       // Index name
        "_id": "1",             // Document ID
        "_score": 1.0,          // Relevance score
        "_source": {            // Actual document content
          "title": "The Great Gatsby",
          "author": "F. Scott Fitzgerald",
          "year": 1925,
          "team": "orca"
        }
      }
    ]
  }
}
```

## Fuzziness Levels
- `"AUTO"` - Elasticsearch decides based on term length (recommended)
- `0` - Exact match only
- `1` - Allow 1 character difference (insertion, deletion, substitution)
- `2` - Allow 2 character differences

## Query Parameters
- `?pretty` - Format JSON response for readability
- `?q=field:value` - Simple query string search
- `?size=10` - Limit number of results
- `?from=0` - Pagination offset

## Best Practices
- Use `match` query for full-text search
- Use `term` query for exact matches
- Use `bool` query to combine multiple conditions
- Use `fuzzy` or `fuzziness` for handling typos
- Always use `?pretty` when testing for better readability