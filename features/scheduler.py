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

    # Always use UTC
    def to_utc(dt: datetime) -> datetime:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(pytz.UTC)

    start_time: datetime = to_utc(payload.start_time)
    args = getattr(payload, "args", [])
    kwargs = getattr(payload, "kwargs", {})

    repeat = payload.repeat
    end_repeat = payload.end_repeat

    end_date = None
    if end_repeat:
        if end_repeat.mode == EndRepeatMode.ON_DATE and end_repeat.until:
            end_date = to_utc(end_repeat.until)

    # One-time job
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

    # --------- Repeat trigger generators ---------

    def hourly_trigger():
        return CalendarIntervalTrigger(
            hour=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC,
            minute=start_time.minute,
            second=start_time.second,
        )

    def daily_trigger():
        return CalendarIntervalTrigger(
            days=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
        )

    def weekly_trigger():
        return CalendarIntervalTrigger(
            weeks=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
        )

    #region unused Triggers
    def monthly_trigger():
        '''
            Repeat every X month(s) on specific days.
            If `on_days` is provided, it will repeat on those days of the month.
            If `on_days` is not provided, it will repeat on the same day of the month as the start time.

            Warning: If day does not exist in the month (e.g., 31st in February), it will not run.
        '''
        days = repeat.on_days or [start_time.day]
        day_expr = ",".join(map(str, days))

        return CronTrigger(
            month=f"*/{repeat.frequency or 1}",
            day=day_expr,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC,
        )

    def yearly_trigger():
        return CronTrigger(
            month=start_time.month,
            day=start_time.day,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC,
        )
    #endregion


    # --------- Trigger selection and job registration ---------

    trigger_map = {
        RepeatType.HOURLY: hourly_trigger,
        RepeatType.DAILY: daily_trigger,
        RepeatType.WEEKLY: weekly_trigger,
        # RepeatType.MONTHLY: monthly_trigger,
        # RepeatType.YEARLY: yearly_trigger,
    }

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