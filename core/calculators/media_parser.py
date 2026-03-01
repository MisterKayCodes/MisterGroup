# Made by Mister 💛
import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

class MediaParser:
    """The 'Brain' (core/calculators/). Pure logic for media tags and range parsing."""
    
    @staticmethod
    def parse_category_ranges(text: str) -> Dict[str, List[List[int]]]:
        """Parse CATEGORY: 0-20 format."""
        categories = {}
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or ':' not in line: continue
            try:
                name, ranges_str = line.split(':', 1)
                name = name.strip().upper()
                ranges = []
                for part in ranges_str.split(','):
                    part = part.strip()
                    if '-' in part:
                        p = part.split('-')
                        if len(p) == 2: ranges.append([int(p[0]), int(p[1])])
                    else:
                        idx = int(part)
                        ranges.append([idx, idx])
                if ranges: categories[name] = ranges
            except: continue
        return categories

    @staticmethod
    def extract_tags(content: str) -> List[str]:
        """Find [TAG] in text."""
        return [m.upper() for m in re.findall(r'\[([A-Za-z_]+)\]', content)]

    @staticmethod
    def remove_tags(content: str) -> str:
        """Clean [TAG] from text for captions."""
        return re.sub(r'\s*\[[A-Za-z_]+\]\s*', ' ', content).strip()

    @staticmethod
    def format_ranges(ranges: List[List[int]]) -> str:
        """Convert [[0,2]] to '0-2'."""
        return ", ".join([f"{r[0]}-{r[1]}" if r[0] != r[1] else str(r[0]) for r in ranges])
