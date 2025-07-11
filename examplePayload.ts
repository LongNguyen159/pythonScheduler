

const oneTimeJob = {
  "task_id": "send_email",
  "start_time": "2025-07-11T08:30:00",
  "is_repeat": false,
}

const repeatDailyNeverEnds = {
  "task_id": "daily_report",
  "start_time": "2025-07-11T08:30:00",
  "is_repeat": true,
  "repeat": {
    "type": "daily"
  },
  "end_repeat": {
    "mode": "never"
  }
}

const repeatWeeklyOnDateEndsAfter10Occurrences = {
  "task_id": "weekly_reminder",
  "start_time": "2025-07-11T08:30:00",
  "is_repeat": true,
  "repeat": {
    "type": "custom",
    "custom": {
      "frequency": "weekly",
      "interval": 2,
      "weekdays": ["monday", "wednesday"]
    }
  },
  "end_repeat": {
    "mode": "after_occurrences",
    "occurrences": 10
  }
}
