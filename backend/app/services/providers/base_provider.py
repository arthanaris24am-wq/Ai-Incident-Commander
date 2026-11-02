from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Base interface for all modular remediation providers.
    """
    
    @property
    @abstractmethod
    def supported_actions(self) -> list:
        """
        Return a list of action types supported by this provider.
        """
        pass

    @abstractmethod
    def execute(self, action_type: str, target: str, **kwargs) -> dict:
        """
        Execute the remediation action.
        Must return a dict: {"success": bool, "message": str}
        """
        pass
