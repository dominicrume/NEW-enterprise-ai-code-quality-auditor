"""
Daily scheduler entrypoint for the ETL pipeline.
Supports APScheduler with cron expressions, falling back to a pure Python interval loop.
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger("data_pipeline.scheduler")

# Try importing APScheduler
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APS_AVAILABLE = True
except ImportError:
    APS_AVAILABLE = False

def run_standard_loop(job_func: Callable[[], None], schedule_time_str: str):
    """
    Fallback scheduler loop using standard library.
    Runs once per day at the specified time (format 'HH:MM').
    """
    logger.info(f"Using standard library fallback loop. Target run time: daily at {schedule_time_str}")
    
    try:
        hour, minute = map(int, schedule_time_str.split(":"))
    except ValueError:
        logger.error(f"Invalid time format '{schedule_time_str}'. Defaulting to '00:00'.")
        hour, minute = 0, 0

    while True:
        now = datetime.now()
        target_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if now >= target_today:
            # If target time has already passed today, target is tomorrow
            target_run = target_today + timedelta(days=1)
        else:
            target_run = target_today
            
        sleep_seconds = (target_run - now).total_seconds()
        logger.info(f"Next scheduled run at {target_run.strftime('%Y-%m-%d %H:%M:%S')}. Sleeping for {sleep_seconds:.1f} seconds.")
        
        try:
            time.sleep(sleep_seconds)
            logger.info("Executing scheduled job...")
            job_func()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error during scheduled job run: {str(e)}")
            # Avoid tight looping on instant failure by sleeping a bit
            time.sleep(60)

def start_scheduler(job_func: Callable[[], None], cron_string: Optional[str] = None, schedule_time: str = "00:00"):
    """
    Starts the scheduler.
    If cron_string is provided, it uses the cron string to schedule the job.
    Otherwise, schedules it daily at the specified schedule_time (HH:MM).
    """
    if APS_AVAILABLE:
        logger.info("Starting scheduler using APScheduler.")
        scheduler = BlockingScheduler()
        
        if cron_string:
            try:
                # E.g. "0 0 * * *" or similar
                trigger = CronTrigger.from_crontab(cron_string)
                logger.info(f"Scheduling job using cron string: '{cron_string}'")
            except Exception as e:
                logger.error(f"Invalid cron string '{cron_string}': {str(e)}. Falling back to daily at {schedule_time}")
                trigger = CronTrigger(hour=int(schedule_time.split(":")[0]), minute=int(schedule_time.split(":")[1]))
        else:
            # Daily schedule
            try:
                hour, minute = map(int, schedule_time.split(":"))
                trigger = CronTrigger(hour=hour, minute=minute)
                logger.info(f"Scheduling job to run daily at {schedule_time}")
            except Exception as e:
                logger.error(f"Invalid time format '{schedule_time}': {str(e)}. Defaulting to daily at 00:00")
                trigger = CronTrigger(hour=0, minute=0)
                
        scheduler.add_job(job_func, trigger)
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("APScheduler stopped by user.")
    else:
        logger.warning("APScheduler is not installed. Falling back to the built-in time loop.")
        if cron_string:
            logger.warning("Cron strings are not supported in fallback mode. Job will default to run daily.")
        run_standard_loop(job_func, schedule_time)
