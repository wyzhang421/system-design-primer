# Ticketmaster Elasticsearch Setup Guide

This guide will walk you through setting up Elasticsearch with Docker and experimenting with the Ticketmaster system design.

## 🚀 Quick Start (TL;DR)

```bash
# 1. Start services
cd solutions/system_design/ticket_master
docker compose up -d

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Initialize and load data
python setup/setup_experiment.py
python setup/ingest_sample_data.py

# 4. Run experiments
python experiments.py --experiment search
```

## Prerequisites

- Docker Desktop installed and running
- Python 3.8+ installed
- Basic knowledge of command line

## Step 1: Start the Elasticsearch Cluster

Navigate to the ticket_master directory and start the services:

```bash
cd solutions/system_design/ticket_master
docker compose up -d
```

This will start:
- **Elasticsearch 8.11.0** on port 9200
- **Kibana 8.11.0** (web UI) on port 5601
- **Redis 7-alpine** on port 6379

## Step 2: Verify Services are Running

Check that all services are healthy:

```bash
# Check Elasticsearch
curl http://localhost:9200
curl http://localhost:9200/_cluster/health

# Check Kibana (wait 1-2 minutes for startup)
open http://localhost:5601

# Check Redis
docker exec ticketmaster-redis redis-cli ping
```

Expected Elasticsearch response:
```json
{
  "name" : "es01",
  "cluster_name" : "ticketmaster-cluster",
  "version" : {
    "number" : "8.11.0"
  }
}
```

## Step 3: Install Python Dependencies

**Recommended: Create a virtual environment first:**
```bash
cd solutions/system_design/ticket_master
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install dependencies with correct versions:**
```bash
pip install -r requirements.txt
```

**Or install manually:**
```bash
pip install elasticsearch==8.11.0 elasticsearch-dsl==8.11.0 redis==5.0.0
```

## Step 4: Create Indices and Mappings

Run the setup script to create all indices:

```bash
python setup/setup_experiment.py
```

This will:
- Create all 4 indices (events, user_behavior, fraud_detection, analytics)
- Set up proper mappings and settings
- Create index templates for time-based data
- Configure lifecycle policies

## Step 5: Ingest Sample Data

Load sample events, users, and behavior data:

```bash
python setup/ingest_sample_data.py
```

This creates:
- **50 sample events** (concerts, sports, theater)
- **100 sample users** with preferences
- **500 user behavior records** (searches, clicks, purchases)
- **20 fraud detection records** with various risk levels

## Step 6: Run Experiments

### Experiment 1: Basic Event Search

```bash
python experiments.py --experiment search
```

**What it tests:**
- Full-text search for "Taylor Swift"
- Location-based search (events near NYC)
- Price filtering ($0-200)
- Category filtering (music events)

### Experiment 2: Faceted Search

```bash
python experiments.py --experiment facets
```

**What it tests:**
- Aggregations for categories, price ranges, cities
- Search with multiple filters
- Facet counts and navigation

### Experiment 3: Geo-Location Search

```bash
python experiments.py --experiment geo
```

**What it tests:**
- Find events within 50 miles of coordinates
- Sort by distance
- Multiple city searches

### Experiment 4: Auto-complete

```bash
python experiments.py --experiment autocomplete
```

**What it tests:**
- Completion suggester for event names
- Artist name suggestions
- Context-aware suggestions

### Experiment 5: Fraud Detection Analytics

```bash
python experiments.py --experiment fraud
```

**What it tests:**
- High-risk user detection
- IP-based anomaly detection
- Behavioral pattern analysis
- Risk scoring algorithms

### Experiment 6: User Behavior Analytics

```bash
python experiments.py --experiment analytics
```

**What it tests:**
- Popular search terms
- Conversion rate analysis
- User activity patterns
- Time-based analytics

## Step 7: Interactive Exploration with Kibana

### 7.1 Access Kibana Web Interface

1. **Open Kibana in your browser**: http://localhost:5601
2. **First-time setup**: Kibana may take 30-60 seconds to load initially
3. **Welcome screen**: You'll see the Kibana home page with various options

### 7.2 Create Index Patterns (Data Views)

Index patterns tell Kibana which Elasticsearch indices to explore.

1. **Navigate to Index Management**:
   - Click **☰** (hamburger menu) in top-left
   - Go to **Management** → **Stack Management**
   - Under **Kibana**, click **Data Views** (or **Index Patterns** in older versions)

2. **Create Data Views** (click **Create data view** for each):

   **Events Data View**:
   - Name: `Events`
   - Index pattern: `events*`
   - Time field: `date` (main event date)
   - Click **Create data view**

   **User Behavior Data View**:
   - Name: `User Behavior`
   - Index pattern: `user_behavior*`
   - Time field: `timestamp`
   - Click **Create data view**

   **Fraud Detection Data View**:
   - Name: `Fraud Detection`
   - Index pattern: `fraud_detection*`
   - Time field: `timestamp`
   - Click **Create data view**

   **Analytics Data View**:
   - Name: `Analytics`
   - Index pattern: `analytics*`
   - Time field: `timestamp`
   - Click **Create data view**

### 7.3 Explore Data with Discover

**Discover** is Kibana's data exploration tool.

1. **Access Discover**:
   - Click **☰** → **Analytics** → **Discover**

2. **Select Data View**:
   - In the dropdown at top-left, select **Events**

3. **Set Correct Time Range**:
   - **Time picker**: Click clock icon (🕐) in top-right
   - **Important**: Sample data spans from Sep 2025 to Mar 2026
   - **Recommended settings**:
     - Select **"Last 2 years"** for broad coverage
     - Or set **Custom range**: Start `2025-09-01`, End `2026-06-01`
   - **Apply time range**

4. **Explore Event Data**:
   - **Search bar**: Try searches like:
     - `category:music`
     - `artist:"Maroon 5"`
     - `venue.city:"Seattle"`
     - `category:theater`
     - `price_range.min:[50 TO 200]`

5. **View Document Details**:
   - Click **>** arrow next to any document to expand
   - Click **View surrounding documents** to see context
   - Use **JSON** tab to see raw document structure

6. **Filter Data**:
   - Click **+ Add filter**
   - Example: Field: `category`, Operator: `is`, Value: `music`
   - Apply multiple filters for complex searches

### 💡 Troubleshooting: No Data in Discover

If you don't see data in Kibana Discover:

1. **Check Time Range**: Sample data is in the future (2025-2026)
   - Set time range to **"Last 2 years"** or custom range `2025-09-01` to `2026-06-01`

2. **Verify Time Field**: Make sure data view uses correct time field:
   - Events: Use `date` field (not `@timestamp`)
   - User Behavior: Use `timestamp` field

3. **Test in Dev Tools**: Verify data exists:
   ```json
   GET events/_search
   {
     "size": 1
   }
   ```

4. **Recreate Data View**: If issues persist, delete and recreate the data view with correct time field

### 7.4 Create Visualizations

1. **Access Visualize**:
   - Click **☰** → **Analytics** → **Visualize Library**
   - Click **Create visualization**

2. **Popular Visualization Types**:

   **Bar Chart - Events by Category**:
   - Choose **Vertical Bar**
   - Data view: **Events**
   - Y-axis: **Count**
   - X-axis: **Terms** → Field: `category.keyword`
   - Click **Update** to see chart

   **Pie Chart - Events by City**:
   - Choose **Pie**
   - Data view: **Events**
   - Slice by: **Terms** → Field: `venue.city.keyword`
   - Size by: **Count**

   **Line Chart - User Activity Over Time**:
   - Choose **Line**
   - Data view: **User Behavior**
   - Y-axis: **Count**
   - X-axis: **Date Histogram** → Field: `timestamp`

   **Heat Map - Fraud Risk by Time**:
   - Choose **Heat map**
   - Data view: **Fraud Detection**
   - Y-axis: **Terms** → Field: `risk_level.keyword`
   - X-axis: **Date Histogram** → Field: `timestamp`
   - Values: **Average** → Field: `risk_score`

3. **Save Visualizations**:
   - Click **Save** in top-right
   - Give descriptive names like "Events by Category"

### 7.5 Build Dashboards

1. **Create Dashboard**:
   - Click **☰** → **Analytics** → **Dashboard**
   - Click **Create dashboard**

2. **Add Visualizations**:
   - Click **Add from library**
   - Select the visualizations you created
   - Drag to resize and rearrange panels

3. **Dashboard Ideas**:
   - **Events Overview**: Events by category, city distribution, price ranges
   - **User Analytics**: Search activity, conversion rates, popular artists
   - **Fraud Monitoring**: Risk levels, suspicious IPs, flagged transactions

4. **Interactive Features**:
   - Click on chart segments to filter entire dashboard
   - Use time picker to analyze different time periods
   - Add text panels for context and explanations

### 7.6 Advanced Kibana Features

**Dev Tools (Query Console)**:
1. Click **☰** → **Management** → **Dev Tools**
2. Practice Elasticsearch queries directly:
   ```json
   GET events/_search
   {
     "query": {
       "match": {
         "artist": "Taylor Swift"
       }
     }
   }
   ```

**Saved Searches**:
1. In Discover, create useful searches
2. Save them with **Save** button
3. Reuse in visualizations and dashboards

**Time-based Analysis**:
- Use **@timestamp** field for time-series analysis
- Try different time intervals (hourly, daily, weekly)
- Look for patterns in user behavior and events

### 7.7 Kibana Navigation Tips

- **Breadcrumbs**: Use the breadcrumb trail at top to navigate back
- **Shortcuts**: Bookmark useful Kibana pages
- **Search Everything**: Use the search bar in Kibana for quick navigation
- **Help**: Click **?** icon for context-sensitive help

### Recommended Kibana Visualizations

1. **Event Distribution Map** - Geo map of event venues
2. **Search Volume Timeline** - User searches over time
3. **Fraud Risk Dashboard** - Risk levels and indicators
4. **Price Range Analysis** - Event pricing distribution
5. **Category Performance** - Popular event categories

## Step 8: Advanced Queries

### Search for High-Demand Events
```json
GET /events/_search
{
  "query": {
    "bool": {
      "must": [
        {"range": {"popularity_score": {"gte": 80}}}
      ],
      "filter": [
        {"term": {"availability.sold_out": false}}
      ]
    }
  },
  "sort": [
    {"popularity_score": {"order": "desc"}}
  ]
}
```

### Detect Suspicious Purchasing Patterns
```json
GET /fraud_detection/_search
{
  "query": {
    "range": {"risk_score": {"gte": 75}}
  },
  "aggs": {
    "risk_indicators": {
      "nested": {"path": "risk_indicators"},
      "aggs": {
        "top_indicators": {
          "terms": {"field": "risk_indicators.indicator.keyword"}
        }
      }
    }
  }
}
```

### Analyze User Search Behavior
```json
GET /user_behavior/_search
{
  "query": {
    "range": {"timestamp": {"gte": "now-7d"}}
  },
  "aggs": {
    "popular_searches": {
      "terms": {"field": "search_query.keyword", "size": 10}
    },
    "conversion_by_category": {
      "nested": {"path": "filters_applied"},
      "aggs": {
        "categories": {
          "filter": {"term": {"filters_applied.filter_type": "category"}},
          "aggs": {
            "category_conversions": {
              "terms": {"field": "filters_applied.filter_value"}
            }
          }
        }
      }
    }
  }
}
```

## Step 9: Performance Testing

Test search performance under load:

```bash
python load_test.py --queries 1000 --concurrent 10
```

This simulates:
- 1000 search queries
- 10 concurrent users
- Various query types (text, geo, faceted)
- Response time measurements

## Step 10: Cleanup

When you're done experimenting:

```bash
# Stop services
docker compose down

# Remove volumes (optional - deletes all data)
docker compose down -v

# Remove images (optional)
docker rmi $(docker images -q)
```

## Troubleshooting

### Common Issues

1. **Elasticsearch client compatibility errors** (`BadRequestError`, `media_type_header_exception`)
   - **Cause**: Version mismatch between Python client and Elasticsearch server
   - **Fix**: Ensure versions match - we use Elasticsearch 8.11.0
   ```bash
   pip install elasticsearch==8.11.0 elasticsearch-dsl==8.11.0
   docker compose down -v && docker compose up -d
   ```

2. **"Can't open file setup_experiment.py"**
   - **Cause**: File moved to `setup/` directory during reorganization
   - **Fix**: Use correct path: `python setup/setup_experiment.py`

3. **Elasticsearch won't start**
   - Check Docker has enough memory (4GB+ recommended)
   - Increase `vm.max_map_count`: `sudo sysctl -w vm.max_map_count=262144`

4. **Connection refused**
   - Wait 30-60 seconds for full startup
   - Check logs: `docker compose logs elasticsearch`

5. **Out of memory**
   - Reduce heap size in docker-compose.yml: `ES_JAVA_OPTS=-Xms512m -Xmx512m`

6. **Kibana not accessible**
   - Ensure Elasticsearch is healthy first
   - Check logs: `docker compose logs kibana`

7. **Docker Compose warnings about `version`**
   - **Cause**: Modern Docker Compose doesn't need version field
   - **Fix**: Already fixed in our docker-compose.yml

### Useful Commands

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f elasticsearch

# Access Elasticsearch container
docker exec -it ticketmaster-elasticsearch bash

# Reset all data
docker compose down -v && docker compose up -d
```

## Learning Objectives

By completing this setup and experiments, you'll learn:

1. **Elasticsearch Fundamentals**
   - Index creation and mapping design
   - Query DSL and search operations
   - Aggregations for analytics

2. **Real-world Application**
   - Full-text search implementation
   - Geo-location queries
   - Faceted search and navigation

3. **System Design Concepts**
   - Search architecture patterns
   - Performance optimization
   - Data modeling for search

4. **Fraud Detection**
   - Behavioral analysis with ES
   - Risk scoring algorithms
   - Real-time monitoring

5. **Analytics and Monitoring**
   - User behavior tracking
   - Business intelligence queries
   - Operational dashboards

## Next Steps

- Experiment with different query types
- Create custom visualizations in Kibana
- Optimize mappings for your use cases
- Scale up with multiple ES nodes
- Integrate with your own applications

Happy experimenting with Elasticsearch! 🚀