"""
Generate Ticketmaster system architecture diagram using Python.
Creates a visual representation of the high-level system design.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_ticketmaster_architecture_diagram():
    """
    Create a comprehensive architecture diagram for the Ticketmaster system.
    Shows all major components including Elasticsearch integration.
    """
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # Color scheme
    colors = {
        'client': '#4A90E2',
        'api': '#7ED321',
        'service': '#F5A623',
        'elasticsearch': '#BD10E0',
        'database': '#B8E986',
        'cache': '#50E3C2',
        'external': '#D0021B'
    }

    # Title
    ax.text(8, 11.5, 'Ticketmaster System Architecture',
            fontsize=20, fontweight='bold', ha='center')
    ax.text(8, 11, 'High-Scale Event Ticketing with Elasticsearch',
            fontsize=14, ha='center', style='italic')

    # Client Layer
    client_y = 9.5
    clients = [
        ('Mobile App', 1.5),
        ('Web Browser', 4),
        ('Partner APIs', 6.5),
        ('Admin Dashboard', 9)
    ]

    for name, x in clients:
        box = FancyBboxPatch((x-0.7, client_y-0.3), 1.4, 0.6,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['client'],
                           edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x, client_y, name, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')

    # Load Balancer
    lb_y = 8
    lb_box = FancyBboxPatch((7, lb_y-0.3), 2, 0.6,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['api'],
                          edgecolor='black', linewidth=1)
    ax.add_patch(lb_box)
    ax.text(8, lb_y, 'Load Balancer\n(AWS ALB)', ha='center', va='center',
            fontsize=10, fontweight='bold')

    # API Gateway
    gateway_y = 6.8
    gateway_box = FancyBboxPatch((6.5, gateway_y-0.4), 3, 0.8,
                               boxstyle="round,pad=0.1",
                               facecolor=colors['api'],
                               edgecolor='black', linewidth=2)
    ax.add_patch(gateway_box)
    ax.text(8, gateway_y, 'API Gateway\nAuthentication • Rate Limiting\nRequest Routing',
            ha='center', va='center', fontsize=9, fontweight='bold')

    # Microservices Layer
    services_y = 5
    services = [
        ('Search\nService', 1.5, 'Elasticsearch\nQueries'),
        ('Event\nService', 3.5, 'Event\nManagement'),
        ('User\nService', 5.5, 'User Profile\n& Auth'),
        ('Payment\nService', 7.5, 'Transaction\nProcessing'),
        ('Notification\nService', 9.5, 'Email & SMS\nAlerts'),
        ('Fraud\nDetection', 11.5, 'Real-time\nAnalytics'),
        ('Recommendation\nEngine', 13.5, 'ML-based\nSuggestions')
    ]

    for name, x, desc in services:
        box = FancyBboxPatch((x-0.6, services_y-0.4), 1.2, 0.8,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['service'],
                           edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x, services_y+0.1, name, ha='center', va='center',
                fontsize=8, fontweight='bold')
        ax.text(x, services_y-0.2, desc, ha='center', va='center',
                fontsize=7, style='italic')

    # Elasticsearch Cluster (Prominent placement)
    es_y = 3.2
    es_box = FancyBboxPatch((1, es_y-0.6), 4, 1.2,
                          boxstyle="round,pad=0.15",
                          facecolor=colors['elasticsearch'],
                          edgecolor='black', linewidth=3)
    ax.add_patch(es_box)
    ax.text(3, es_y+0.2, 'Elasticsearch Cluster', ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    ax.text(3, es_y-0.2, '• Event Search Index\n• User Behavior Index\n• Analytics Index\n• Fraud Detection Index',
            ha='center', va='center', fontsize=8, color='white')

    # Cache Layer
    cache_y = 3.2
    cache_box = FancyBboxPatch((5.5, cache_y-0.4), 1.5, 0.8,
                             boxstyle="round,pad=0.1",
                             facecolor=colors['cache'],
                             edgecolor='black', linewidth=1)
    ax.add_patch(cache_box)
    ax.text(6.25, cache_y, 'Redis Cache\nSearch Results\nSession Data',
            ha='center', va='center', fontsize=8, fontweight='bold')

    # Message Queue
    mq_y = 3.2
    mq_box = FancyBboxPatch((7.5, mq_y-0.4), 1.5, 0.8,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['service'],
                          edgecolor='black', linewidth=1)
    ax.add_patch(mq_box)
    ax.text(8.25, mq_y, 'Kafka Queue\nReal-time Events\nInventory Updates',
            ha='center', va='center', fontsize=8, fontweight='bold')

    # Database Layer
    db_y = 1.5
    databases = [
        ('PostgreSQL\n(Events DB)', 2, 'Event Details\nVenue Info\nSchedules'),
        ('PostgreSQL\n(Users DB)', 4, 'User Profiles\nPreferences\nHistory'),
        ('PostgreSQL\n(Orders DB)', 6, 'Transactions\nTicket Sales\nPayments'),
        ('MongoDB\n(Analytics)', 8, 'User Behavior\nClickstream\nMetrics'),
        ('PostgreSQL\n(Inventory)', 10, 'Seat Maps\nAvailability\nPricing')
    ]

    for name, x, desc in databases:
        box = FancyBboxPatch((x-0.7, db_y-0.4), 1.4, 0.8,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['database'],
                           edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x, db_y+0.15, name, ha='center', va='center',
                fontsize=8, fontweight='bold')
        ax.text(x, db_y-0.2, desc, ha='center', va='center',
                fontsize=7, style='italic')

    # External Services
    external_y = 1.5
    externals = [
        ('Payment\nGateway', 12, 'Stripe/PayPal'),
        ('Email/SMS\nService', 13.5, 'SendGrid\nTwilio'),
        ('CDN', 15, 'CloudFlare\nStatic Assets')
    ]

    for name, x, desc in externals:
        box = FancyBboxPatch((x-0.6, external_y-0.3), 1.2, 0.6,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['external'],
                           edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x, external_y+0.1, name, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
        ax.text(x, external_y-0.15, desc, ha='center', va='center',
                fontsize=7, color='white')

    # Connection arrows
    connections = [
        # Client to Load Balancer
        ((2.2, client_y-0.3), (7, lb_y+0.3)),
        ((4.7, client_y-0.3), (7.3, lb_y+0.3)),
        ((7.2, client_y-0.3), (7.7, lb_y+0.3)),
        ((9.7, client_y-0.3), (8.3, lb_y+0.3)),

        # Load Balancer to API Gateway
        ((8, lb_y-0.3), (8, gateway_y+0.4)),

        # API Gateway to Services
        ((6.8, gateway_y-0.4), (1.5, services_y+0.4)),
        ((7.2, gateway_y-0.4), (3.5, services_y+0.4)),
        ((7.6, gateway_y-0.4), (5.5, services_y+0.4)),
        ((8, gateway_y-0.4), (7.5, services_y+0.4)),
        ((8.4, gateway_y-0.4), (9.5, services_y+0.4)),
        ((8.8, gateway_y-0.4), (11.5, services_y+0.4)),
        ((9.2, gateway_y-0.4), (13.5, services_y+0.4)),

        # Services to Elasticsearch (highlighted)
        ((1.5, services_y-0.4), (2, es_y+0.6)),
        ((11.5, services_y-0.4), (4, es_y+0.6)),
        ((13.5, services_y-0.4), (4.5, es_y+0.6)),

        # Services to Cache
        ((5.5, services_y-0.4), (6.25, cache_y+0.4)),

        # Services to Message Queue
        ((7.5, services_y-0.4), (8.25, mq_y+0.4)),

        # Services to Databases
        ((3.5, services_y-0.4), (2, db_y+0.4)),
        ((5.5, services_y-0.4), (4, db_y+0.4)),
        ((7.5, services_y-0.4), (6, db_y+0.4)),
        ((9.5, services_y-0.4), (8, db_y+0.4)),
        ((11.5, services_y-0.4), (10, db_y+0.4)),

        # Services to External
        ((7.5, services_y-0.4), (12, external_y+0.3)),
        ((9.5, services_y-0.4), (13.5, external_y+0.3)),
    ]

    for start, end in connections:
        if 'es_y' in str(end):  # Highlight ES connections
            arrow = patches.FancyArrowPatch(start, end,
                                          arrowstyle='->', mutation_scale=15,
                                          color=colors['elasticsearch'], linewidth=2)
        else:
            arrow = patches.FancyArrowPatch(start, end,
                                          arrowstyle='->', mutation_scale=12,
                                          color='gray', linewidth=1)
        ax.add_patch(arrow)

    # Add data flow indicators
    ax.text(0.5, 8.5, 'User Traffic\n↓', ha='center', va='center',
            fontsize=10, fontweight='bold', color=colors['client'])

    ax.text(14.5, 4, 'Real-time\nUpdates\n→', ha='center', va='center',
            fontsize=9, fontweight='bold', color=colors['elasticsearch'])

    # Legend
    legend_x = 12.5
    legend_y = 7
    ax.text(legend_x, legend_y, 'Key Components', fontsize=12, fontweight='bold')

    legend_items = [
        ('Client Applications', colors['client']),
        ('API & Load Balancing', colors['api']),
        ('Microservices', colors['service']),
        ('Elasticsearch Cluster', colors['elasticsearch']),
        ('Caching Layer', colors['cache']),
        ('Databases', colors['database']),
        ('External Services', colors['external'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = legend_y - 0.4 - (i * 0.3)
        legend_box = FancyBboxPatch((legend_x-0.1, y_pos-0.08), 0.2, 0.16,
                                  boxstyle="round,pad=0.02",
                                  facecolor=color, edgecolor='black')
        ax.add_patch(legend_box)
        ax.text(legend_x + 0.3, y_pos, label, ha='left', va='center', fontsize=9)

    # Elasticsearch callout
    ax.text(3, 0.5, 'Elasticsearch Powers:', ha='center', va='center',
            fontsize=11, fontweight='bold', color=colors['elasticsearch'])
    ax.text(3, 0.1, '• Event Search & Filtering\n• Real-time Analytics\n• Fraud Detection\n• Recommendations',
            ha='center', va='center', fontsize=9, color=colors['elasticsearch'])

    plt.tight_layout()
    return fig

def save_architecture_diagram():
    """Save the architecture diagram as both PNG and SVG."""
    fig = create_ticketmaster_architecture_diagram()

    # Save as high-resolution PNG
    fig.savefig('/Users/wyzhang/workplace/system-design-primer/solutions/system_design/ticket_master/ticketmaster_architecture.png',
                dpi=300, bbox_inches='tight', facecolor='white')

    print("Architecture diagram saved:")
    print("- ticketmaster_architecture.png (high-res)")

    plt.close(fig)

if __name__ == "__main__":
    save_architecture_diagram()