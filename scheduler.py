"""
Job Monitor Scheduler
Runs the job monitor at specified intervals
"""

import schedule
import time
import json
from datetime import datetime
from job_monitor import JobMonitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_job_monitor():
    """Execute the job monitor"""
    try:
        logging.info("Starting scheduled job monitor run...")
        monitor = JobMonitor()
        monitor.run()
        logging.info("Job monitor run completed")
    except Exception as e:
        logging.error(f"Error in scheduled run: {e}")

def setup_schedule():
    """Setup the schedule based on config"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    schedule_config = config.get('schedule', {})
    
    # Option 1: Run at specific times
    if 'run_times' in schedule_config:
        for run_time in schedule_config['run_times']:
            schedule.every().day.at(run_time).do(run_job_monitor)
            logging.info(f"Scheduled job monitor to run daily at {run_time}")
    
    # Option 2: Run at intervals
    elif 'check_interval_hours' in schedule_config:
        interval = schedule_config['check_interval_hours']
        schedule.every(interval).hours.do(run_job_monitor)
        logging.info(f"Scheduled job monitor to run every {interval} hours")
    
    # Default: run every 4 hours
    else:
        schedule.every(4).hours.do(run_job_monitor)
        logging.info("Scheduled job monitor to run every 4 hours (default)")

def main():
    """Main scheduler loop"""
    logging.info("Job Monitor Scheduler started")
    logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    setup_schedule()
    
    # Run immediately on start
    logging.info("Running initial job search...")
    run_job_monitor()
    
    # Then run on schedule
    logging.info("Entering scheduled mode...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\nScheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")
