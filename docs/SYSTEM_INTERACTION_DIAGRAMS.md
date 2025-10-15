# 🔄 System Interaction Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "External Data Sources"
        CG[CoinGecko API]
        RSS[RSS Feeds<br/>26 Sources]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Control Plane Node"
            CP[Control Plane<br/>API Server, etcd, scheduler]
        end
        
        subgraph "Data Collection Node"
            ECP[Enhanced Crypto Prices<br/>Service]
            CNC[Crypto News Collector<br/>Service]
            SC[Sentiment Collector<br/>Service]
            MU[Materialized Updater<br/>Service]
            RD[Redis Cache]
            CM[Cache Manager<br/>Service]
            DCHM[Data Collection<br/>Health Monitor]
        end
        
        subgraph "Analytics Infrastructure Node"
            P[Prometheus]
            G[Grafana]
            AM[Alertmanager]
            PM[Performance Monitor<br/>Service]
            CT[Cost Tracker<br/>Service]
            RM[Resource Monitor<br/>Service]
        end
        
        subgraph "ML Trading Engine Node"
            ML[ML Services<br/>Future]
        end
    end
    
    subgraph "External Storage"
        MySQL[(MySQL Database<br/>Windows Host)]
    end
    
    subgraph "External Access"
        UI[Web UI<br/>Port Forwards]
    end
    
    %% Data Flow Connections
    CG --> ECP
    RSS --> CNC
    ECP --> MySQL
    ECP --> RD
    CNC --> MySQL
    CNC --> RD
    SC --> MySQL
    SC --> RD
    MU --> MySQL
    
    %% Monitoring Connections
    ECP --> P
    CNC --> P
    SC --> P
    MU --> P
    DCHM --> P
    PM --> P
    CT --> P
    CM --> P
    RM --> P
    
    P --> G
    P --> AM
    
    %% Cache Management
    CM --> RD
    
    %% Health Monitoring
    DCHM --> ECP
    DCHM --> CNC
    DCHM --> SC
    DCHM --> MU
    
    %% Performance Monitoring
    PM --> MySQL
    PM --> RD
    PM --> CP
    
    %% Cost Tracking
    CT --> CP
    
    %% Resource Monitoring
    RM --> CP
    
    %% External Access
    G --> UI
    P --> UI
    PM --> UI
    CT --> UI
    CM --> UI
    
    %% Styling
    classDef dataCollection fill:#e1f5fe
    classDef monitoring fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class ECP,CNC,SC,MU,RD,CM,DCHM dataCollection
    class P,G,AM,PM,CT,RM monitoring
    class MySQL storage
    class CG,RSS,UI external
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant CG as CoinGecko API
    participant ECP as Enhanced Crypto Prices
    participant RD as Redis Cache
    participant MySQL as MySQL Database
    participant MU as Materialized Updater
    participant P as Prometheus
    participant G as Grafana
    
    Note over CG, G: Price Data Collection Flow
    
    loop Every 5 minutes
        ECP->>CG: GET /api/v3/simple/price
        CG-->>ECP: Price data (92 cryptocurrencies)
        ECP->>RD: Cache price data (TTL: 5min)
        ECP->>MySQL: INSERT price_data_real
        ECP->>P: Export metrics
        MU->>MySQL: UPDATE ml_features_materialized
        MU->>P: Export metrics
    end
    
    Note over CG, G: Monitoring Flow
    
    loop Every 30 seconds
        P->>ECP: Scrape /metrics
        P->>MU: Scrape /metrics
        P->>G: Provide metrics data
        G->>G: Update dashboards
    end
```

## News Collection Flow

```mermaid
sequenceDiagram
    participant RSS as RSS Sources
    participant CNC as Crypto News Collector
    participant RD as Redis Cache
    participant MySQL as MySQL Database
    participant SC as Sentiment Collector
    participant P as Prometheus
    
    Note over RSS, P: News Collection & Processing Flow
    
    loop Every 15 minutes
        CNC->>RSS: Fetch RSS feeds (26 sources)
        RSS-->>CNC: News articles
        CNC->>CNC: Deduplicate articles
        CNC->>RD: Cache news data (TTL: 15min)
        CNC->>MySQL: INSERT crypto_news
        CNC->>P: Export metrics
        
        Note over SC: Sentiment Analysis
        SC->>MySQL: SELECT new articles
        SC->>SC: Analyze sentiment
        SC->>MySQL: UPDATE sentiment scores
        SC->>P: Export metrics
    end
```

## Monitoring & Health Check Flow

```mermaid
sequenceDiagram
    participant DCHM as Health Monitor
    participant ECP as Enhanced Crypto Prices
    participant CNC as Crypto News Collector
    participant SC as Sentiment Collector
    participant MySQL as MySQL Database
    participant RD as Redis Cache
    participant P as Prometheus
    participant G as Grafana
    
    Note over DCHM, G: Continuous Health Monitoring
    
    loop Every 60 seconds
        DCHM->>ECP: Health check
        DCHM->>CNC: Health check
        DCHM->>SC: Health check
        DCHM->>MySQL: Connection test
        DCHM->>RD: Connection test
        DCHM->>DCHM: Calculate health score
        DCHM->>P: Export health metrics
        
        P->>G: Provide metrics
        G->>G: Update health dashboard
    end
```

## Autoscaling Flow

```mermaid
sequenceDiagram
    participant MS as Metrics Server
    participant HPA as Horizontal Pod Autoscaler
    participant K8S as Kubernetes API
    participant ECP as Enhanced Crypto Prices
    participant CNC as Crypto News Collector
    participant SC as Sentiment Collector
    participant P as Prometheus
    
    Note over MS, P: Automatic Scaling Based on Load
    
    loop Every 15 seconds
        MS->>ECP: Collect CPU/Memory metrics
        MS->>CNC: Collect CPU/Memory metrics
        MS->>SC: Collect CPU/Memory metrics
        MS->>HPA: Provide metrics
        
        alt CPU > 70% OR Memory > 80%
            HPA->>K8S: Scale up deployment
            K8S->>ECP: Create new pod
            K8S->>CNC: Create new pod
            K8S->>SC: Create new pod
        else CPU < 30% AND Memory < 50%
            HPA->>K8S: Scale down deployment
            K8S->>ECP: Remove pod
            K8S->>CNC: Remove pod
            K8S->>SC: Remove pod
        end
        
        HPA->>P: Export scaling metrics
    end
```

## Cache Management Flow

```mermaid
sequenceDiagram
    participant CM as Cache Manager
    participant RD as Redis Cache
    participant ECP as Enhanced Crypto Prices
    participant CNC as Crypto News Collector
    participant SC as Sentiment Collector
    participant P as Prometheus
    
    Note over CM, P: Intelligent Cache Management
    
    loop Every 60 seconds
        CM->>RD: Check cache status
        RD-->>CM: Memory usage, hit rates, evictions
        
        CM->>CM: Apply cache policies
        Note over CM: Set TTLs, manage evictions
        
        CM->>ECP: Cache price data
        CM->>CNC: Cache news data
        CM->>SC: Cache sentiment data
        
        CM->>P: Export cache metrics
    end
```

## Cost Optimization Flow

```mermaid
sequenceDiagram
    participant CT as Cost Tracker
    participant K8S as Kubernetes API
    participant PM as Performance Monitor
    participant P as Prometheus
    participant G as Grafana
    
    Note over CT, G: Real-time Cost Tracking & Optimization
    
    loop Every 5 minutes
        CT->>K8S: Get resource usage
        K8S-->>CT: CPU, Memory, Storage usage
        
        CT->>CT: Calculate costs
        Note over CT: CPU: $0.16, Memory: $0.17<br/>Storage: $0.12, Network: $0.02
        
        CT->>CT: Calculate optimization score
        Note over CT: Score: 100/100 (Perfect)
        
        CT->>P: Export cost metrics
        P->>G: Provide cost data
        G->>G: Update cost dashboard
    end
```

## Service Discovery & Communication

```mermaid
graph LR
    subgraph "Kubernetes DNS"
        DNS[Service Discovery<br/>*.svc.cluster.local]
    end
    
    subgraph "Data Collection Services"
        ECP[enhanced-crypto-prices<br/>.svc.cluster.local:8000]
        CNC[crypto-news-collector<br/>.svc.cluster.local:8000]
        SC[sentiment-collector<br/>.svc.cluster.local:8000]
        MU[materialized-updater<br/>.svc.cluster.local:8000]
    end
    
    subgraph "Monitoring Services"
        P[prometheus<br/>.svc.cluster.local:9090]
        G[grafana<br/>.svc.cluster.local:3000]
        PM[performance-monitor<br/>.svc.cluster.local:8000]
        CT[cost-tracker<br/>.svc.cluster.local:8000]
    end
    
    subgraph "Storage Services"
        RD[redis-data-collection<br/>.svc.cluster.local:6379]
        MySQL[MySQL<br/>host.docker.internal:3306]
    end
    
    DNS --> ECP
    DNS --> CNC
    DNS --> SC
    DNS --> MU
    DNS --> P
    DNS --> G
    DNS --> PM
    DNS --> CT
    DNS --> RD
    
    ECP --> RD
    ECP --> MySQL
    CNC --> RD
    CNC --> MySQL
    SC --> RD
    SC --> MySQL
    MU --> MySQL
    
    P --> ECP
    P --> CNC
    P --> SC
    P --> MU
    P --> PM
    P --> CT
    
    G --> P
```

## Error Handling & Resilience

```mermaid
graph TB
    subgraph "Resilience Patterns"
        CB[Circuit Breaker<br/>5 failures → Open<br/>60s timeout]
        RL[Retry Logic<br/>3 retries<br/>Exponential backoff]
        TO[Timeouts<br/>DB: 5s, API: 30s]
        CP[Connection Pooling<br/>Reuse connections]
        RL2[Rate Limiting<br/>Respect API quotas]
    end
    
    subgraph "Error Handling"
        EH[Error Handling<br/>Try-catch blocks]
        GD[Graceful Degradation<br/>Fallback mechanisms]
        EC[Error Context<br/>Timestamp, service, operation]
        AR[Auto Recovery<br/>Where possible]
    end
    
    subgraph "Health Monitoring"
        HC[Health Checks<br/>Continuous monitoring]
        HS[Health Score<br/>100/100]
        AL[Alerting<br/>Prometheus + Alertmanager]
    end
    
    CB --> EH
    RL --> EH
    TO --> EH
    CP --> EH
    RL2 --> EH
    
    EH --> GD
    EH --> EC
    EH --> AR
    
    HC --> HS
    HS --> AL
```

## Performance Characteristics

```mermaid
graph LR
    subgraph "Current Performance"
        PS[Performance Score<br/>100/100]
        CS[Cost Score<br/>100/100]
        RU[Resource Usage<br/>1.55 CPU cores<br/>3.38 GB memory]
        OC[Operational Cost<br/>$0.47/hour<br/>$336.78/month]
    end
    
    subgraph "Data Coverage"
        DC[Data Coverage<br/>92 cryptocurrencies<br/>26 news sources]
        DR[Data Rate<br/>5min prices<br/>15min news]
        DS[Data Size<br/>5.77 GB database<br/>1.02 MB cache]
    end
    
    subgraph "Scaling"
        HPA[HPA Status<br/>3 services scaling<br/>1-3 replicas]
        TH[Thresholds<br/>70% CPU<br/>80% Memory]
        RT[Response Time<br/>Sub-second scaling]
    end
    
    PS --> HPA
    CS --> TH
    RU --> RT
    OC --> HPA
    DC --> TH
    DR --> RT
    DS --> HPA
```

## Access Points & Port Forwards

```mermaid
graph TB
    subgraph "External Access"
        UI[Web Browser]
    end
    
    subgraph "Port Forwards"
        PF1[kubectl port-forward<br/>prometheus 9090:9090]
        PF2[kubectl port-forward<br/>grafana 3000:3000]
        PF3[kubectl port-forward<br/>performance-monitor 8005:8000]
        PF4[kubectl port-forward<br/>cost-tracker 8006:8000]
        PF5[kubectl port-forward<br/>cache-manager 8007:8000]
    end
    
    subgraph "Service URLs"
        URL1[http://localhost:9090<br/>Prometheus]
        URL2[http://localhost:3000<br/>Grafana]
        URL3[http://localhost:8005<br/>Performance Monitor]
        URL4[http://localhost:8006<br/>Cost Tracker]
        URL5[http://localhost:8007<br/>Cache Manager]
    end
    
    UI --> PF1
    UI --> PF2
    UI --> PF3
    UI --> PF4
    UI --> PF5
    
    PF1 --> URL1
    PF2 --> URL2
    PF3 --> URL3
    PF4 --> URL4
    PF5 --> URL5
```

## Summary

These diagrams illustrate the comprehensive interaction patterns within the Crypto Data Collection System:

1. **High-Level Architecture**: Shows the complete system with all components and their relationships
2. **Data Flow**: Demonstrates how data flows through the system from external sources to storage
3. **News Collection**: Details the news collection and sentiment analysis process
4. **Monitoring**: Shows continuous health monitoring and alerting
5. **Autoscaling**: Illustrates how the system automatically scales based on load
6. **Cache Management**: Details intelligent cache management and optimization
7. **Cost Optimization**: Shows real-time cost tracking and optimization
8. **Service Discovery**: Demonstrates Kubernetes DNS-based service communication
9. **Error Handling**: Shows resilience patterns and error handling mechanisms
10. **Performance**: Illustrates current performance characteristics and scaling
11. **Access Points**: Shows how to access the system through port forwards

The system is designed for high availability, scalability, and maintainability with clear separation of concerns and well-defined integration points.
