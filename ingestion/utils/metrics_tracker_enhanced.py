# Enhanced MetricsTracker methods to add to existing file

async def query_mcp_store_details(
    self,
    mcp_id: str,
    mcp_store_url: str = "http://localhost:5500"
) -> Dict[str, Any]:
    """
    Query mcp-store for MCP persistence details (NEW!).
    
    Args:
        mcp_id: The MCP identifier
        mcp_store_url: URL of the mcp-store service
    
    Returns:
        Dictionary with storage location, size, and metadata
    """
    details = {
        "queried": True,
        "mcp_id": mcp_id,
        "storage_location": f"/data/mcp/{mcp_id}",
        "mcp_size_mb": None,
        "index_size_mb": None,
        "total_documents": None,
        "created_at": None,
        "last_accessed": None,
        "error": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{mcp_store_url}/api/v1/mcp/{mcp_id}/details"
            )
            
            if response.status_code == 200:
                data = response.json()
                details.update({
                    "storage_location": data.get("storage_location", f"/data/mcp/{mcp_id}"),
                    "mcp_size_mb": data.get("size_bytes", 0) / (1024 * 1024),
                    "index_size_mb": data.get("index_size_bytes", 0) / (1024 * 1024),
                    "total_documents": data.get("document_count", 0),
                    "created_at": data.get("created_at"),
                    "last_accessed": data.get("last_accessed")
                })
            else:
                details["error"] = f"mcp-store returned {response.status_code}"
    
    except Exception as e:
        details["error"] = str(e)
    
    # Update MCP lifecycle metrics
    if self.mcp_lifecycle:
        self.mcp_lifecycle.storage_location = details["storage_location"]
        self.mcp_lifecycle.mcp_size_mb = details["mcp_size_mb"]
    
    return details

async def measure_container_specs(
    self,
    mcp_id: str,
    container_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Measure Docker container specifications (NEW!).
    
    Args:
        mcp_id: The MCP identifier
        container_id: Optional Docker container ID
    
    Returns:
        Dictionary with container image, size, and resource limits
    """
    specs = {
        "measured": True,
        "mcp_id": mcp_id,
        "container_id": container_id,
        "image_name": None,
        "image_size_mb": None,
        "cpu_limit": None,
        "memory_limit_mb": None,
        "status": None,
        "uptime_seconds": None,
        "error": None
    }
    
    try:
        client = docker.from_env()
        
        # Find container by ID or by label
        if container_id:
            container = client.containers.get(container_id)
        else:
            # Try to find by MCP ID label
            containers = client.containers.list(
                filters={"label": f"mcp_id={mcp_id}"}
            )
            if containers:
                container = containers[0]
            else:
                specs["error"] = "Container not found"
                return specs
        
        # Get container details
        specs["container_id"] = container.id[:12]
        specs["status"] = container.status
        
        # Get image info
        image = container.image
        specs["image_name"] = image.tags[0] if image.tags else image.id[:12]
        specs["image_size_mb"] = image.attrs.get("Size", 0) / (1024 * 1024)
        
        # Get resource limits
        host_config = container.attrs.get("HostConfig", {})
        specs["memory_limit_mb"] = host_config.get("Memory", 0) / (1024 * 1024) if host_config.get("Memory") else None
        specs["cpu_limit"] = host_config.get("CpuShares", None)
        
        # Calculate uptime
        started_at = container.attrs.get("State", {}).get("StartedAt")
        if started_at:
            try:
                from dateutil import parser as date_parser
                start_time = date_parser.parse(started_at)
                uptime = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                specs["uptime_seconds"] = uptime
            except:
                pass
        
        # Update MCP lifecycle metrics
        if self.mcp_lifecycle:
            self.mcp_lifecycle.container_id = specs["container_id"]
            self.mcp_lifecycle.container_image = specs["image_name"]
            self.mcp_lifecycle.container_size_mb = specs["image_size_mb"]
    
    except docker.errors.DockerException as e:
        specs["error"] = f"Docker error: {str(e)}"
    except Exception as e:
        specs["error"] = f"Error: {str(e)}"
    
    return specs

async def benchmark_query_performance(
    self,
    mcp_id: str,
    gateway_url: str = "http://localhost:8001",
    num_queries: int = 10,
    test_queries: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Benchmark MCP query performance (NEW!).
    
    Args:
        mcp_id: The MCP identifier
        gateway_url: URL of the mcp-gateway
        num_queries: Number of test queries to run
        test_queries: Optional list of test queries
    
    Returns:
        Dictionary with avg, p95, p99 query times and throughput
    """
    benchmark = {
        "benchmarked": True,
        "mcp_id": mcp_id,
        "num_queries": num_queries,
        "query_times_ms": [],
        "avg_query_time_ms": None,
        "median_query_time_ms": None,
        "p95_query_time_ms": None,
        "p99_query_time_ms": None,
        "min_query_time_ms": None,
        "max_query_time_ms": None,
        "throughput_qps": None,
        "success_rate": None,
        "errors": [],
        "error": None
    }
    
    # Generate test queries if not provided
    if not test_queries:
        test_queries = [
            "What is the Horus Heresy?",
            "Who was the Warmaster?",
            "Which Legions remained loyal?",
            "What role did Chaos play?",
            "Describe the Siege of Terra",
            "Who were the Primarchs?",
            "What caused the rebellion?",
            "What was the outcome?",
            "How long did it last?",
            "What is the Emperor's role?"
        ][:num_queries]
    
    successes = 0
    start_benchmark = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, query in enumerate(test_queries, 1):
                try:
                    query_start = time.time()
                    
                    response = await client.post(
                        f"{gateway_url}/api/v1/query",
                        json={
                            "mcp_id": mcp_id,
                            "query": query,
                            "max_results": 5
                        }
                    )
                    
                    query_duration_ms = (time.time() - query_start) * 1000
                    
                    if response.status_code == 200:
                        benchmark["query_times_ms"].append(query_duration_ms)
                        successes += 1
                    else:
                        benchmark["errors"].append(f"Query {i}: HTTP {response.status_code}")
                
                except Exception as e:
                    benchmark["errors"].append(f"Query {i}: {str(e)}")
                
                # Small delay between queries
                await asyncio.sleep(0.1)
    
    except Exception as e:
        benchmark["error"] = str(e)
        return benchmark
    
    # Calculate statistics
    if benchmark["query_times_ms"]:
        times = sorted(benchmark["query_times_ms"])
        benchmark["avg_query_time_ms"] = statistics.mean(times)
        benchmark["median_query_time_ms"] = statistics.median(times)
        benchmark["min_query_time_ms"] = min(times)
        benchmark["max_query_time_ms"] = max(times)
        
        # Calculate percentiles
        if len(times) >= 2:
            p95_idx = int(len(times) * 0.95)
            p99_idx = int(len(times) * 0.99)
            benchmark["p95_query_time_ms"] = times[min(p95_idx, len(times) - 1)]
            benchmark["p99_query_time_ms"] = times[min(p99_idx, len(times) - 1)]
        
        # Calculate throughput
        total_time = time.time() - start_benchmark
        benchmark["throughput_qps"] = len(times) / total_time if total_time > 0 else 0
        
        # Success rate
        benchmark["success_rate"] = successes / num_queries
        
        # Update MCP lifecycle metrics
        if self.mcp_lifecycle:
            self.mcp_lifecycle.query_times_ms.extend(times)
            self.mcp_lifecycle.avg_query_time_ms = benchmark["avg_query_time_ms"]
            self.mcp_lifecycle.p95_query_time_ms = benchmark["p95_query_time_ms"]
            self.mcp_lifecycle.p99_query_time_ms = benchmark["p99_query_time_ms"]
    
    return benchmark

