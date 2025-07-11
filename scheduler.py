from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from typing import Any, Dict
from schema import TaskSchedulePayload

scheduler = BackgroundScheduler()
scheduler.start()

def task_runner(*args):
    print("Executing task with", args)

def schedule_from_payload(payload: TaskSchedulePayload):
    task_id = payload.task_id
    start_time = payload.start_time if isinstance(payload.start_time, datetime) else datetime.fromisoformat(payload.start_time)
    is_repeat = payload.is_repeat
    args = getattr(payload, "args", [])
    
    trigger = None
    trigger_args = {}
    print(f"Scheduling task {task_id} at {start_time} with repeat={is_repeat}\n")

    print(f"Payload: {payload}\n")



    if not is_repeat:
        # ========== One-time job ==========
        trigger = "date"
        trigger_args = {
            "run_date": start_time
        }

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
            trigger = "cron"
            trigger_args.update({
                "hour": start_time.hour,
                "minute": start_time.minute,
                "second": start_time.second,
                "start_date": start_time,
            })

            if repeat.type == "daily":
                pass  # no need to set day_of_week/month/etc
            elif repeat.type == "weekly":
                trigger_args["day_of_week"] = start_time.strftime("%A").lower()
            elif repeat.type == "monthly":
                trigger_args["day"] = start_time.day
            elif repeat.type == "yearly":
                trigger_args["month"] = start_time.month
                trigger_args["day"] = start_time.day

        # ========== Custom patterns ==========
        elif repeat.type == "custom":
            custom = repeat.custom
            frequency = custom.frequency

            if frequency == "daily":
                trigger = "interval"
                trigger_args.update({
                    "days": custom.interval,
                    "start_date": start_time
                })

            elif frequency == "weekly":
                trigger = "cron"
                weekdays = getattr(custom, "weekdays", None)
                if weekdays is None:
                    raise ValueError("Custom weekly schedule must provide 'weekdays'.")
                trigger_args.update({
                    "day_of_week": ",".join(weekdays),
                    "hour": start_time.hour,
                    "minute": start_time.minute,
                    "second": start_time.second,
                    "start_date": start_time
                })

            elif frequency == "monthly":
                trigger = "cron"
                trigger_args.update({
                    "day": start_time.day,
                    "month": f"*/{custom.interval}",
                    "hour": start_time.hour,
                    "minute": start_time.minute,
                    "second": start_time.second,
                    "start_date": start_time
                })

        else:
            raise ValueError("Invalid repeat type")

        # ========== Handle `after_occurrences` ==========
        if end_repeat and end_repeat.mode == "after_occurrences":
            occurrences = end_repeat.occurrences
            # APScheduler doesn't support max_runs natively.
            # You need to implement a run counter in `task_runner`
            # and call `scheduler.remove_job(job_id)` inside it.
            # For now, log a warning:
            print(f"[Warning] You need to track {occurrences} runs for job {task_id} manually.")

            '''
                Idea on how to track occurences:
                1. After getting the JSON, extract the `occurrences` value.
                2. Calculate the end date based on start time and interval.
                3. Store `occurences` count in a database
                4. In `task_runner`, increment the count each time the task runs, and write the count back to the database.
                5.1. When the count reaches `occurrences`, call `scheduler.remove_job(job_id)` to stop the job.
            '''




    # ========== Add the Job ==========
    # Only pass trigger-specific arguments, not as generic kwargs
    if trigger == "date":
        print(f"Scheduling one-time job {task_id} at {start_time}\n")
        print(f"Trigger args: {trigger_args}\n")

        scheduler.add_job(
            func=task_runner,
            trigger=trigger,
            id=task_id,
            name=task_id,
            args=args,
            replace_existing=True,
            run_date=trigger_args.get("run_date"),
        )
    elif trigger == "interval":
        scheduler.add_job(
            func=task_runner,
            trigger=trigger,
            id=task_id,
            name=task_id,
            args=args,
            replace_existing=True,
            days=trigger_args.get("days"),
            start_date=trigger_args.get("start_date"),
            end_date=trigger_args.get("end_date"),
        )
    elif trigger == "cron":
        scheduler.add_job(
            func=task_runner,
            trigger=trigger,
            id=task_id,
            name=task_id,
            args=args,
            replace_existing=True,
            hour=trigger_args.get("hour"),
            minute=trigger_args.get("minute"),
            second=trigger_args.get("second"),
            day_of_week=trigger_args.get("day_of_week"),
            day=trigger_args.get("day"),
            month=trigger_args.get("month"),
            start_date=trigger_args.get("start_date"),
            end_date=trigger_args.get("end_date"),
        )
    else:
        raise ValueError(f"Unknown trigger type: {trigger}")
    



schedule_from_payload(
    TaskSchedulePayload(
        task_id="send_email",
        start_time=datetime.fromisoformat("2025-07-11T08:30:00"),
        is_repeat=False
    )
)