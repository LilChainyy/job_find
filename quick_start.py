"""
Quick Start - Test the Job Monitor
Run this first to see how it works
"""

import json
import os
from job_monitor import JobMonitor

def quick_setup():
    """Quick interactive setup"""
    print("=" * 60)
    print("JOB MONITOR - QUICK START")
    print("=" * 60)
    print()
    
    # Check if config exists
    if not os.path.exists('config.json'):
        print("❌ config.json not found!")
        print("Creating a default config for you...")
        
        default_config = {
            "keywords": [
                "trade operations",
                "trading operations",
                "settlements"
            ],
            "locations": [
                "New York, NY",
                "Remote"
            ],
            "companies_to_monitor": {},
            "linkedin_email": "",
            "linkedin_password": "",
            "auto_apply": False,
            "confirm_before_submit": True,
            "show_browser": True
        }
        
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print("✓ Created config.json")
        print()
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Check credentials
    if not config.get('linkedin_email') or config['linkedin_email'] == 'your_email@example.com':
        print("⚠️  LinkedIn credentials not set in config.json")
        print()
        print("For full functionality, add your LinkedIn email and password to config.json")
        print("Without credentials, the script can only scrape public job listings.")
        print()
        
        response = input("Continue without auto-apply features? (y/n): ")
        if response.lower() != 'y':
            print("\nPlease update config.json with your credentials and try again.")
            return False
        
        config['auto_apply'] = False
    
    # Show configuration
    print("\n" + "=" * 60)
    print("CURRENT CONFIGURATION:")
    print("=" * 60)
    print(f"Keywords: {', '.join(config['keywords'][:3])}...")
    print(f"Locations: {', '.join(config['locations'])}")
    print(f"Auto-apply: {'✓ Enabled' if config['auto_apply'] else '✗ Disabled (monitor only)'}")
    print(f"Show browser: {'✓ Yes' if config['show_browser'] else '✗ No (headless)'}")
    print("=" * 60)
    print()
    
    response = input("Start job search? (y/n): ")
    if response.lower() != 'y':
        print("Setup cancelled.")
        return False
    
    return True

def main():
    """Run the quick start"""
    if not quick_setup():
        return
    
    print("\n🔍 Starting job search...")
    print("This may take a few minutes.\n")
    
    try:
        monitor = JobMonitor()
        monitor.run()
        
        print("\n" + "=" * 60)
        print("✓ SEARCH COMPLETE!")
        print("=" * 60)
        
        if monitor.jobs_found:
            print(f"\n📋 Found {len(monitor.jobs_found)} jobs:")
            print()
            
            for i, job in enumerate(monitor.jobs_found[:5], 1):
                print(f"{i}. {job['title']}")
                print(f"   {job['company']} - {job['location']}")
                print(f"   {job['url']}")
                print(f"   Status: {job['status']}")
                print()
            
            if len(monitor.jobs_found) > 5:
                print(f"   ... and {len(monitor.jobs_found) - 5} more jobs")
            
            print(f"\n✓ All results saved to: job_tracker_master.csv")
            print(f"✓ Details logged to: job_monitor.log")
        else:
            print("\n😕 No jobs found matching your criteria.")
            print("\nTips:")
            print("- Try broader keywords in config.json")
            print("- Add more locations")
            print("- Check if LinkedIn is accessible")
        
        print("\n" + "=" * 60)
        print("\nNext steps:")
        print("1. Review job_tracker_master.csv")
        print("2. To run automatically: python scheduler.py")
        print("3. To customize: edit config.json")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCheck job_monitor.log for details")
        print("Common issues:")
        print("- ChromeDriver not installed: pip install webdriver-manager")
        print("- LinkedIn credentials incorrect")
        print("- Network/firewall blocking access")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
