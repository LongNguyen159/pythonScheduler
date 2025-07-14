from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Union, Dict, Any
from datetime import datetime






# ========== End Repeat ==========
class EndRepeatNever(BaseModel):
    mode: Literal["never"]

class EndRepeatOnDate(BaseModel):
    mode: Literal["on_date"]
    until: datetime

class EndRepeatAfterOccurrences(BaseModel):
    mode: Literal["after_occurrences"]
    occurrences: int

EndRepeat = Union[EndRepeatNever, EndRepeatOnDate, EndRepeatAfterOccurrences]

# ========== Custom Repeats ==========

class CustomDaily(BaseModel):
    frequency: Literal["daily"]
    interval: int = Field(..., gt=0, description="Every X days")

class CustomWeekly(BaseModel):
    frequency: Literal["weekly"]
    interval: int = Field(..., gt=0, description="Every X weeks")
    weekdays: List[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]]

class CustomMonthly(BaseModel):
    frequency: Literal["monthly"]
    interval: int = Field(..., gt=0, description="Every X months")

CustomRepeat = Union[CustomDaily, CustomWeekly, CustomMonthly]

# ========== Repeat Block ==========

class RepeatSimple(BaseModel):
    type: Literal["daily", "weekly", "monthly", "yearly"]

class RepeatCustom(BaseModel):
    type: Literal["custom"]
    custom: CustomRepeat

Repeat = Union[RepeatSimple, RepeatCustom]

# ========== Main Scheduler Payload ==========

class TaskSchedulePayload(BaseModel):
    task_id: str
    start_time: datetime
    is_repeat: bool = False
    repeat: Optional[Repeat] = None
    end_repeat: Optional[EndRepeat] = None
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

    @model_validator(mode="after")
    def validate_repeat_logic(self):
        is_repeat = self.is_repeat
        repeat = self.repeat
        end_repeat = self.end_repeat

        if is_repeat and not repeat:
            raise ValueError("`repeat` must be provided if `is_repeat` is True.")
        
        # if not is_repeat and repeat:
        #     raise ValueError("`repeat` must be omitted if `is_repeat` is False.")
        # if not is_repeat and end_repeat:
        #     raise ValueError("`end_repeat` must be omitted if `is_repeat` is False.")
        return self
