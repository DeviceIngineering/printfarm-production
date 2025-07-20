"""
Custom exceptions for PrintFarm production system.
"""

class PrintFarmException(Exception):
    """Base exception for PrintFarm application."""
    pass

class MoySkladAPIException(PrintFarmException):
    """Exception for МойСклад API errors."""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class SyncException(PrintFarmException):
    """Exception for synchronization errors."""
    pass

class ProductionCalculationException(PrintFarmException):
    """Exception for production calculation errors."""
    pass