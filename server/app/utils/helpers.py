 from datetime import datetime


 def format_timestamp(ts: datetime | str | None = None) -> str:
     if ts is None:
         ts = datetime.now()
     if isinstance(ts, str):
         ts = datetime.fromisoformat(ts)
     now = datetime.now()
     diff = (now - ts).days
     if diff == 0:
         return ts.strftime("%H:%M")
     elif diff == 1:
         return "昨天"
     elif diff < 7:
         return f"{diff}天前"
     else:
         return ts.strftime("%m/%d")


 def truncate_text(text: str, max_length: int = 100) -> str:
     if len(text) <= max_length:
         return text
     return text[:max_length].rsplit(" ", 1)[0] + "..."
