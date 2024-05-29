from dotenv import dotenv_values
from typing import Dict, Optional


class ParticipantEnvLoader:
    __slots__ = ('env_vars',)

    def __init__(self, env_file: str = ".env") -> None:
        self.env_vars: Dict[str, str] = dotenv_values(env_file)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get the value of a variable from the .env file.
        If the variable is not found, return the default value (if provided).
        """
        return self.env_vars.get(key, default)

    def load(self) -> Dict[str, str]:
        """
        Load all the variables from the .env file.
        """
        return self.env_vars


"""
---------> Use case of above class

# Example usage:
# Initialize the EnvLoader with your .env file
env_loader = EnvLoader()

# Load all the variables from the .env file
env_vars = env_loader.load()

# Get the value of a specific variable
print(env_loader.get("INTERESTS_URL"))
"""
