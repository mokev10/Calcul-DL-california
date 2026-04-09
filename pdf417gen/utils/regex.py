import re
from typing import Optional

class Regex:
    def first_match(self, pattern: str, data: str) -> Optional[str]:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            m = regex.search(data)
            if not m or m.lastindex is None:
                return None
            group = m.group(1).strip()
            return group if group else None
        except re.error:
            return None
