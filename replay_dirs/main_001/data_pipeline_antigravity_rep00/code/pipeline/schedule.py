"""
Scheduler module for the data pipeline.
Schedules execution daily at a given time or cron expression.
Falls back to a standard library sleep loop if APScheduler is not available.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger("data_pipeline.schedule")

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    APS_AVAILABLE = True
except ImportError:
    APS_AVAILABLE = False

def run_fallback_loop(job_func: Callable[[], None], schedule_time_str: str):
    """
    Standard library fallback sleep loop that runs daily at target 'HH:MM'.
    """
    logger.info(f"APScheduler not found. Using fallback standard library daily execution loop.")
    logger.info(f"Target run time configured: daily at {schedule_time_str}")
    
    try:
        hour, minute = map(int, schedule_time_str.split(":"))
    except ValueError:
        logger.error(f"Invalid daily time format '{schedule_time_str}'. Defaulting to '00:00'.")
        hour, minute = 0, 0

    while True:
        now = datetime.now()
        target_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if now >= target_today:
            target_run = target_today + timedelta(days=1)
        else:
            target_run = target_today
            
        sleep_seconds = (target_run - now).total_seconds()
        logger.info(f"Next scheduled run target: {target_run.strftime('%Y-%m-%d %H:%M:%S')}. Sleeping for {sleep_seconds:.1f} seconds.")
        
        try:
            time.sleep(sleep_seconds)
            logger.info("Executing scheduled pipeline run...")
            job_func()
        except KeyboardInterrupt:
            logger.info("Scheduler loop interrupted. Exiting.")
            break
        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
            time.sleep(60) # Avoid rapid tight loop crash

def start_scheduler(job_func: Callable[[], None], cron_string: Optional[str] = None, schedule_time: str = "00:00"):
    """
    Starts scheduling daily pipeline execution.
    If cron_string is provided, schedules with the cron expression.
    Otherwise, schedules daily at schedule_time ('HH:MM').
    """
    if APS_AVAILABLE:
        logger.info("Initializing APScheduler blocking scheduler.")
        scheduler = BlockingScheduler()
        
        if cron_string:
            try:
                trigger = CronTrigger.from_crontab(cron_string)
                logger.info(f"Scheduling job using cron trigger: '{cron_string}'")
            except Exception as e:
                logger.error(f"Invalid cron expression '{cron_string}': {str(e)}. Falling back to time '{schedule_time}'")
                hour, minute = map(int, schedule_time.split(":"))
                trigger = CronTrigger(hour=hour, minute=minute)
        else:
            try:
                hour, minute = map(int, schedule_time.split(":"))
                trigger = CronTrigger(hour=hour, minute=minute)
                logger.info(f"Scheduling job to run daily at {schedule_time}")
            except Exception as e:
                logger.error(f"Invalid daily time format '{schedule_time}': {str(e)}. Defaulting to daily at 00:00")
                trigger = CronTrigger(hour=0, minute=0)
                
        scheduler.add_job(job_func, trigger)
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
    else:
        run_fallback_loop(job_func, schedule_time)
