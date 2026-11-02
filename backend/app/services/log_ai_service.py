import os


class LogAIService:

    RULES = {

        "MYSQL": {
            "severity": "HIGH",
            "confidence": 95,
            "cause": "Database connection failure",
            "actions": [
                "Verify MySQL service",
                "Check DB credentials",
                "Restart database"
            ]
        },

        "CONNECTION LOST": {
            "severity": "HIGH",
            "confidence": 94,
            "cause": "Network connectivity problem",
            "actions": [
                "Check network",
                "Verify firewall",
                "Ping database server"
            ]
        },

        "DOCKER": {
            "severity": "MEDIUM",
            "confidence": 90,
            "cause": "Docker related issue",
            "actions": [
                "Inspect Docker logs",
                "Restart container",
                "Check Docker daemon"
            ]
        },

        "ERROR": {
            "severity": "MEDIUM",
            "confidence": 85,
            "cause": "Application error",
            "actions": [
                "Inspect logs",
                "Check stack trace"
            ]
        },

        "WARNING": {
            "severity": "LOW",
            "confidence": 70,
            "cause": "Potential issue detected",
            "actions": [
                "Monitor system"
            ]
        }
    }

    @staticmethod
    def analyze_log(message):

        text = message.upper()

        for keyword, data in LogAIService.RULES.items():

            if keyword in text:

                return {
                    "severity": data["severity"],
                    "confidence": data["confidence"],
                    "root_cause": data["cause"],
                    "recommended_actions": data["actions"]
                }

        return {
            "severity": "LOW",
            "confidence": 50,
            "root_cause": "Unknown issue",
            "recommended_actions": [
                "Review complete log"
            ]
        }