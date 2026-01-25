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

        # Remove the report ID from the text to avoid extracting numbers from it
        clean_text = re.sub(rf"\b{report_id}\b", "", user_text, flags=re.IGNORECASE)

        query = report["query"]
        # Support :variable by converting to {variable}
        query = re.sub(r":(\w+)", r"{\1}", query)

        params = self.extract_parameters(clean_text)

        # Try to fill placeholders in the query
        try:
            # We use a default dictionary to avoid KeyError if some params are missing
            # but we should probably only format if we have matches.
            # For now, let's just try to format with what we have.
            formatted_query = query.format(**params)
            return formatted_query
        except KeyError as e:
            # If a required parameter is missing, return original query or handle it
            print(f"Missing parameter for report {report_id}: {e}")
            return query
        except Exception as e:
            print(f"Error formatting query: {e}")
            return query

    def get_missing_variables(self, report_id, user_text):
        report = self.get_report(report_id)
        if not report:
            return []

        query = report["query"]
        # Convert :var to {var}
        query = re.sub(r":(\w+)", r"{\1}", query)

        # Find all required variables in {var} format
        required_vars = list(set(re.findall(r"\{(\w+)\}", query)))

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
