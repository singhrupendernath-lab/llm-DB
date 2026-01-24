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
