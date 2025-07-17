
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from datetime import datetime
from features.schema import (
    TaskExecutionSettings,
    EndRepeatMode,
    RepeatType,
    Repeat,
    EndRepeat,
    JobResponse,
    PayloadType,
    SimpleConfig,
    ExpertConfig
)
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from typing import List, cast, Optional, Any, Dict
import pytz

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def to_utc(self, dt: datetime) -> datetime:
        '''Helper function: Convert a datetime to UTC timezone.'''
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(pytz.UTC)

    def _schedule_job(self, payload: TaskExecutionSettings, task_to_execute_callback: Any, args: Optional[Any] = None, kwargs: Optional[Dict[str, Any]] = None) -> Job | None:
        if payload.task_id is None:
            raise ValueError("task_id must not be None")
        task_id: str = payload.task_id
        task_name: Optional[str] = payload.task_name
        schedule_config: SimpleConfig | ExpertConfig = payload.task_config

        if schedule_config.mode == PayloadType.EXPERT:
            ''' Expert mode: CRON string scheduling '''
            expert_config = cast(ExpertConfig, schedule_config)
            try:

                trigger = CronTrigger.from_crontab(expert_config.cron_string, timezone=pytz.UTC)
                print(f"Scheduling expert-mode CRON job {task_id} with trigger: {trigger}")
                return self.scheduler.add_job(
                    func=task_to_execute_callback,
                    trigger=trigger,
                    id=task_id,
                    name=task_name,
                    args=args,
                    kwargs=kwargs,
                    replace_existing=True,
                )
            except ValueError as e:
                raise ValueError(f"Invalid CRON string: {str(e)}")

        elif schedule_config.mode == PayloadType.SIMPLE:
            ''' Simple mode: Time-based scheduling with triggers and repeat logic '''
            simple_config = cast(SimpleConfig, schedule_config)
            start_time: datetime = self.to_utc(simple_config.start_time)
            repeat: Repeat | None = simple_config.repeat
            end_repeat: EndRepeat | None = simple_config.end_repeat


            # Apply end repeat if provided
            end_date: datetime | None = None
            if end_repeat:
                if end_repeat.mode == EndRepeatMode.ON_DATE and end_repeat.until:
                    end_date = self.to_utc(end_repeat.until)
    

            # One-time job
            if not repeat:
                trigger = DateTrigger(run_date=start_time)
                print(f"Scheduling one-time job {task_id} with trigger: {trigger}\n")
                return self.scheduler.add_job(
                    func=task_to_execute_callback,
                    trigger=trigger,
                    id=task_id,
                    name=task_name,
                    args=args,
                    kwargs=kwargs,
                    replace_existing=True,
                )

            #region Triggers generators
            '''
            Generate the appropriate trigger based on repeat type:
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

                return CalendarIntervalTrigger(
                    weeks=repeat.frequency or 1,
                    start_date=start_time,
                    end_date=end_date,
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=start_time.second,
                    timezone=pytz.UTC,
                )

            def monthly_trigger():
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
            #endregion


            print(f"Scheduling job {task_id} with trigger: {trigger}\n")
            return self.scheduler.add_job(
                func=task_to_execute_callback,
                trigger=trigger,
                id=task_id,
                name=task_name,
                args=args,
                kwargs=kwargs,
                replace_existing=True,
            )


    #region Public methods
    '''
        API methods for scheduling, canceling, and listing jobs.
    '''
    def cancel_job(self, job_id: str):
        '''Cancel a job by its ID. This will remove all future executions of the job.'''
        job = self.scheduler.get_job(job_id)
        if not job:
            raise Exception("Job not found")
        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            raise Exception(f"Scheduler failure: {str(e)}")
        return {"message": f"Job {job_id} canceled successfully"}

    def get_all_jobs(self) -> List[JobResponse]:
        '''
            List all scheduled jobs: their IDs, names, next run times, etc.
        '''
        jobs: List[Job] = self.scheduler.get_jobs()
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

    def get_job_by_id(self, job_id: str) -> JobResponse:
        '''
            Get details of a specific job by its ID.
            Returns job details including ID, name, next run time, etc.
        '''
        job: Job | None = self.scheduler.get_job(job_id)
        if not job:
            raise Exception("Job not found")
        
        return JobResponse(
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
    
    def remove_all_jobs(self):
        '''
            Remove all jobs from the scheduler. No more jobs will be executed after this.
        '''
        try:
            self.scheduler.remove_all_jobs()
            return {"message": "All jobs removed successfully."}
        except Exception as e:
            raise Exception(f"Scheduler failure: {str(e)}")
        

    def schedule_job(self, task_configs: TaskExecutionSettings, callback: Any | None = None, args: Optional[Any] = None, kwargs: Optional[Dict[str, Any]] = None) -> JobResponse | None:
        '''
            Schedule a job based on the provided TaskExecutionSettings.
            Parameters:
                - task_configs: `TaskExecutionSettings` containing task ID, name, and configuration.
                    - Configuration mode: `SimpleConfig` or `ExpertConfig`.
                    - `SimpleConfig`: Contains start_time, end_time, repeat configurations.
                    - `ExpertConfig`: Contains a CRON string for scheduling.

                - callback: Optional callback function to execute when the job runs.
                - args: Optional arguments to pass to the callback function.
                - kwargs: Optional keyword arguments to pass to the callback function.



            Returns a JobResponse type with job details.
        '''
        try:
            job = self._schedule_job(task_configs, task_to_execute_callback=callback, args=args, kwargs=kwargs)
            if not job:
                raise Exception("Failed to schedule job: Job not found.")
            
            # Convert job to response format
            job_details = JobResponse(
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
            return job_details
        except Exception as e:
            raise Exception(f"Failed to schedule job: {str(e)}")
    #endregion
        