"""
Performance testing for consciousness system under load.
Tests response times, throughput, and resource usage under various load conditions.
"""
import asyncio
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import psutil
import pytest

from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.core.emotion_processor import EmotionProcessor
from consciousness.core.query_engine import QueryEngine


class PerformanceMetrics:
    """Utility class for collecting performance metrics."""

    def __init__(self):
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self._monitor_resources()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.end_time = time.time()

    def record_response(self, response_time, success=True):
        """Record a response time."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def _monitor_resources(self):
        """Monitor system resources in background."""

        def monitor():
            while self.end_time is None:
                self.memory_usage.append(psutil.virtual_memory().percent)
                self.cpu_usage.append(psutil.cpu_percent())
                time.sleep(0.1)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def get_summary(self):
        """Get performance summary statistics."""
        if not self.response_times:
            return {}

        return {
            "total_requests": len(self.response_times),
            "success_rate": self.success_count / len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[
                18
            ],  # 95th percentile
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[
                98
            ],  # 99th percentile
            "max_response_time": max(self.response_times),
            "min_response_time": min(self.response_times),
            "avg_memory_usage": statistics.mean(self.memory_usage)
            if self.memory_usage
            else 0,
            "max_memory_usage": max(self.memory_usage) if self.memory_usage else 0,
            "avg_cpu_usage": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            "max_cpu_usage": max(self.cpu_usage) if self.cpu_usage else 0,
            "total_duration": self.end_time - self.start_time if self.end_time else 0,
            "throughput": len(self.response_times) / (self.end_time - self.start_time)
            if self.end_time
            else 0,
        }


@pytest.fixture
async def consciousness_engine_performance():
    """Create consciousness engine optimized for performance testing."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        engine = ConsciousnessEngine()
        await engine.initialize()

        # Optimize for performance testing
        engine.emotion_processor._gather_emotional_factors = AsyncMock(
            return_value={
                "system_health": {"score": 0.8},
                "user_interaction": {"satisfaction": 0.7, "interaction_frequency": 0.5},
                "environmental": {"overall_score": 0.6},
                "task_completion": {"completion_rate": 0.9, "task_load": 0.4},
                "learning_progress": {
                    "improvement_score": 0.6,
                    "learning_activity": 0.3,
                },
            }
        )

        yield engine
        await engine.stop()


@pytest.mark.asyncio
async def test_concurrent_query_processing_load(consciousness_engine_performance):
    """Test performance under concurrent query load."""
    engine = consciousness_engine_performance
    metrics = PerformanceMetrics()

    # Test parameters
    concurrent_users = 50
    queries_per_user = 10

    test_queries = [
        "How are you feeling?",
        "What's the temperature in the living room?",
        "Turn on the lights",
        "Is everything working properly?",
        "What devices are connected?",
        "How comfortable is the environment?",
        "Can you optimize the energy usage?",
        "What's your current emotional state?",
        "Are there any issues I should know about?",
        "How efficient is the system running?",
    ]

    async def user_simulation(user_id):
        """Simulate a user sending multiple queries."""
        user_metrics = []

        for query_num in range(queries_per_user):
            query = test_queries[query_num % len(test_queries)]

            start_time = time.time()
            try:
                response = await engine.process_query(query)
                end_time = time.time()
                response_time = (
                    end_time - start_time
                ) * 1000  # Convert to milliseconds

                user_metrics.append(response_time)
                metrics.record_response(response_time, success=True)

                assert response is not None
                assert len(response.get("response", "")) > 0

            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                metrics.record_response(response_time, success=False)
                print(f"Query failed for user {user_id}: {e}")

            # Small delay between queries from same user
            await asyncio.sleep(0.01)

        return user_metrics

    # Start monitoring
    metrics.start_monitoring()

    # Run concurrent user simulations
    tasks = [user_simulation(i) for i in range(concurrent_users)]
    user_results = await asyncio.gather(*tasks)

    # Stop monitoring
    metrics.stop_monitoring()

    # Analyze results
    summary = metrics.get_summary()

    # Performance assertions
    assert summary["success_rate"] > 0.95  # 95% success rate
    assert summary["avg_response_time"] < 500  # Average under 500ms
    assert summary["p95_response_time"] < 1000  # 95th percentile under 1s
    assert summary["throughput"] > 50  # At least 50 requests/second
    assert summary["max_memory_usage"] < 80  # Memory usage under 80%

    print(f"Load Test Results:")
    print(f"  Total Requests: {summary['total_requests']}")
    print(f"  Success Rate: {summary['success_rate']:.2%}")
    print(f"  Avg Response Time: {summary['avg_response_time']:.2f}ms")
    print(f"  P95 Response Time: {summary['p95_response_time']:.2f}ms")
    print(f"  Throughput: {summary['throughput']:.2f} req/s")
    print(f"  Max Memory Usage: {summary['max_memory_usage']:.1f}%")


@pytest.mark.asyncio
async def test_sustained_load_endurance(consciousness_engine_performance):
    """Test performance under sustained load over time."""
    engine = consciousness_engine_performance
    metrics = PerformanceMetrics()

    # Test parameters
    duration_minutes = 5  # 5-minute endurance test
    requests_per_second = 20

    test_queries = [
        "Status check",
        "Environment query",
        "Device control request",
        "Optimization query",
    ]

    async def sustained_load():
        """Generate sustained load for specified duration."""
        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            query = test_queries[int(time.time()) % len(test_queries)]

            start_time = time.time()
            try:
                response = await engine.process_query(query)
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=True)

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=False)

            # Control request rate
            await asyncio.sleep(1.0 / requests_per_second)

    # Start monitoring
    metrics.start_monitoring()

    # Run sustained load
    await sustained_load()

    # Stop monitoring
    metrics.stop_monitoring()

    summary = metrics.get_summary()

    # Endurance test assertions
    assert summary["success_rate"] > 0.98  # Higher success rate for sustained load
    assert summary["avg_response_time"] < 300  # Lower average for sustained operation
    assert (
        summary["total_duration"] >= duration_minutes * 60 * 0.95
    )  # Ran for expected duration

    # Check for performance degradation over time
    early_responses = metrics.response_times[:100]
    late_responses = metrics.response_times[-100:]

    early_avg = statistics.mean(early_responses)
    late_avg = statistics.mean(late_responses)
    degradation = (late_avg - early_avg) / early_avg

    assert degradation < 0.5  # Less than 50% performance degradation

    print(f"Endurance Test Results:")
    print(f"  Duration: {summary['total_duration']:.1f}s")
    print(f"  Avg Response Time: {summary['avg_response_time']:.2f}ms")
    print(f"  Performance Degradation: {degradation:.1%}")


@pytest.mark.asyncio
async def test_memory_usage_under_load(consciousness_engine_performance):
    """Test memory usage and potential leaks under load."""
    engine = consciousness_engine_performance

    # Measure baseline memory
    import gc

    gc.collect()
    baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    memory_samples = [baseline_memory]

    # Generate load with memory monitoring
    for iteration in range(10):
        # Process batch of queries
        tasks = []
        for i in range(100):
            task = engine.process_query(f"Query {iteration}-{i}")
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Force garbage collection and measure memory
        gc.collect()
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_samples.append(current_memory)

        # Small delay between batches
        await asyncio.sleep(0.1)

    # Analyze memory usage
    max_memory = max(memory_samples)
    final_memory = memory_samples[-1]
    memory_growth = final_memory - baseline_memory
    peak_growth = max_memory - baseline_memory

    # Memory usage assertions
    assert memory_growth < 100  # Less than 100MB growth
    assert peak_growth < 200  # Less than 200MB peak growth
    assert final_memory / baseline_memory < 2.0  # Less than 2x baseline

    print(f"Memory Usage Test:")
    print(f"  Baseline: {baseline_memory:.1f}MB")
    print(f"  Final: {final_memory:.1f}MB")
    print(f"  Growth: {memory_growth:.1f}MB")
    print(f"  Peak Growth: {peak_growth:.1f}MB")


@pytest.mark.asyncio
async def test_emotion_processor_performance(consciousness_engine_performance):
    """Test emotion processor performance under load."""
    engine = consciousness_engine_performance
    emotion_processor = engine.emotion_processor

    metrics = PerformanceMetrics()

    # Test parameters
    iterations = 1000

    async def emotion_processing_load():
        """Generate load on emotion processor."""
        for i in range(iterations):
            start_time = time.time()
            try:
                # Process emotional state update
                await emotion_processor.process_current_state()
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=True)

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=False)

    # Start monitoring
    metrics.start_monitoring()

    # Run emotion processing load
    await emotion_processing_load()

    # Stop monitoring
    metrics.stop_monitoring()

    summary = metrics.get_summary()

    # Emotion processor performance assertions
    assert summary["success_rate"] > 0.99  # Very high success rate
    assert summary["avg_response_time"] < 50  # Fast emotion processing
    assert summary["p95_response_time"] < 100  # Consistent performance

    print(f"Emotion Processor Performance:")
    print(f"  Avg Response Time: {summary['avg_response_time']:.2f}ms")
    print(f"  P95 Response Time: {summary['p95_response_time']:.2f}ms")
    print(f"  Throughput: {summary['throughput']:.2f} updates/s")


@pytest.mark.asyncio
async def test_query_engine_throughput(consciousness_engine_performance):
    """Test query engine throughput limits."""
    engine = consciousness_engine_performance
    query_engine = engine.query_engine

    # Test different query complexities
    query_types = {
        "simple": "Hello",
        "medium": "What's the temperature in the living room?",
        "complex": "Analyze the energy efficiency of all devices and provide optimization recommendations",
        "emotional": "How are you feeling about the current environmental conditions?",
    }

    results = {}

    for query_type, query in query_types.items():
        metrics = PerformanceMetrics()
        metrics.start_monitoring()

        # Test throughput for this query type
        iterations = 200

        for i in range(iterations):
            start_time = time.time()
            try:
                response = await query_engine.process_query(query)
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=True)

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                metrics.record_response(response_time, success=False)

        metrics.stop_monitoring()
        results[query_type] = metrics.get_summary()

    # Analyze results by complexity
    for query_type, summary in results.items():
        print(f"{query_type.title()} Query Performance:")
        print(f"  Avg Response Time: {summary['avg_response_time']:.2f}ms")
        print(f"  Throughput: {summary['throughput']:.2f} queries/s")

        # Performance expectations by complexity
        if query_type == "simple":
            assert summary["avg_response_time"] < 20
            assert summary["throughput"] > 100
        elif query_type == "medium":
            assert summary["avg_response_time"] < 50
            assert summary["throughput"] > 50
        elif query_type == "complex":
            assert summary["avg_response_time"] < 200
            assert summary["throughput"] > 10
        elif query_type == "emotional":
            assert summary["avg_response_time"] < 100
            assert summary["throughput"] > 20


@pytest.mark.asyncio
async def test_database_operation_performance(consciousness_engine_performance):
    """Test database operation performance under load."""
    engine = consciousness_engine_performance

    # Mock intensive database operations
    mock_session = engine.emotion_processor.session

    # Test read operations
    read_metrics = PerformanceMetrics()
    read_metrics.start_monitoring()

    for i in range(500):
        start_time = time.time()
        try:
            # Simulate database read
            await mock_session.execute("SELECT * FROM emotional_states LIMIT 10")
            response_time = (time.time() - start_time) * 1000
            read_metrics.record_response(response_time, success=True)
        except Exception:
            response_time = (time.time() - start_time) * 1000
            read_metrics.record_response(response_time, success=False)

    read_metrics.stop_monitoring()

    # Test write operations
    write_metrics = PerformanceMetrics()
    write_metrics.start_monitoring()

    for i in range(200):
        start_time = time.time()
        try:
            # Simulate database write
            await mock_session.commit()
            response_time = (time.time() - start_time) * 1000
            write_metrics.record_response(response_time, success=True)
        except Exception:
            response_time = (time.time() - start_time) * 1000
            write_metrics.record_response(response_time, success=False)

    write_metrics.stop_monitoring()

    read_summary = read_metrics.get_summary()
    write_summary = write_metrics.get_summary()

    # Database performance assertions
    assert read_summary["avg_response_time"] < 10  # Fast reads
    assert write_summary["avg_response_time"] < 50  # Reasonable write time
    assert read_summary["throughput"] > 200  # High read throughput
    assert write_summary["throughput"] > 20  # Reasonable write throughput

    print(f"Database Performance:")
    print(f"  Read Avg: {read_summary['avg_response_time']:.2f}ms")
    print(f"  Write Avg: {write_summary['avg_response_time']:.2f}ms")
    print(f"  Read Throughput: {read_summary['throughput']:.2f} ops/s")
    print(f"  Write Throughput: {write_summary['throughput']:.2f} ops/s")


@pytest.mark.asyncio
async def test_stress_testing_resource_limits(consciousness_engine_performance):
    """Stress test to find resource limits and breaking points."""
    engine = consciousness_engine_performance

    # Gradually increase load until failure or resource limits
    load_levels = [10, 25, 50, 100, 200, 500]
    results = {}

    for concurrent_load in load_levels:
        print(f"Testing load level: {concurrent_load} concurrent requests")

        metrics = PerformanceMetrics()
        metrics.start_monitoring()

        async def stress_worker():
            """Worker that generates stress load."""
            for i in range(10):  # Each worker does 10 operations
                try:
                    start_time = time.time()
                    await engine.process_query(f"Stress test query {i}")
                    response_time = (time.time() - start_time) * 1000
                    metrics.record_response(response_time, success=True)
                except Exception:
                    response_time = (time.time() - start_time) * 1000
                    metrics.record_response(response_time, success=False)

        # Run concurrent workers
        tasks = [stress_worker() for _ in range(concurrent_load)]
        await asyncio.gather(*tasks)

        metrics.stop_monitoring()
        summary = metrics.get_summary()
        results[concurrent_load] = summary

        # Stop if success rate drops too low or response times get too high
        if summary["success_rate"] < 0.8 or summary["avg_response_time"] > 5000:
            print(f"Breaking point reached at load level {concurrent_load}")
            break

    # Analyze stress test results
    for load, summary in results.items():
        print(
            f"Load {load}: Success {summary['success_rate']:.1%}, "
            f"Avg {summary['avg_response_time']:.1f}ms, "
            f"P95 {summary['p95_response_time']:.1f}ms"
        )

    # Verify system handled reasonable load levels
    assert 50 in results  # Should handle at least 50 concurrent users
    assert results[50]["success_rate"] > 0.9  # With good success rate
