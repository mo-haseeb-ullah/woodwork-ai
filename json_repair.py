import json
import re

def repair_and_parse_json(json_str):
    """
    Robust JSON parser that cleans markdown fences, trailing commas, 
    unescaped control characters, and syntax glitches from LLM output.
    """
    if not isinstance(json_str, str):
        return json_str
        
    s = json_str.strip()
    
    # 1. Strip markdown code fences ```json ... ```
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().endswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
        
    # 2. Find outer JSON object boundaries { ... }
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    if first_brace != -1 and last_brace != -1:
        s = s[first_brace:last_brace+1]

    # Attempt 1: Direct standard parse
    try:
        return json.loads(s)
    except Exception as e1:
        err_msg = str(e1)
        print(f"Standard JSON parse failed ({err_msg}). Attempting auto-repair...")

    # Attempt 2: Remove trailing commas before } or ]
    s_fixed = re.sub(r',\s*([\}\]])', r'\1', s)
    try:
        return json.loads(s_fixed)
    except Exception:
        pass

    # Attempt 3: Fix unescaped newlines inside string literals
    def replace_literal_newlines(match):
        content = match.group(0)
        return content.replace('\n', '\\n').replace('\r', '\\r')
        
    s_fixed2 = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', replace_literal_newlines, s_fixed)
    try:
        return json.loads(s_fixed2)
    except Exception:
        pass

    # Attempt 4: Clean single quotes / curly quotes
    s_fixed3 = s_fixed2.replace("“", '"').replace("”", '"').replace("’", "'")
    s_fixed3 = re.sub(r'(?<=[{,\s])\'([a-zA-Z0-9_]+)\'\s*:', r'"\1":', s_fixed3)
    try:
        return json.loads(s_fixed3)
    except Exception:
        pass

    # Attempt 5: Truncation recovery - if JSON was cut off near the end, close open arrays/objects
    open_braces = s_fixed3.count('{') - s_fixed3.count('}')
    open_brackets = s_fixed3.count('[') - s_fixed3.count(']')
    
    s_truncated = s_fixed3.rstrip()
    if s_truncated.endswith(','):
        s_truncated = s_truncated[:-1]
        
    s_truncated += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
    try:
        return json.loads(s_truncated)
    except Exception:
        pass

    # If all repairs fail, raise error with helpful context
    return json.loads(s)
