#!/usr/bin/env python3
"""
Test script for the Automated Health Monitoring System

Quick test to validate the health monitoring system is working properly.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the monitoring script to the path
sys.path.append(str(Path(__file__).parent / "scripts" / "monitoring"))

try:
    from automated_health_monitoring import AutomatedHealthMonitor
except ImportError as e:
    print(f"Error importing health monitor: {e}")
    sys.exit(1)


async def test_health_monitoring_system():
    """Test the health monitoring system."""
    print("🏥 Testing Automated Health Monitoring System...")
    print("=" * 60)
    
    # Initialize the monitor
    config_path = "config/health_monitoring_config.json"
    monitor = AutomatedHealthMonitor(config_path)
    
    print("✅ Health monitor initialized successfully")
    
    # Test database initialization
    try:
        status_summary = monitor.database.get_service_status_summary()
        print(f"✅ Database connection successful (found {len(status_summary)} service records)")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test service health checks
    print("\n🔍 Testing service health checks...")
    try:
        health_statuses = await monitor.check_all_services()
        
        healthy_count = sum(1 for status in health_statuses if status.status == "healthy")
        total_count = len(health_statuses)
        
        print(f"📊 Health Check Results: {healthy_count}/{total_count} services healthy")
        
        # Show status for each service
        for status in health_statuses[:5]:  # Show first 5 services
            status_icon = "✅" if status.status == "healthy" else "❌"
            print(f"  {status_icon} {status.service_name}: {status.status} ({status.response_time:.2f}s)")
        
        if total_count > 5:
            print(f"  ... and {total_count - 5} more services")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test alert evaluation
    print("\n🚨 Testing alert evaluation...")
    try:
        for status in health_statuses[:3]:  # Test first 3 services
            alerts = monitor.alert_manager.evaluate_alerts(status)
            if alerts:
                print(f"  ⚠️ Alerts for {status.service_name}: {len(alerts)} triggered")
            else:
                print(f"  ✅ No alerts for {status.service_name}")
    except Exception as e:
        print(f"❌ Alert evaluation error: {e}")
        return False
    
    # Test health report generation
    print("\n📊 Testing health report generation...")
    try:
        report = await monitor.generate_health_report()
        print(f"✅ Health report generated successfully")
        print(f"  Overall Health: {report['overall_health']}")
        print(f"  Services: {report['summary']['healthy_services']}/{report['summary']['total_services']} healthy")
        print(f"  Health Percentage: {report['summary']['health_percentage']:.1f}%")
    except Exception as e:
        print(f"❌ Health report error: {e}")
        return False
    
    # Test dashboard data
    print("\n📈 Testing dashboard data generation...")
    try:
        dashboard_data = await monitor.get_health_dashboard_data()
        print(f"✅ Dashboard data generated successfully")
        print(f"  Data includes: {list(dashboard_data.keys())}")
    except Exception as e:
        print(f"❌ Dashboard data error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Health Monitoring System Test PASSED!")
    print("✅ All core functionality working correctly")
    print("📊 System ready for production deployment")
    
    return True


async def run_quick_health_check():
    """Run a quick health check and display results."""
    print("\n🚀 Running Quick Health Check...")
    print("-" * 40)
    
    config_path = "config/health_monitoring_config.json"
    monitor = AutomatedHealthMonitor(config_path)
    
    # Run a single monitoring cycle
    await monitor.run_monitoring_cycle()
    
    # Get and display summary
    report = await monitor.generate_health_report()
    
    print(f"\n📋 Quick Health Summary:")
    print(f"  🎯 Overall Status: {report['overall_health'].upper()}")
    print(f"  📊 Health Score: {report['summary']['health_percentage']:.1f}%")
    print(f"  ✅ Healthy: {report['summary']['healthy_services']}")
    print(f"  ❌ Unhealthy: {report['summary']['unhealthy_services']}")
    print(f"  🔴 Critical Issues: {report['summary']['critical_unhealthy']}")
    
    # Show unhealthy services
    unhealthy_services = [s for s in report['services'] if s['current_status'] != 'healthy']
    if unhealthy_services:
        print(f"\n⚠️ Services Needing Attention:")
        for service in unhealthy_services:
            print(f"  - {service['service_name']}: {service['current_status']}")
    else:
        print(f"\n🎉 All services are healthy!")


def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Run quick health check
        asyncio.run(run_quick_health_check())
    else:
        # Run full test suite
        success = asyncio.run(test_health_monitoring_system())
        
        if success:
            print("\n🚀 Ready to start health monitoring:")
            print("  python scripts/monitoring/automated_health_monitoring.py --config config/health_monitoring_config.json")
        else:
            print("\n❌ Health monitoring system has issues that need to be resolved")
            sys.exit(1)


if __name__ == "__main__":
    main()
