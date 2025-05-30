#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
import hashlib
import tempfile
import re
from typing import Optional, Callable, Any, Tuple, Union, Dict

# Custom exceptions for better error handling
class KatoolinError(Exception):
    """Base exception class for Katoolin errors"""
    def __init__(self, message: str, details: Optional[str] = None, suggestion: Optional[str] = None):
        """
        Initialize the exception with a message, optional details, and suggestion.

        Args:
            message (str): The main error message
            details (Optional[str]): Additional details about the error
            suggestion (Optional[str]): Suggestion for how to resolve the error
        """
        self.message = message
        self.details = details
        self.suggestion = suggestion

        # Construct the full error message
        full_message = message
        if details:
            full_message += f"\nDetails: {details}"
        if suggestion:
            full_message += f"\nSuggestion: {suggestion}"

        super().__init__(full_message)

        # Log the error
        logging.error(f"{self.__class__.__name__}: {message}")
        if details:
            logging.debug(f"Error details: {details}")

class RepositoryError(KatoolinError):
    """Exception raised for repository-related errors"""
    pass

class ToolInstallationError(KatoolinError):
    """Exception raised for tool installation errors"""
    pass

class PermissionError(KatoolinError):
    """Exception raised for permission-related errors"""
    pass

class FileOperationError(KatoolinError):
    """Exception raised for file operation errors"""
    pass

class NetworkError(KatoolinError):
    """Exception raised for network-related errors"""
    pass

class PluginError(KatoolinError):
    """Exception raised for plugin-related errors"""
    pass

class UserInputError(KatoolinError):
    """Exception raised for invalid user input"""
    pass

class ConfigurationError(KatoolinError):
    """Exception raised for configuration-related errors"""
    pass

class DependencyError(KatoolinError):
    """Exception raised for dependency-related errors"""
    pass

class SecurityError(KatoolinError):
    """Exception raised for security-related errors"""
    pass

# Define color constants for terminal output
class Colors:
    """
    Class containing color constants for terminal output
    """
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[33m"
    CYAN = "\033[1;36m"
    RESET = "\033[0m"

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration

    Args:
        log_level (int): Logging level (default: logging.INFO)
        log_file (Optional[str]): Path to log file (default: None, logs to console only)
    """
    # Create logger
    logger = logging.getLogger('katoolin')
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent logging from propagating to the root logger
    logger.propagate = False

    logging.info("Logging initialized")

def sanitize_command(command: str) -> str:
    """
    Sanitize a command to prevent command injection

    Args:
        command (str): The command to sanitize

    Returns:
        str: The sanitized command

    Raises:
        SecurityError: If the command contains potentially dangerous patterns
    """
    # Check for common shell injection patterns
    dangerous_patterns = [
        ';', '&&', '||',                # Command chaining
        '`', '$(', '${',                # Command substitution
        '>', '>>', '<',                 # Redirection
        '|',                            # Pipe
        'rm -rf /', 'rm -rf /*',        # Very dangerous commands
        'mkfs', 'dd if=/dev/zero',      # Disk formatting
        ':(){:|:&};:',                  # Fork bomb
        '/etc/passwd', '/etc/shadow'    # Sensitive files
    ]

    for pattern in dangerous_patterns:
        if pattern in command:
            error_msg = f"Command contains potentially dangerous pattern: {pattern}"
            logging.warning(error_msg)
            raise SecurityError(
                message=error_msg,
                details=f"The pattern '{pattern}' could be used for command injection",
                suggestion="Please review the command for security issues"
            )

    return command

def run_command(command: str, capture_output: bool = False, 
                check_security: bool = True) -> Union[int, Tuple[int, str, str]]:
    """
    Run a shell command and return the exit code and optionally the output

    Args:
        command (str): The command to run
        capture_output (bool): Whether to capture and return stdout/stderr
        check_security (bool): Whether to check the command for security issues

    Returns:
        Union[int, Tuple[int, str, str]]: 
            If capture_output is False: The exit code of the command
            If capture_output is True: Tuple of (exit_code, stdout, stderr)

    Raises:
        SecurityError: If the command contains potentially dangerous patterns and check_security is True
    """
    try:
        # Sanitize the command if security checking is enabled
        if check_security:
            command = sanitize_command(command)

        logging.debug(f"Running command: {command}")

        if capture_output:
            # Use subprocess.run to capture output
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            if result.returncode != 0:
                logging.warning(f"Command failed with exit code {result.returncode}: {command}")
                logging.debug(f"stderr: {stderr}")
            else:
                logging.debug(f"Command succeeded: {command}")

            return result.returncode, stdout, stderr
        else:
            # Use subprocess.run without capturing output for better security
            result = subprocess.run(
                command,
                shell=True,
                check=False
            )
            exit_code = result.returncode

            if exit_code != 0:
                logging.warning(f"Command failed with exit code {exit_code}: {command}")
            else:
                logging.debug(f"Command succeeded: {command}")

            return exit_code
    except SecurityError:
        # Re-raise security errors
        raise
    except Exception as e:
        error_msg = f"Error executing command '{command}': {str(e)}"
        logging.error(error_msg)
        if capture_output:
            return 1, "", str(e)
        return 1

def check_root() -> bool:
    """
    Check if the script is running with root privileges

    Returns:
        bool: True if running as root, False otherwise

    Raises:
        PermissionError: If the script is not running with root privileges
    """
    if os.geteuid() != 0:
        error_msg = "You need to have root privileges to run this script. Please try again using 'sudo'."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}{Colors.RESET}")
        raise PermissionError(error_msg)

    logging.debug("Running with root privileges")
    return True

def format_category_name(category_name: str) -> str:
    """
    Format a category name for display

    Args:
        category_name (str): Name of the category

    Returns:
        str: Formatted category name
    """
    category_name = category_name.replace('_', ' ')
    return category_name.title()

def validate_input(user_input: str, allowed_chars: str = None, disallowed_chars: str = None, 
                max_length: int = None, pattern: str = None) -> str:
    """
    Validate and sanitize user input to prevent command injection

    Args:
        user_input (str): The input to validate
        allowed_chars (str, optional): String of allowed characters. If provided, only these characters will be allowed.
        disallowed_chars (str, optional): String of disallowed characters. If provided, these characters will be removed.
        max_length (int, optional): Maximum allowed length of the input.
        pattern (str, optional): Regex pattern that the input must match.

    Returns:
        str: The sanitized input

    Raises:
        UserInputError: If the input is invalid
    """
    # Check if input is empty
    if not user_input:
        return user_input

    # Check max length
    if max_length and len(user_input) > max_length:
        error_msg = f"Input exceeds maximum length of {max_length} characters"
        logging.warning(error_msg)
        raise UserInputError(
            message=error_msg,
            suggestion=f"Please limit your input to {max_length} characters"
        )

    # Check against pattern
    if pattern:
        import re
        if not re.match(pattern, user_input):
            error_msg = "Input contains invalid characters or format"
            logging.warning(error_msg)
            raise UserInputError(
                message=error_msg,
                suggestion=f"Input must match the pattern: {pattern}"
            )

    # Filter based on allowed characters
    if allowed_chars:
        sanitized = ''.join(c for c in user_input if c in allowed_chars)
        if sanitized != user_input:
            logging.warning(f"Input contained disallowed characters: {set(user_input) - set(sanitized)}")
            user_input = sanitized

    # Remove disallowed characters
    if disallowed_chars:
        sanitized = ''.join(c for c in user_input if c not in disallowed_chars)
        if sanitized != user_input:
            logging.warning(f"Input contained disallowed characters: {set(user_input) - set(sanitized)}")
            user_input = sanitized

    # Check for common shell injection patterns
    dangerous_patterns = [
        ';', '&&', '||', '`', '$(',  # Command chaining
        '>', '>>', '<',               # Redirection
        '|',                          # Pipe
        'rm -rf', 'wget', 'curl',     # Dangerous commands
        '/etc/passwd', '/etc/shadow'  # Sensitive files
    ]

    for pattern in dangerous_patterns:
        if pattern in user_input:
            error_msg = f"Input contains potentially dangerous pattern: {pattern}"
            logging.warning(error_msg)
            raise UserInputError(
                message=error_msg,
                details=f"The pattern '{pattern}' could be used for command injection",
                suggestion="Please remove special characters and shell commands from your input"
            )

    return user_input

def safe_input(prompt: str, default: Optional[str] = None, 
               allowed_chars: str = None, disallowed_chars: str = None,
               max_length: int = None, pattern: str = None) -> str:
    """
    Safely get input from the user, handling KeyboardInterrupt and validating input

    Args:
        prompt (str): The prompt to display
        default (Optional[str]): Default value to return if KeyboardInterrupt is caught
        allowed_chars (str, optional): String of allowed characters. If provided, only these characters will be allowed.
        disallowed_chars (str, optional): String of disallowed characters. If provided, these characters will be removed.
        max_length (int, optional): Maximum allowed length of the input.
        pattern (str, optional): Regex pattern that the input must match.

    Returns:
        str: The validated user input or default value

    Raises:
        UserInputError: If there's an error getting input from the user or the input is invalid
    """
    try:
        logging.debug(f"Requesting user input with prompt: {prompt}")
        user_input = input(prompt)
        logging.debug(f"Received user input: {user_input}")

        # Validate and sanitize the input
        validated_input = validate_input(
            user_input, 
            allowed_chars=allowed_chars,
            disallowed_chars=disallowed_chars,
            max_length=max_length,
            pattern=pattern
        )

        if validated_input != user_input:
            logging.info(f"Input was sanitized from '{user_input}' to '{validated_input}'")
            print(f"{Colors.YELLOW}Note: Your input was sanitized for security reasons.{Colors.RESET}")

        return validated_input
    except KeyboardInterrupt:
        message = "Operation cancelled by user."
        logging.info(message)
        print(f"\n{message}")
        if default is not None:
            logging.debug(f"Using default value: {default}")
        return default if default is not None else ""
    except EOFError as e:
        error_msg = "Error reading input from user"
        logging.error(f"{error_msg}: {str(e)}")
        raise UserInputError(
            message=error_msg,
            details=str(e),
            suggestion="Try again or check your terminal settings"
        ) from e

def safe_exit(exit_code: int = 0, message: Optional[str] = None) -> None:
    """
    Safely exit the program with an optional message

    Args:
        exit_code (int): The exit code to use
        message (Optional[str]): Optional message to display before exiting
    """
    if message:
        logging.info(f"Exiting with message: {message}")
        print(message)
    else:
        logging.info(f"Exiting with code: {exit_code}")

    sys.exit(exit_code)

def with_error_handling(func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[Exception]]:
    """
    Execute a function with error handling

    Args:
        func (Callable): The function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Tuple[bool, Any, Optional[Exception]]: 
            - bool: True if the function executed successfully, False otherwise
            - Any: The return value of the function or None if an exception occurred
            - Optional[Exception]: The exception that was caught, or None if no exception occurred
    """
    try:
        logging.debug(f"Executing function: {func.__name__}")
        result = func(*args, **kwargs)
        logging.debug(f"Function {func.__name__} executed successfully")
        return True, result, None
    except KatoolinError as e:
        # These errors have already been logged
        logging.debug(f"Caught KatoolinError in with_error_handling: {str(e)}")

        # Display error message with details and suggestion if available
        error_msg = e.message
        if hasattr(e, 'details') and e.details:
            error_msg += f"\nDetails: {e.details}"
        if hasattr(e, 'suggestion') and e.suggestion:
            error_msg += f"\nSuggestion: {e.suggestion}"

        print(f"{Colors.RED}{error_msg}{Colors.RESET}")
        return False, None, e
    except PermissionError as e:
        error_msg = f"Permission denied: {str(e)}"
        suggestion = "Try running the command with sudo or as root."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False, None, e
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        suggestion = "Check if the file exists and the path is correct."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False, None, e
    except IOError as e:
        error_msg = f"IO error: {str(e)}"
        suggestion = "Check if you have the necessary permissions and if the disk has enough space."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False, None, e
    except ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        suggestion = "Check your internet connection and try again."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False, None, e
    except Exception as e:
        error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
        suggestion = "Please report this issue with the details below."
        details = traceback.format_exc()
        logging.error(error_msg)
        logging.debug(f"Exception details:\n{details}")
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False, None, e

def read_file(file_path: str) -> Optional[str]:
    """
    Read the contents of a file

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[str]: Contents of the file or None if an error occurred

    Raises:
        FileOperationError: If the file cannot be read
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            logging.debug(f"Successfully read file: {file_path}")
            return content
    except FileNotFoundError as e:
        error_msg = f"File not found: {file_path}"
        suggestion = "Check if the file exists and the path is correct."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        raise FileOperationError(
            message=error_msg,
            details=str(e),
            suggestion=suggestion
        ) from e
    except PermissionError as e:
        error_msg = f"Permission denied when reading file: {file_path}"
        suggestion = "Check if you have the necessary permissions to read the file."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        raise FileOperationError(
            message=error_msg,
            details=str(e),
            suggestion=suggestion
        ) from e
    except IOError as e:
        error_msg = f"IO error when reading file {file_path}: {str(e)}"
        suggestion = "Check if the file is accessible and not corrupted."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        raise FileOperationError(
            message=error_msg,
            details=str(e),
            suggestion=suggestion
        ) from e
    except Exception as e:
        error_msg = f"Unexpected error reading file {file_path}: {str(e)}"
        suggestion = "This is an unexpected error. Please report this issue."
        details = traceback.format_exc()
        logging.error(error_msg)
        logging.debug(f"Exception details:\n{details}")
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return None

def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file

    Args:
        file_path (str): Path to the file
        content (str): Content to write

    Returns:
        bool: True if successful, False otherwise

    Raises:
        FileOperationError: If the file cannot be written
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.debug(f"Created directory: {directory}")
            except PermissionError as e:
                error_msg = f"Permission denied when creating directory: {directory}"
                suggestion = "Check if you have the necessary permissions to create directories."
                logging.error(error_msg)
                print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
                raise FileOperationError(
                    message=error_msg,
                    details=str(e),
                    suggestion=suggestion
                ) from e
            except OSError as e:
                error_msg = f"Error creating directory {directory}: {str(e)}"
                suggestion = "Check if the path is valid and you have the necessary permissions."
                logging.error(error_msg)
                print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
                raise FileOperationError(
                    message=error_msg,
                    details=str(e),
                    suggestion=suggestion
                ) from e

        with open(file_path, 'w') as file:
            file.write(content)

        logging.debug(f"Successfully wrote to file: {file_path}")
        return True
    except PermissionError as e:
        error_msg = f"Permission denied when writing to file: {file_path}"
        suggestion = "Check if you have the necessary permissions to write to the file."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        raise FileOperationError(
            message=error_msg,
            details=str(e),
            suggestion=suggestion
        ) from e
    except IOError as e:
        error_msg = f"IO error when writing to file {file_path}: {str(e)}"
        suggestion = "Check if the disk has enough space and the file is not being used by another process."
        logging.error(error_msg)
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        raise FileOperationError(
            message=error_msg,
            details=str(e),
            suggestion=suggestion
        ) from e
    except Exception as e:
        error_msg = f"Unexpected error writing to file {file_path}: {str(e)}"
        suggestion = "This is an unexpected error. Please report this issue."
        details = traceback.format_exc()
        logging.error(error_msg)
        logging.debug(f"Exception details:\n{details}")
        print(f"{Colors.RED}{error_msg}\nSuggestion: {suggestion}{Colors.RESET}")
        return False

def clear_screen() -> None:
    """
    Clear the terminal screen
    """
    os.system('clear')

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify the checksum of a file

    Args:
        file_path (str): Path to the file to verify
        expected_checksum (str): Expected checksum value
        algorithm (str): Hash algorithm to use (default: sha256)

    Returns:
        bool: True if the checksum matches, False otherwise

    Raises:
        FileOperationError: If there's an error reading the file
        SecurityError: If the checksum verification fails
    """
    logging.info(f"Verifying {algorithm} checksum for file: {file_path}")

    try:
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise FileOperationError(
                message=error_msg,
                suggestion="Check if the file exists and the path is correct"
            )

        # Calculate the checksum
        hash_obj = getattr(hashlib, algorithm)()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)

        calculated_checksum = hash_obj.hexdigest()
        logging.debug(f"Calculated {algorithm} checksum: {calculated_checksum}")
        logging.debug(f"Expected {algorithm} checksum: {expected_checksum}")

        if calculated_checksum.lower() != expected_checksum.lower():
            error_msg = f"Checksum verification failed for {file_path}"
            details = f"Expected: {expected_checksum}\nCalculated: {calculated_checksum}"
            logging.error(f"{error_msg}\n{details}")
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise SecurityError(
                message=error_msg,
                details=details,
                suggestion="The file may have been tampered with or corrupted during download"
            )

        logging.info(f"Checksum verification successful for {file_path}")
        return True

    except FileOperationError:
        # Already logged and raised
        raise
    except SecurityError:
        # Already logged and raised
        raise
    except Exception as e:
        error_msg = f"Error verifying checksum for {file_path}: {str(e)}"
        logging.error(error_msg)
        print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
        return False

def verify_gpg_key(key_path: str, fingerprint: Optional[str] = None) -> bool:
    """
    Verify a GPG key

    Args:
        key_path (str): Path to the GPG key file
        fingerprint (Optional[str]): Expected fingerprint of the key

    Returns:
        bool: True if the key is valid and trusted, False otherwise

    Raises:
        FileOperationError: If there's an error reading the key file
        SecurityError: If the key verification fails
    """
    logging.info(f"Verifying GPG key: {key_path}")

    try:
        if not os.path.exists(key_path):
            error_msg = f"Key file not found: {key_path}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise FileOperationError(
                message=error_msg,
                suggestion="Check if the key file exists and the path is correct"
            )

        # Get key information
        cmd = f"gpg --with-fingerprint --with-colons {key_path}"
        result, stdout, stderr = run_command(cmd, capture_output=True)

        if result != 0:
            error_msg = f"Error getting key information: {stderr}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise SecurityError(
                message=error_msg,
                suggestion="Check if the key file is valid"
            )

        # Extract fingerprint from output
        key_info = {}
        for line in stdout.splitlines():
            if line.startswith('fpr:'):
                key_info['fingerprint'] = line.split(':')[9]
            elif line.startswith('pub:'):
                key_info['key_id'] = line.split(':')[4]
                key_info['creation_date'] = line.split(':')[5]
                key_info['expiration_date'] = line.split(':')[6]

        if 'fingerprint' not in key_info:
            error_msg = "Could not extract fingerprint from key"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise SecurityError(
                message=error_msg,
                suggestion="The key file may be invalid or corrupted"
            )

        logging.debug(f"Key information: {key_info}")

        # Verify fingerprint if provided
        if fingerprint and key_info['fingerprint'].lower() != fingerprint.lower().replace(' ', ''):
            error_msg = "Key fingerprint verification failed"
            details = f"Expected: {fingerprint}\nFound: {key_info['fingerprint']}"
            logging.error(f"{error_msg}\n{details}")
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise SecurityError(
                message=error_msg,
                details=details,
                suggestion="The key may have been tampered with or is not the expected key"
            )

        logging.info(f"GPG key verification successful for {key_path}")
        return True

    except FileOperationError:
        # Already logged and raised
        raise
    except SecurityError:
        # Already logged and raised
        raise
    except Exception as e:
        error_msg = f"Error verifying GPG key {key_path}: {str(e)}"
        logging.error(error_msg)
        print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
        return False

def display_progress(current: int, total: int, prefix: str = '', suffix: str = '', length: int = 50, fill: str = '█') -> None:
    """
    Display a progress bar in the terminal

    Args:
        current (int): Current progress value
        total (int): Total value
        prefix (str): Prefix string
        suffix (str): Suffix string
        length (int): Bar length
        fill (str): Bar fill character
    """
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')

    # Print new line on complete
    if current == total:
        print()

def display_spinner(message: str, duration: float) -> None:
    """
    Display a spinner animation for a specified duration

    Args:
        message (str): Message to display alongside the spinner
        duration (float): Duration in seconds
    """
    import time
    import itertools
    import threading
    import sys

    spinner = itertools.cycle(['|', '/', '-', '\\'])

    def spin():
        for _ in range(int(duration * 10)):  # Update spinner 10 times per second
            sys.stdout.write(f'\r{message} {next(spinner)}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write(f'\r{message} Done!   \n')

    threading.Thread(target=spin).start()

def download_and_verify_key(key_url: str, output_path: str, fingerprint: Optional[str] = None) -> bool:
    """
    Download and verify a GPG key

    Args:
        key_url (str): URL of the GPG key
        output_path (str): Path to save the key
        fingerprint (Optional[str]): Expected fingerprint of the key

    Returns:
        bool: True if the key is valid and trusted, False otherwise

    Raises:
        NetworkError: If there's an error downloading the key
        SecurityError: If the key verification fails
    """
    logging.info(f"Downloading and verifying GPG key from {key_url}")

    try:
        # Create a temporary file for the key
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Download the key
        cmd = f"wget -q -O {temp_path} {key_url}"
        result = run_command(cmd)

        if result != 0:
            error_msg = f"Error downloading key from {key_url}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise NetworkError(
                message=error_msg,
                suggestion="Check your internet connection and the key URL"
            )

        # Verify the key
        if verify_gpg_key(temp_path, fingerprint):
            # Move the key to the output path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            os.rename(temp_path, output_path)
            logging.info(f"Key saved to {output_path}")
            return True
        else:
            os.remove(temp_path)
            return False

    except NetworkError:
        # Already logged and raised
        raise
    except SecurityError:
        # Already logged and raised
        raise
    except Exception as e:
        error_msg = f"Error downloading and verifying key from {key_url}: {str(e)}"
        logging.error(error_msg)
        print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
