# Made by Mister 💛
import time
import asyncio
from loguru import logger
from typing import Dict, Any, Optional

class HealthMonitor:
    """The 'Nervous System' health probe. Monitors server latency and network stability."""
    
    def __init__(self):
        self.last_check_time = 0
        self.latency_samples = []
    
    async def check_network_latency(self) -> float:
        """Pings the Organism's responsiveness."""
        start = time.perf_counter()
        # Simulation of a simple internal health check
        await asyncio.sleep(0.01) # Baseline
        latency = (time.perf_counter() - start) * 1000
        
        self.latency_samples.append(latency)
        if len(self.latency_samples) > 10:
            self.latency_samples.pop(0)
            
        return latency

    def get_health_status(self) -> Dict[str, Any]:
        """Gathers a health report for the user."""
        avg_latency = sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0
        status = "Healthy"
        if avg_latency > 100: status = "Slow Connection"
        if avg_latency > 500: status = "Critical Delay"
        
        return {
            "status": status,
            "avg_latency": round(avg_latency, 2),
            "healthy": avg_latency < 300
        }
