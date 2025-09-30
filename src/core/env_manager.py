from typing import Optional

ENV_FOLDER: str = "."


class EnvManager:
    """
    A class to manage environment variables.
    """

    @staticmethod
    def get_env_variable(name: str, default: Optional[str] = None) -> str:
        """
        Get an environment variable by name, with an optional default value.

        :param name: The name of the environment variable.
        :param default: The default value if the environment variable is not set.
        :return: The value of the environment variable or the default value.
        """
        from dotenv import load_dotenv
        import os

        # Load environment variables from .env file
        load_dotenv(os.path.join(os.getcwd(), ENV_FOLDER, ".env"))
        value = os.getenv(name, default)
        return value if value is not None else (default if default is not None else "")
