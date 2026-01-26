import json
import os
import re

class ReportsManager:
    def __init__(self, filepath="reports.json"):
        self.filepath = filepath
        self.reports = self.load_reports()

    def load_reports(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading reports: {e}")
            return {}

    def find_report_id(self, text):
        # Look for report IDs (e.g., AT1201) in the text
        for report_id in self.reports.keys():
            if re.search(rf"\b{report_id}\b", text, re.IGNORECASE):
                return report_id
        return None

    def extract_parameters(self, text):
        params = {}
        # Extract dates (YYYY-MM-DD)
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if dates:
            params["date"] = dates[0]
            if len(dates) > 1:
                params["start_date"] = dates[0]
                params["end_date"] = dates[1]

        # Extract numbers for ranges or single values
        numbers = re.findall(r"\d+", text)
        if numbers:
            params["value"] = numbers[0]
            params["class_id"] = numbers[0]
            params["teacher_id"] = numbers[0]
            params["student_id"] = numbers[0]
            if len(numbers) > 1:
                params["min_value"] = numbers[0]
                params["max_value"] = numbers[1]
                params["min_balance"] = numbers[0]
                params["max_balance"] = numbers[1]

        return params

    def format_query(self, report_id, user_text):
        report = self.get_report(report_id)
        if not report:
            return None

        clean_text = re.sub(rf"\b{report_id}\b", "", user_text, flags=re.IGNORECASE)
        query = report["query"]
        params = self.extract_parameters(clean_text)

        for key, val in params.items():
            # Placeholders can be :key or {key}

            # Heuristic for replacement
            is_pure_int = val.isdigit()
            replacement = val if is_pure_int else f"'{val}'"

            # 1. Replace colon placeholders :key
            # Use \b to ensure we don't match :key_something
            query = re.sub(rf"':{key}\b'", f"'{val}'", query)
            query = re.sub(rf'":{key}\b"', f"'{val}'", query)
            query = re.sub(rf"(?<!['\"]):{key}\b(?!['\"])", replacement, query)

            # 2. Replace brace placeholders {key}
            # Braces are usually literal in this context, escape them for regex
            query = query.replace(f"'{{{key}}}'", f"'{val}'")
            query = query.replace(f'"{{{key}}}"', f"'{val}'")
            # For unquoted braces, just replace directly (no \b needed usually for braces)
            pattern_unquoted = rf"(?<!['\"])\{{{key}\}}(?!['\"])"
            query = re.sub(pattern_unquoted, replacement, query)

        return query

    def get_missing_variables(self, report_id, user_text):
        report = self.get_report(report_id)
        if not report:
            return []

        query = report["query"]
        # Convert :var to {var} for uniform variable finding
        temp_query = re.sub(r":(\w+)", r"{\1}", query)

        # Find all required variables in {var} format
        required_vars = list(set(re.findall(r"\{(\w+)\}", temp_query)))

        clean_text = re.sub(rf"\b{report_id}\b", "", user_text, flags=re.IGNORECASE)
        params = self.extract_parameters(clean_text)

        missing = [v for v in required_vars if v not in params]
        return missing

    def get_report(self, report_id):
        return self.reports.get(report_id)

    def log_execution(self, report_id, query, log_file="report_execution.log"):
        from datetime import datetime
        report = self.get_report(report_id)
        report_name = report["name"] if report else "Unknown"

        log_entry = (
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Report ID: {report_id}\n"
            f"Report Name: {report_name}\n"
            f"Query: {query}\n"
            f"{'-'*40}\n"
        )

        try:
            with open(log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging report execution: {e}")
