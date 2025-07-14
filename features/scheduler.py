from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from datetime import datetime, timedelta
from typing import Any, Dict, Union
from features.schema import (
    TaskSchedulePayload,
    RepeatSimple,
    RepeatCustom,
    CustomDaily,
    CustomWeekly,
    CustomMonthly,
    EndRepeatNever,
    EndRepeatOnDate,
    EndRepeatAfterOccurrences,
    EndRepeatMode,
    RepeatType,
    Frequency,
    EndRepeat,
    CustomRepeat
)
import json
import time
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

scheduler = BackgroundScheduler()
scheduler.start()
now = datetime.now()

def task_runner(*args, **kwargs):
    print("Executing task with", args, kwargs)



def schedule_from_payload(payload: TaskSchedulePayload) -> Job:
    task_id: str = payload.task_id
    start_time: datetime = payload.start_time if isinstance(payload.start_time, datetime) else datetime.fromisoformat(payload.start_time)
    is_repeat: bool = payload.is_repeat
    args = getattr(payload, "args", [])
    kwargs = getattr(payload, "kwargs", {})  # Add this line
    
    trigger: Union[CronTrigger, IntervalTrigger, DateTrigger, None] = None


    if not is_repeat:
        # ========== One-time job ==========
        trigger = DateTrigger(run_date=start_time)
    else:
        # ========== Repeating job ==========
        repeat = payload.repeat
        end_repeat = payload.end_repeat


        # Apply end_repeat constraints
        end_date = None
        if end_repeat:
            if isinstance(end_repeat, EndRepeatOnDate): # Validate if end_repeat is of type EndRepeatOnDate
                end_date = end_repeat.until if isinstance(end_repeat.until, datetime) else datetime.fromisoformat(end_repeat.until)

        if repeat is None:
            raise ValueError("`repeat` must be provided if `is_repeat` is True.")

        # Repeat Custom handling
        if isinstance(repeat, RepeatCustom):
            custom = repeat.custom
            match custom.frequency:
                case Frequency.DAILY:
                    trigger = IntervalTrigger(days=custom.interval, start_date=start_time, end_date=end_date)
                case Frequency.WEEKLY:
                    weekdays = getattr(custom, "weekdays", None)
                    if weekdays is None:
                        raise ValueError("Custom weekly schedule must provide 'weekdays'.")
                    # CronTrigger expects comma-separated three-letter weekday names
                    trigger = CronTrigger(day_of_week=",".join(weekdays), hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)
                case Frequency.MONTHLY:
                    trigger = CronTrigger(day=start_time.day, month=f"*/{custom.interval}", hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)
                case _:
                    raise ValueError("Invalid custom frequency")
        # Repeat Simple handling
        elif repeat.type in [RepeatType.DAILY, RepeatType.WEEKLY, RepeatType.MONTHLY, RepeatType.YEARLY]:
            match repeat.type:
                case RepeatType.DAILY:
                    trigger = IntervalTrigger(days=1, start_date=start_time, end_date=end_date)
                case RepeatType.WEEKLY:
                    trigger = IntervalTrigger(weeks=1, start_date=start_time, end_date=end_date)
                case RepeatType.MONTHLY:
                    trigger = CronTrigger(day=start_time.day, hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)
                case RepeatType.YEARLY:
                    trigger = CronTrigger(month=start_time.month, day=start_time.day, hour=start_time.hour, minute=start_time.minute, second=start_time.second, start_date=start_time, end_date=end_date)
                case _:
                    raise ValueError("Invalid repeat type")
        else:
            raise ValueError("Invalid repeat type")



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
    











# ========== Test Examples ==========



# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="send_email_once",
#         start_time=now + timedelta(seconds=5),
#         is_repeat=False,
#         args=["user@example.com", "Hello!"],
#         kwargs={"subject": "Test Email", "body": "This is a test email."}
#     )
# )



# 2. Daily repeat, never ends, with kwargs
# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="daily_never_end",
#         start_time=now + timedelta(seconds=3),
#         is_repeat=True,
#         repeat=RepeatSimple(type="daily"),
#         end_repeat=EndRepeatNever(mode="never"),
#         args=["daily at a time never ends."],
#         kwargs={"priority": "high", "send_copy": True}
#     )
# )


# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="custom_daily_after_occurrences",
#         start_time=now + timedelta(seconds=2),
#         is_repeat=True,
#         repeat=RepeatCustom(
#             type="custom",
#             custom=CustomDaily(frequency="daily", interval=1)
#         ),
#         end_repeat=None,
#         args=["Daily After Occurrences"],
#         kwargs={"custom_flag": 123}
#     )
# )

# 3. Weekly repeat, ends on a specific date, with both args and kwargs
# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="weekly_end_on_date",
#         start_time=now + timedelta(seconds=6),
#         is_repeat=True,
#         repeat=RepeatSimple(type="weekly"),
#         end_repeat=EndRepeatOnDate(mode="on_date", until=now + timedelta(seconds=20)),
#         args=["weekly_summary"],
#         kwargs={"recipients": ["a@example.com", "b@example.com"]}
#     )
# )

# 4. Custom daily repeat every 2 days, ends after 3 occurrences
# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="custom_daily_after_occurrences",
#         start_time=now + timedelta(seconds=8),
#         is_repeat=True,
#         repeat=RepeatCustom(
#             type="custom",
#             custom=CustomDaily(frequency="daily", interval=2)
#         ),
#         end_repeat=EndRepeatAfterOccurrences(mode="after_occurrences", occurrences=3),
#         args=["custom_task"],
#         kwargs={"custom_flag": 123}
#     )
# )

# 5. Custom weekly repeat on Monday and Friday, never ends
# schedule_from_payload(
#     TaskSchedulePayload(
#         task_id="custom_weekly_never_end",
#         start_time=now + timedelta(seconds=10),
#         is_repeat=True,
#         repeat=RepeatCustom(weekly",
#             type="custom",
#                 frequency="weekly",   weekdays=["mon", "fri"]
#                 interval=1,  )
#                 weekdays=["mon", "fri"]
#             )er(mode="never"),
#         ),
#         end_repeat=EndRepeatNever(mode="never"),   kwargs={"note": "This is a custom weekly job"}
#         args=["weekly_custom"],   )
#         kwargs={"note": "This is a custom weekly job"}# )
#     )
# )or 10 seconds



# scheduler.add_job(
#     func=task_runner,
#     trigger=CronTrigger(second="*"),
#     id="test_every_second",
#     name="test_every_second",
#     args=["test_every_second"],
#     kwargs={"demo": True},
#     replace_existing=True,
# )