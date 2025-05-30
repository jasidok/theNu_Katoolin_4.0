#!/usr/bin/env python3

import os
import logging
import tempfile
from typing import Optional, List, Dict
from core.utils import (
    Colors, run_command, read_file, write_file, 
    RepositoryError, PermissionError, FileOperationError, NetworkError, SecurityError,
    verify_gpg_key, download_and_verify_key
)

class RepositoryManager:
    """
    Class for managing Kali Linux repositories and custom repositories from plugins
    """
    def __init__(self, plugin_manager=None):
        self.repository_path = "/etc/apt/sources.list.d/katoolin.list"
        self.tmp_key_path = "/tmp/key_katoolin.txt"
        self.plugin_manager = plugin_manager
        self.custom_repositories = []

        # Load custom repositories from plugins if plugin_manager is provided
        if self.plugin_manager:
            self.custom_repositories = self.plugin_manager.get_plugin_repositories()

    def add_repository(self, repository_info: Optional[Dict[str, str]] = None) -> bool:
        """
        Add a repository to sources.list.d
        If repository_info is None, adds the default Kali Linux repository

        Args:
            repository_info (Optional[Dict[str, str]]): Repository information dictionary
                                                      If None, adds the default Kali repository

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RepositoryError: If there's an error adding the repository
            PermissionError: If the script doesn't have permission to add the repository
            FileOperationError: If there's an error writing to the repository file
        """
        # If no repository info is provided, use the default Kali repository
        if repository_info is None:
            logging.info("Adding default Kali Linux repository")

            if os.path.exists(self.repository_path):
                logging.debug(f"Repository file already exists: {self.repository_path}")
                try:
                    self.add_key()
                    return True
                except Exception as e:
                    logging.error(f"Error adding key for existing repository: {str(e)}")
                    raise RepositoryError(f"Error adding key for existing repository: {str(e)}") from e
            else:
                try:
                    logging.debug(f"Creating repository file: {self.repository_path}")
                    content = "#Katoolin\ndeb http://http.kali.org/kali kali-rolling main contrib non-free\n" \
                              "# For source package access, uncomment the following line\n" \
                              "# deb-src http://http.kali.org/kali kali-rolling main contrib non-free\n"

                    if write_file(self.repository_path, content):
                        success_msg = "Repository added successfully"
                        logging.info(success_msg)
                        print(f"{Colors.GREEN}\n[+] {success_msg}\n{Colors.RESET}")
                        self.add_key()
                        return True
                    else:
                        error_msg = "Failed to write repository file"
                        logging.error(error_msg)
                        raise FileOperationError(error_msg)
                except PermissionError as e:
                    error_msg = "Permission denied when adding repository. Please run as root."
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise PermissionError(error_msg) from e
                except FileOperationError as e:
                    # This exception is already logged in write_file
                    raise
                except Exception as e:
                    error_msg = f"Unexpected error adding repository: {str(e)}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise RepositoryError(error_msg) from e
        else:
            # Add custom repository
            try:
                repo_name = repository_info.get('name', 'custom')
                repo_url = repository_info.get('url')
                repo_components = repository_info.get('components', 'main')

                logging.info(f"Adding custom repository: {repo_name}")
                logging.debug(f"Repository URL: {repo_url}, Components: {repo_components}")

                if not repo_url:
                    error_msg = "Repository URL is required"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise RepositoryError(error_msg)

                # Create a unique filename for this repository
                repo_filename = f"/etc/apt/sources.list.d/{repo_name.lower().replace(' ', '_')}.list"
                logging.debug(f"Repository filename: {repo_filename}")

                # Check if repository already exists
                if os.path.exists(repo_filename):
                    warning_msg = f"Repository {repo_name} already exists"
                    logging.warning(warning_msg)
                    print(f"{Colors.YELLOW}{warning_msg}{Colors.RESET}")

                    # Add key if provided
                    if 'key_url' in repository_info or 'key_id' in repository_info:
                        self.add_custom_key(repository_info)

                    return True

                # Create repository file
                content = f"# {repo_name} - Added by Katoolin\n"
                content += f"deb {repo_url} {repo_components}\n"

                if write_file(repo_filename, content):
                    success_msg = f"Repository {repo_name} added successfully"
                    logging.info(success_msg)
                    print(f"{Colors.GREEN}\n[+] {success_msg}\n{Colors.RESET}")

                    # Add key if provided
                    if 'key_url' in repository_info or 'key_id' in repository_info:
                        self.add_custom_key(repository_info)

                    return True
                else:
                    error_msg = f"Failed to write repository file for {repo_name}"
                    logging.error(error_msg)
                    raise FileOperationError(error_msg)

            except PermissionError as e:
                error_msg = "Permission denied when adding repository. Please run as root."
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise PermissionError(error_msg) from e
            except FileOperationError as e:
                # This exception is already logged in write_file
                raise
            except Exception as e:
                error_msg = f"Unexpected error adding repository: {str(e)}"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise RepositoryError(error_msg) from e

    def add_custom_key(self, repository_info: Dict[str, str]) -> bool:
        """
        Add a custom repository key with proper verification

        Args:
            repository_info (Dict[str, str]): Repository information dictionary

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RepositoryError: If there's an error adding the repository key
            SecurityError: If the key verification fails
            NetworkError: If there's a network error when fetching the key
        """
        repo_name = repository_info.get('name', 'custom')
        logging.info(f"Adding key for repository: {repo_name}")

        try:
            # Determine key path in trusted.gpg.d
            key_filename = f"{repo_name.lower().replace(' ', '-')}-key.gpg"
            key_path = f"/etc/apt/trusted.gpg.d/{key_filename}"

            # Get fingerprint if provided
            fingerprint = repository_info.get('fingerprint')
            if fingerprint:
                logging.info(f"Using provided fingerprint: {fingerprint}")

            # Add key from URL if provided
            if 'key_url' in repository_info and repository_info['key_url']:
                key_url = repository_info['key_url']
                logging.debug(f"Adding key from URL: {key_url}")

                # Check if key already exists
                if os.path.exists(key_path) and fingerprint:
                    logging.info(f"Key already exists at {key_path}, verifying...")
                    if verify_gpg_key(key_path, fingerprint):
                        logging.info("Existing key verified successfully")
                        return True
                    else:
                        logging.warning("Existing key verification failed, downloading new key")
                        os.remove(key_path)

                # Download and verify the key
                if not download_and_verify_key(key_url, key_path, fingerprint):
                    error_msg = f"Failed to download and verify key from URL: {key_url}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise SecurityError(
                        message=error_msg,
                        suggestion="Check the key URL and your internet connection"
                    )

                success_msg = f"Repository key for {repo_name} added and verified successfully"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True

            # Add key from keyserver if key_id is provided
            elif 'key_id' in repository_info and repository_info['key_id']:
                key_id = repository_info['key_id']
                keyserver = repository_info.get('keyserver', 'keyserver.ubuntu.com')
                logging.debug(f"Adding key {key_id} from keyserver: {keyserver}")

                # Create a temporary file for the key
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = temp_file.name

                # Download the key from the keyserver
                key_cmd = f"gpg --keyserver {keyserver} --recv-keys {key_id} && gpg --export {key_id} > {temp_path}"
                result = run_command(key_cmd)

                if result != 0:
                    error_msg = f"Failed to download key {key_id} from keyserver: {keyserver}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise NetworkError(
                        message=error_msg,
                        suggestion="Check the key ID and keyserver, and your internet connection"
                    )

                # Verify the key
                if fingerprint and not verify_gpg_key(temp_path, fingerprint):
                    error_msg = f"Key verification failed for key {key_id} from keyserver: {keyserver}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    os.remove(temp_path)
                    raise SecurityError(
                        message=error_msg,
                        suggestion="The key may have been tampered with or is not the expected key"
                    )

                # Move the key to the trusted.gpg.d directory
                os.makedirs(os.path.dirname(key_path), exist_ok=True)
                os.rename(temp_path, key_path)

                success_msg = f"Repository key for {repo_name} added and verified successfully"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True

            logging.debug("No key to add")
            return True  # No key to add

        except SecurityError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error adding custom key: {str(e)}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise RepositoryError(error_msg) from e

    def delete_repository(self, repository_name: Optional[str] = None) -> bool:
        """
        Remove a repository from sources.list.d
        If repository_name is None, removes the default Kali Linux repository

        Args:
            repository_name (Optional[str]): Name of the repository to remove
                                           If None, removes the default Kali repository

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RepositoryError: If there's an error removing the repository
            FileOperationError: If there's an error removing the repository file
            PermissionError: If the script doesn't have permission to remove the repository
        """
        if repository_name is None:
            # Remove default Kali repository
            logging.info("Removing default Kali Linux repository")

            if os.path.exists(self.repository_path):
                try:
                    logging.debug(f"Removing repository file: {self.repository_path}")
                    os.remove(self.repository_path)
                    success_msg = "Kali repository deleted successfully"
                    logging.info(success_msg)
                    print(f"{Colors.GREEN}\n[+] {success_msg}\n{Colors.RESET}")
                    return True
                except PermissionError as e:
                    error_msg = "Permission denied when removing repository file. Please run as root."
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise PermissionError(error_msg) from e
                except OSError as e:
                    error_msg = f"Error removing repository file: {str(e)}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    raise FileOperationError(error_msg) from e
            else:
                warning_msg = "Kali repository file not found"
                logging.warning(warning_msg)
                print(f"{Colors.YELLOW}{warning_msg}{Colors.RESET}")
                return False
        else:
            # Remove custom repository
            logging.info(f"Removing custom repository: {repository_name}")

            try:
                repo_filename = f"/etc/apt/sources.list.d/{repository_name.lower().replace(' ', '_')}.list"
                logging.debug(f"Repository filename: {repo_filename}")

                if os.path.exists(repo_filename):
                    try:
                        os.remove(repo_filename)
                        success_msg = f"Repository {repository_name} deleted successfully"
                        logging.info(success_msg)
                        print(f"{Colors.GREEN}\n[+] {success_msg}\n{Colors.RESET}")
                        return True
                    except PermissionError as e:
                        error_msg = "Permission denied when removing repository file. Please run as root."
                        logging.error(error_msg)
                        print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                        raise PermissionError(error_msg) from e
                    except OSError as e:
                        error_msg = f"Error removing repository file: {str(e)}"
                        logging.error(error_msg)
                        print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                        raise FileOperationError(error_msg) from e
                else:
                    warning_msg = f"Repository {repository_name} not found"
                    logging.warning(warning_msg)
                    print(f"{Colors.YELLOW}{warning_msg}{Colors.RESET}")
                    return False
            except Exception as e:
                error_msg = f"Unexpected error removing repository: {str(e)}"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise RepositoryError(error_msg) from e

    def add_key(self) -> bool:
        """
        Add repository keyserver with proper verification

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RepositoryError: If there's an error adding the repository key
            SecurityError: If the key verification fails
            NetworkError: If there's a network error when fetching the key
        """
        # Kali Linux archive key fingerprint (updated April 2025)
        kali_key_fingerprint = "827C8569F2518CC677FECA1AED65462EC8D5E4C5"
        kali_key_url = "https://archive.kali.org/archive-key.asc"
        key_path = "/etc/apt/trusted.gpg.d/kali-archive-key.gpg"

        logging.info("Adding Kali Linux repository key")

        try:
            # Check if key already exists
            if os.path.exists(key_path):
                logging.info(f"Key already exists at {key_path}, verifying...")
                if verify_gpg_key(key_path, kali_key_fingerprint):
                    logging.info("Existing key verified successfully")
                    return True
                else:
                    logging.warning("Existing key verification failed, downloading new key")
                    os.remove(key_path)

            # Download and verify the key
            logging.info(f"Downloading key from {kali_key_url}")
            if not download_and_verify_key(kali_key_url, key_path, kali_key_fingerprint):
                error_msg = "Failed to download and verify Kali Linux repository key"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise SecurityError(
                    message=error_msg,
                    suggestion="Check your internet connection and try again"
                )

            # Create marker file to indicate key was added
            if not write_file(self.tmp_key_path, "katoolin\n"):
                error_msg = "Failed to create key marker file"
                logging.error(error_msg)
                raise FileOperationError(
                    message=error_msg,
                    suggestion="Check if you have permission to write to the directory"
                )

            success_msg = "Kali Linux repository key added and verified successfully"
            logging.info(success_msg)
            print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")

            # Update repositories
            update_cmd = 'apt-get update -o Dir::Etc::sourcelist="sources.list.d/katoolin.list" -o Dir::Etc::sourceparts="-" -o apt::Get::List-Cleanup="0"'
            logging.debug(f"Running update command: {update_cmd}")

            result = run_command(update_cmd)

            if result != 0:
                error_msg = "Failed to update repositories"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise RepositoryError(error_msg)

            success_msg = "Repositories updated successfully"
            logging.info(success_msg)
            print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")

            return True

        except SecurityError:
            # Already logged and raised
            raise
        except FileOperationError:
            # Already logged and raised
            raise
        except RepositoryError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error adding repository key: {str(e)}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise RepositoryError(error_msg) from e

    def view_sources_list(self) -> Optional[str]:
        """
        View the contents of the sources.list file

        Returns:
            Optional[str]: Contents of the file or None if an error occurred

        Raises:
            FileOperationError: If there's an error reading the sources.list file
        """
        logging.info("Viewing contents of sources.list file")
        try:
            content = read_file('/etc/apt/sources.list')
            if content is None:
                error_msg = "Failed to read sources.list file"
                logging.error(error_msg)
                raise FileOperationError(error_msg)
            return content
        except FileOperationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error reading sources.list: {str(e)}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            return None

    def update_repositories(self) -> bool:
        """
        Update the package lists

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RepositoryError: If there's an error updating the repositories
            NetworkError: If there's a network error during the update
        """
        logging.info("Updating package lists")
        try:
            update_cmd = "apt-get update -m"
            logging.debug(f"Running update command: {update_cmd}")

            result = run_command(update_cmd)

            if result == 0:
                success_msg = "Repositories updated successfully"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True
            else:
                error_msg = "Failed to update repositories"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise RepositoryError(error_msg)

        except PermissionError as e:
            error_msg = "Permission denied when updating repositories. Please run as root."
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise PermissionError(error_msg) from e
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower() or "unreachable" in str(e).lower():
                error_msg = f"Network error updating repositories: {str(e)}"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise NetworkError(error_msg) from e
            else:
                error_msg = f"Unexpected error updating repositories: {str(e)}"
                logging.error(error_msg)
                print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                raise RepositoryError(error_msg) from e
