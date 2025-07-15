from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from datetime import datetime, timedelta
from typing import Any, Dict, Union, Optional
from features.schema import (
    TaskSchedulePayload,
    EndRepeatMode,
    RepeatType,
)
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
import pytz

scheduler = BackgroundScheduler()
scheduler.start()


def task_runner(*args, **kwargs):
    print("Task executed! Arguments: ", args, kwargs)


def schedule_from_payload(payload: TaskSchedulePayload) -> Job:
    task_id: str = payload.task_id
    start_time: datetime = payload.start_time if isinstance(payload.start_time, datetime) else datetime.fromisoformat(payload.start_time)
    args = getattr(payload, "args", [])
    kwargs = getattr(payload, "kwargs", {})

    repeat = payload.repeat
    end_repeat = payload.end_repeat

    # Apply end_repeat constraints
    end_date = None
    if end_repeat:
        if end_repeat.mode == EndRepeatMode.ON_DATE and end_repeat.until:
            end_date = end_repeat.until if isinstance(end_repeat.until, datetime) else datetime.fromisoformat(end_repeat.until)


    # If repeat is None, schedule a one-time job
    if not repeat:
        trigger = DateTrigger(run_date=start_time)
        print(f"Scheduling one-time job {task_id} with trigger: {trigger}\n")
        return scheduler.add_job(
            func=task_runner,
            trigger=trigger,
            id=task_id,
            name=task_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True,
        )
    


    # Define trigger logic for each repeat type
    def hourly_trigger():
        return IntervalTrigger(hours=repeat.frequency or 1, start_date=start_time, end_date=end_date)

    def daily_trigger():
        return IntervalTrigger(days=repeat.frequency or 1, start_date=start_time, end_date=end_date)

    def weekly_trigger():
        """
        Create a CalendarIntervalTrigger that fires every `repeat.frequency` weeks,
        starting at `start_time`, ending at `end_date`. Assumes UTC.
        """
        return CalendarIntervalTrigger(
            weeks=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            timezone=pytz.UTC
        )


    def monthly_trigger():
        if repeat.on_days:
            days = ",".join(map(str, repeat.on_days))
            return CronTrigger(day=days, hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)
        return CronTrigger(day=start_time.day, month=f"*/{repeat.frequency or 1}", hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)

    def yearly_trigger():
        return CronTrigger(month=start_time.month, day=start_time.day, hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)

    # Map repeat types to their corresponding trigger logic
    trigger_map = {
        RepeatType.HOURLY: hourly_trigger,
        RepeatType.DAILY: daily_trigger,
        RepeatType.WEEKLY: weekly_trigger,
        RepeatType.MONTHLY: monthly_trigger,
        RepeatType.YEARLY: yearly_trigger,
    }

    # Get the trigger function based on the repeat type
    trigger_func = trigger_map.get(repeat.type)
    if not trigger_func:
        raise ValueError("Invalid repeat type")

    trigger = trigger_func()

    print(f"Scheduling job {task_id} with trigger: {trigger}\n")
    return scheduler.add_job(
        func=task_runner,
        trigger=trigger,
        id=task_id,
        name=task_id,
        args=args,
        kwargs=kwargs,
        replace_existing=True,
    )