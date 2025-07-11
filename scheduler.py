from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from typing import Any, Dict
from schema import (
    TaskSchedulePayload,
    RepeatSimple,
    RepeatCustom,
    CustomDaily,
    CustomWeekly,
    CustomMonthly,
    EndRepeatNever,
    EndRepeatOnDate,
    EndRepeatAfterOccurrences,
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

def schedule_from_payload(payload: TaskSchedulePayload):
    task_id = payload.task_id
    start_time = payload.start_time if isinstance(payload.start_time, datetime) else datetime.fromisoformat(payload.start_time)
    is_repeat = payload.is_repeat
    args = getattr(payload, "args", [])
    kwargs = getattr(payload, "kwargs", {})  # Add this line
    
    trigger = None
    trigger_args = {}
    print(f"Scheduling task {task_id} at {start_time} with repeat={is_repeat}\n")

    print("Payload (formatted):")
    print(json.dumps(payload.model_dump(), indent=2, default=str))



    if not is_repeat:
        # ========== One-time job ==========
        trigger_args = {
            "run_date": start_time
        }
        trigger = DateTrigger(**trigger_args)
    else:
        repeat = payload.repeat
        end_repeat = payload.end_repeat
        
        # Apply end_repeat constraints
        if end_repeat and end_repeat.mode == "on_date":
            if isinstance(end_repeat.until, datetime):
                trigger_args["end_date"] = end_repeat.until
            else:
                trigger_args["end_date"] = datetime.fromisoformat(end_repeat.until)
        if repeat is None:
            raise ValueError("`repeat` must be provided if `is_repeat` is True.")
        

        # ========== Fixed patterns ==========
        if repeat.type in ["daily", "weekly", "monthly", "yearly"]:
            if repeat.type == "daily":
                # Use IntervalTrigger for daily repeat
                trigger_args = {
                    "days": 1,
                    "start_date": start_time
                }
                trigger = IntervalTrigger(**trigger_args)
            # Optionally, add similar logic for weekly/monthly/yearly if desired
            elif repeat.type == "weekly":
                trigger_args = {
                    "weeks": 1,
                    "start_date": start_time
                }
                trigger = IntervalTrigger(**trigger_args)
            else:
                # Fallback to original CronTrigger logic for monthly/yearly
                trigger_args.update({
                    "hour": start_time.hour,
                    "minute": start_time.minute,
                    "second": start_time.second,
                    "start_date": start_time,
                })
                if repeat.type == "monthly":
                    trigger_args["day"] = start_time.day
                elif repeat.type == "yearly":
                    trigger_args["month"] = start_time.month
                    trigger_args["day"] = start_time.day
                trigger = CronTrigger(**trigger_args)
        elif repeat.type == "custom":
            custom = repeat.custom
            frequency = custom.frequency
            if frequency == "daily":
                trigger_args.update({
                    "days": custom.interval,
                    "start_date": start_time
                })
                trigger = IntervalTrigger(**trigger_args)
            elif frequency == "weekly":
                weekdays = getattr(custom, "weekdays", None)
                if weekdays is None:
                    raise ValueError("Custom weekly schedule must provide 'weekdays'.")
                # CronTrigger expects comma-separated three-letter weekday names
                trigger_args.update({
                    "day_of_week": ",".join(weekdays),
                    "hour": start_time.hour,
                    "minute": start_time.minute,
                    "second": start_time.second,
                    "start_date": start_time
                })
                trigger = CronTrigger(**trigger_args)
            elif frequency == "monthly":
                trigger_args.update({
                    "day": start_time.day,
                    "month": f"*/{custom.interval}",
                    "hour": start_time.hour,
                    "minute": start_time.minute,
                    "second": start_time.second,
                    "start_date": start_time
                })
                trigger = CronTrigger(**trigger_args)
            else:
                raise ValueError("Invalid custom frequency")
        else:
            raise ValueError("Invalid repeat type")

    print(f"Scheduling job {task_id} with trigger: {trigger}\n")
    print(f"Trigger args: {trigger_args}\n")
    print(f"Trigger: {trigger}\n")
    scheduler.add_job(
        func=task_runner,
        trigger=trigger,  # Use the trigger object, not a cron string
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
schedule_from_payload(
    TaskSchedulePayload(
        task_id="daily_never_end",
        start_time=now + timedelta(seconds=3),
        is_repeat=True,
        repeat=RepeatSimple(type="daily"),
        end_repeat=EndRepeatNever(mode="never"),
        args=["daily at a time never ends."],
        kwargs={"priority": "high", "send_copy": True}
    )
)


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



scheduler.add_job(
    func=task_runner,
    trigger=CronTrigger(second="*"),
    id="test_every_second",
    name="test_every_second",
    args=["test_every_second"],
    kwargs={"demo": True},
    replace_existing=True,
)


time.sleep(20)  # Keep script alive to allow jobs to runimport timedef schedule_test_cron_every_second():