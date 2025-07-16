from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from datetime import datetime
from features.schema import (
    TaskSchedulePayload,
    EndRepeatMode,
    RepeatType,
    JobResponse
)
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from typing import List
import pytz

scheduler = BackgroundScheduler()
scheduler.start()


def task_runner(*args, **kwargs):
    print("Task executed! Arguments: ", args, kwargs)


def to_utc(dt: datetime) -> datetime:
    '''Convert a datetime to UTC timezone.'''
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.UTC)


def run_scheduler(payload: TaskSchedulePayload) -> Job:
    task_id: str = payload.task_id
    start_time: datetime = to_utc(payload.start_time)
    repeat = payload.repeat
    end_repeat = payload.end_repeat
    args = getattr(payload, "args", [])
    kwargs = getattr(payload, "kwargs", {})

    # Apply end repeat if provided
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
    '''
        IntervalTrigger: Use when time frame is smaller than a day (minute, hour). Repeat from start_time + interval.
        CalendarIntervalTrigger: Use when time frame is larger than a day to ensure correct calendar behaviour and avoid time drift.
        CronTrigger: Use for complex schedules (e.g., every Monday and Thursday).
        DateTrigger: Use for one-time jobs.
    '''
    def minutely_trigger():
        return IntervalTrigger(
            minutes=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC
        )

    def hourly_trigger():
        return IntervalTrigger(
            hours=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            timezone=pytz.UTC
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
        """
        Creates a weekly trigger.

        - If `repeat.on_weekdays` is provided and frequency == 1 (repeat every week on specific weekdays):
            → use CronTrigger (e.g. every week on Mon, Thu)

        - If frequency > 1 (repeat every X weeks, does not support multiple weekdays):
            → use CalendarIntervalTrigger & reject if multiple weekdays are requested (not supported in this mode)
            
        """
        weekdays = repeat.on_weekdays or []
        use_cron = weekdays and (repeat.frequency == 1)

        if use_cron:
            # APScheduler CronTrigger accepts comma-separated string of "mon,tue,wed"
            day_of_week_expr = ",".join(weekdays)

            return CronTrigger(
                day_of_week=day_of_week_expr,
                hour=start_time.hour,
                minute=start_time.minute,
                second=start_time.second,
                start_date=start_time,
                end_date=end_date,
                timezone=pytz.UTC,
            )

        if weekdays and (repeat.frequency or 1) > 1:
            raise ValueError(
                "Cannot schedule 'every X weeks on multiple weekdays'. "
                "Please create a separate job for each weekday."
            )

        # If no weekdays: repeat every X weeks from start_time
        return CalendarIntervalTrigger(
            weeks=repeat.frequency or 1,
            start_date=start_time,
            end_date=end_date,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            timezone=pytz.UTC,
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


    # --------- Trigger selection and job registration --------- #
    trigger_map = {
        RepeatType.MINUTELY: minutely_trigger,
        RepeatType.HOURLY: hourly_trigger,
        RepeatType.DAILY: daily_trigger,
        RepeatType.WEEKLY: weekly_trigger
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


def cancel_job(job_id: str):
    job = scheduler.get_job(job_id)
    if not job:
        raise Exception("Job not found")
    try:
        scheduler.remove_job(job_id)
    except Exception as e:
        raise Exception(f"Scheduler failure: {str(e)}")
    return {"message": f"Job {job_id} canceled successfully"}


def get_all_jobs() -> List[JobResponse]:
    """
    Returns a list of all scheduled jobs.
    """
    jobs: List[Job] = scheduler.get_jobs()

    jobs_list: List[JobResponse] = [
        JobResponse(
            id=job.id,
            name=job.name,
            func=str(job.func),
            args=job.args,
            kwargs=job.kwargs,
            coalesce=job.coalesce,
            trigger=str(job.trigger),
            executor=job.executor,
            misfire_grace_time=job.misfire_grace_time,
            max_instances=job.max_instances,
            next_run_time=job.next_run_time.isoformat() if job.next_run_time else None
        )
        for job in jobs
    ]
    return jobs_list



def remove_all_jobs():
    try:
        scheduler.remove_all_jobs()
        return {"message": "All jobs removed successfully."}
    except Exception as e:
        raise Exception(f"Scheduler failure: {str(e)}")