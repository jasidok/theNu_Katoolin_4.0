#!/usr/bin/env python3

import os
import re
import logging
import traceback
from typing import List, Optional, Tuple, Union, Dict
from core.repository import RepositoryManager
from core.cache import cached, global_cache
from core.profiler import profile, global_profiler
from core.parallel import parallel, parallel_map, ParallelExecutor
from core.utils import (
    Colors, run_command, ToolInstallationError, 
    RepositoryError, PermissionError, NetworkError,
    display_progress, display_spinner
)

class ToolManager:
    """
    Class for managing tool installation
    """
    def __init__(self, repository_manager: RepositoryManager):
        self.repository_manager = repository_manager

    @profile
    def install_tool(self, tool_name: str, skip_confirmation: bool = False) -> bool:
        """
        Install a specific tool

        Args:
            tool_name (str): Name of the tool to install
            skip_confirmation (bool): Whether to skip the confirmation prompt

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ToolInstallationError: If there's an error installing the tool
            RepositoryError: If there's an error with the repository
            PermissionError: If the script doesn't have permission to install the tool
            NetworkError: If there's a network error during installation
        """
        logging.info(f"Installing tool: {tool_name}")

        try:
            # Confirm installation if not skipped
            if not skip_confirmation:
                from core.utils import safe_input

                # Get detailed information about the tool
                print(f"{Colors.CYAN}[*] Fetching information about {Colors.YELLOW}{tool_name}{Colors.CYAN}...{Colors.RESET}")
                tool_info = self.get_tool_info(tool_name)

                if tool_info:
                    # Display detailed information
                    print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"║{Colors.YELLOW} Tool Information {Colors.CYAN}║")
                    print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

                    print(f"{Colors.GREEN}Name:{Colors.RESET} {tool_info.get('name', tool_name)}")

                    if 'version' in tool_info:
                        print(f"{Colors.GREEN}Version:{Colors.RESET} {tool_info['version']}")

                    if 'description' in tool_info:
                        print(f"{Colors.GREEN}Description:{Colors.RESET}")
                        # Wrap the description text to 70 characters
                        import textwrap
                        for line in textwrap.wrap(tool_info['description'], width=70):
                            print(f"  {line}")

                    if 'homepage' in tool_info:
                        print(f"{Colors.GREEN}Homepage:{Colors.RESET} {tool_info['homepage']}")

                    print("")
                else:
                    print(f"{Colors.YELLOW}[!] Could not fetch detailed information about {tool_name}.{Colors.RESET}\n")

                confirm = safe_input(f"{Colors.YELLOW}Do you want to install this tool? [Y/n]: {Colors.RESET}")
                if confirm.lower() == 'n':
                    print(f"{Colors.YELLOW}[*] Installation cancelled.{Colors.RESET}")
                    return False

            # Add repository if needed
            try:
                logging.debug("Adding repository before tool installation")
                print(f"{Colors.CYAN}[*] Checking repositories...{Colors.RESET}")
                if not self.repository_manager.add_repository():
                    error_msg = "Failed to add repository"
                    logging.error(error_msg)
                    raise RepositoryError(error_msg)
            except RepositoryError:
                # Already logged and raised
                raise

            # Install the tool
            print(f"{Colors.CYAN}[*] Installing {tool_name}... This may take a while.{Colors.RESET}")

            # Show a spinner while preparing for installation
            display_spinner("Preparing installation", 1.0)

            install_cmd = f"apt install -y {tool_name}"
            logging.debug(f"Running install command: {install_cmd}")

            result, stdout, stderr = run_command(install_cmd, capture_output=True)

            if result == 0:
                # Show progress completion
                display_progress(100, 100, prefix=f"{Colors.GREEN}[+] Installation progress:", suffix="Complete", length=40)

                success_msg = f"Successfully installed {tool_name}"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")

                # Check if the tool provides a command and show usage example
                check_cmd = f"which {tool_name} 2>/dev/null"
                cmd_result = run_command(check_cmd)
                if cmd_result == 0:
                    print(f"{Colors.GREEN}[+] You can now run the tool using: {Colors.YELLOW}{tool_name} [options]{Colors.RESET}")

                return True
            else:
                # Check for specific error patterns in stderr
                if "Could not resolve" in stderr or "Failed to fetch" in stderr:
                    error_msg = f"Network error while installing {tool_name}: Could not fetch packages"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise NetworkError(error_msg)
                elif "Permission denied" in stderr or "requires root privileges" in stderr:
                    error_msg = f"Permission denied while installing {tool_name}. Please run as root."
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise PermissionError(error_msg)
                elif "Unable to locate package" in stderr:
                    error_msg = f"Package {tool_name} not found in the repositories"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise ToolInstallationError(error_msg)
                else:
                    error_msg = f"Failed to install {tool_name}"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise ToolInstallationError(error_msg)

        except RepositoryError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error installing tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    @profile
    def install_tools(self, tools: List[str], skip_confirmation: bool = False) -> bool:
        """
        Install multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to install
            skip_confirmation (bool): Whether to skip the confirmation prompt

        Returns:
            bool: True if all tools were installed successfully, False otherwise

        Raises:
            ToolInstallationError: If there's an error installing the tools
            RepositoryError: If there's an error with the repository
            PermissionError: If the script doesn't have permission to install the tools
            NetworkError: If there's a network error during installation
        """
        logging.info(f"Installing multiple tools: {len(tools)} tools")
        logging.debug(f"Tools to install: {', '.join(tools)}")

        try:
            # Confirm installation if not skipped
            if not skip_confirmation:
                from core.utils import safe_input
                print(f"{Colors.CYAN}[*] You are about to install {Colors.YELLOW}{len(tools)}{Colors.CYAN} tools:{Colors.RESET}")

                # Display the list of tools in a formatted way
                for i, tool in enumerate(tools, 1):
                    print(f"{Colors.YELLOW}   {i}. {tool}{Colors.RESET}")

                confirm = safe_input(f"\n{Colors.YELLOW}Do you want to continue? [Y/n]: {Colors.RESET}")
                if confirm.lower() == 'n':
                    print(f"{Colors.YELLOW}[*] Installation cancelled.{Colors.RESET}")
                    return False

            # Add repository if needed
            try:
                logging.debug("Adding repository before tools installation")
                print(f"{Colors.CYAN}[*] Checking repositories...{Colors.RESET}")
                if not self.repository_manager.add_repository():
                    error_msg = "Failed to add repository"
                    logging.error(error_msg)
                    raise RepositoryError(error_msg)
            except RepositoryError:
                # Already logged and raised
                raise

            # Show a spinner while preparing for installation
            print(f"{Colors.CYAN}[*] Preparing to install {len(tools)} tools...{Colors.RESET}")
            display_spinner("Preparing installation", 1.0)

            # Determine whether to use parallel installation or batch installation
            if len(tools) <= 3:
                # For a small number of tools, use batch installation
                return self._batch_install_tools(tools)
            else:
                # For a larger number of tools, use parallel installation
                return self._parallel_install_tools(tools)

        except RepositoryError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error installing tools: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    def _batch_install_tools(self, tools: List[str]) -> bool:
        """
        Install multiple tools in a single batch

        Args:
            tools (List[str]): List of tool names to install

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Batch installing {len(tools)} tools")

        # Install the tools
        tools_str = " ".join(tools)
        install_cmd = f"apt install -y {tools_str}"
        logging.debug(f"Running install command: {install_cmd}")

        # Show progress message
        print(f"{Colors.CYAN}[*] Installing tools... This may take a while.{Colors.RESET}")

        # Run the command
        result, stdout, stderr = run_command(install_cmd, capture_output=True)

        if result == 0:
            # Show progress completion
            display_progress(100, 100, prefix=f"{Colors.GREEN}[+] Installation progress:", suffix="Complete", length=40)

            success_msg = "Successfully installed all tools"
            logging.info(success_msg)
            print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
            return True
        else:
            # Check for specific error patterns in stderr
            if "Could not resolve" in stderr or "Failed to fetch" in stderr:
                error_msg = "Network error while installing tools: Could not fetch packages"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise NetworkError(error_msg)
            elif "Permission denied" in stderr or "requires root privileges" in stderr:
                error_msg = "Permission denied while installing tools. Please run as root."
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise PermissionError(error_msg)
            elif "Unable to locate package" in stderr:
                # Try to extract which package was not found
                match = re.search(r"Unable to locate package ([^\s]+)", stderr)
                package = match.group(1) if match else "some packages"

                error_msg = f"Package {package} not found in the repositories"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise ToolInstallationError(error_msg)
            else:
                error_msg = "Failed to install some tools"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise ToolInstallationError(error_msg)

    def _parallel_install_tools(self, tools: List[str]) -> bool:
        """
        Install multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to install

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Parallel installing {len(tools)} tools")

        # Show progress message
        print(f"{Colors.CYAN}[*] Installing tools in parallel... This may take a while.{Colors.RESET}")

        # Create a parallel executor for I/O-bound operations (apt install is mostly I/O-bound)
        executor = ParallelExecutor(max_workers=min(10, len(tools)), use_processes=False)

        # Track progress
        total_tools = len(tools)
        completed_tools = 0
        failed_tools = []
        skipped_tools = []

        # Function to install a single tool and update progress
        def install_single_tool(tool_name):
            nonlocal completed_tools, failed_tools, skipped_tools

            try:
                # First try standard installation
                install_cmd = f"apt install -y {tool_name}"
                result, stdout, stderr = run_command(install_cmd, capture_output=True)

                # Update progress
                completed_tools += 1
                display_progress(completed_tools, total_tools, 
                                prefix=f"{Colors.GREEN}[+] Installation progress:", 
                                suffix=f"{completed_tools}/{total_tools}", length=40)

                if result != 0:
                    # Try fallback strategies
                    if self._try_installation_fallbacks(tool_name, stderr):
                        return True

                    # Log the failure
                    logging.warning(f"Command failed with exit code {result}: apt install -y {tool_name}")
                    logging.error(f"Failed to install {tool_name}: {stderr}")

                    # Check if it's a non-critical error we can skip
                    if self._is_skippable_error(stderr):
                        skipped_tools.append((tool_name, self._get_error_reason(stderr)))
                        return True  # Don't fail the whole process

                    failed_tools.append((tool_name, stderr))
                    return False

                return True
            except Exception as e:
                logging.error(f"Error installing {tool_name}: {str(e)}")
                failed_tools.append((tool_name, str(e)))
                return False

        try:
            # Install tools in parallel
            results = executor.map(install_single_tool, tools)

            # Calculate success statistics
            successful = sum(results)
            failed = len(failed_tools)
            skipped = len(skipped_tools)

            # Report results
            print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
            print(f"║{Colors.YELLOW} Installation Summary {Colors.CYAN}║")
            print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}")

            print(f"{Colors.GREEN}✓ Successfully installed: {successful}/{total_tools} tools{Colors.RESET}")

            if skipped > 0:
                print(f"{Colors.YELLOW}⚠ Skipped (unavailable): {skipped} tools{Colors.RESET}")
                for tool, reason in skipped_tools:
                    print(f"{Colors.YELLOW}    - {tool}: {reason}{Colors.RESET}")

            if failed > 0:
                print(f"{Colors.RED}✗ Failed: {failed} tools{Colors.RESET}")
                for tool, error in failed_tools:
                    print(f"{Colors.RED}    - {tool}: {self._get_error_reason(error)}{Colors.RESET}")

            # Determine success based on more intelligent criteria
            # If most failures are due to packages not being available (skipped), that's acceptable
            actual_failures = failed  # Real failures (not just unavailable packages)
            installable_tools = total_tools - skipped  # Tools that should have been installable

            if installable_tools == 0:
                # All tools were skipped (not available), this is informational
                print(f"\n{Colors.YELLOW}[!] No tools were available for installation on this system{Colors.RESET}")
                return False
            elif successful == installable_tools:
                # All installable tools were installed successfully
                print(f"\n{Colors.GREEN}[+] Successfully installed all available tools{Colors.RESET}")
                return True
            elif actual_failures == 0:
                # No real failures, just some unavailable packages
                print(
                    f"\n{Colors.GREEN}[+] Installation completed - all available tools installed successfully{Colors.RESET}")
                return True
            else:
                # Some real failures occurred
                failure_rate = actual_failures / installable_tools
                if failure_rate <= 0.3:  # Allow up to 30% failure rate for real failures
                    print(
                        f"\n{Colors.GREEN}[+] Installation mostly successful ({successful}/{installable_tools} available tools installed){Colors.RESET}")
                    return True
                else:
                    error_msg = f"Too many installation failures: {actual_failures}/{installable_tools} installable tools failed"
                    logging.error(error_msg)
                    print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")

                    # List the most critical failures
                    if failed > 0:
                        print(f"{Colors.RED}[!] Critical failures:{Colors.RESET}")
                        for tool, error in failed_tools[:5]:  # Show first 5 failures
                            print(f"{Colors.RED}    - {tool}: {self._get_error_reason(error)}{Colors.RESET}")
                        if failed > 5:
                            print(f"{Colors.RED}    ... and {failed - 5} more{Colors.RESET}")

                    raise ToolInstallationError(error_msg)

        except Exception as e:
            error_msg = f"Error during parallel installation: {str(e)}"
            logging.error(error_msg)
            print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    def _try_installation_fallbacks(self, tool_name: str, stderr: str) -> bool:
        """
        Try alternative installation methods for failed packages
        
        Args:
            tool_name (str): Name of the tool that failed to install
            stderr (str): Error message from the failed installation
            
        Returns:
            bool: True if fallback installation succeeded, False otherwise
        """
        logging.debug(f"Trying fallback installation methods for {tool_name}")

        # Strategy 1: Handle dependency conflicts (Python version issues)
        if "dependency" in stderr.lower() and "python" in stderr.lower():
            if self._resolve_python_dependency_conflicts(tool_name, stderr):
                return True

        # Strategy 2: Try with --fix-broken for general dependency issues
        if "dependency" in stderr.lower() or "broken" in stderr.lower():
            try:
                logging.debug(f"Trying --fix-broken for {tool_name}")
                fix_cmd = f"apt install -f -y && apt install -y {tool_name}"
                result, _, _ = run_command(fix_cmd, capture_output=True)
                if result == 0:
                    logging.info(f"Successfully installed {tool_name} using --fix-broken")
                    return True
            except Exception:
                pass

        # Strategy 3: Try alternative package names (common variations)
        alt_names = self._get_alternative_package_names(tool_name)
        for alt_name in alt_names:
            try:
                logging.debug(f"Trying alternative name {alt_name} for {tool_name}")
                alt_cmd = f"apt install -y {alt_name}"
                result, _, _ = run_command(alt_cmd, capture_output=True)
                if result == 0:
                    logging.info(f"Successfully installed {tool_name} as {alt_name}")
                    return True
            except Exception:
                continue

        # Strategy 4: Try installing from snap if available
        try:
            # Check if snap is available
            snap_check = run_command("which snap")
            if snap_check == 0:
                logging.debug(f"Trying snap installation for {tool_name}")
                snap_cmd = f"snap install {tool_name}"
                result, _, _ = run_command(snap_cmd, capture_output=True)
                if result == 0:
                    logging.info(f"Successfully installed {tool_name} via snap")
                    return True
        except Exception:
            pass

        return False

    def _resolve_python_dependency_conflicts(self, tool_name: str, stderr: str) -> bool:
        """
        Try to resolve Python dependency conflicts
        
        Args:
            tool_name (str): Name of the tool with conflicts
            stderr (str): Error message from apt
            
        Returns:
            bool: True if conflict was resolved and tool installed, False otherwise
        """
        logging.debug(f"Attempting to resolve Python dependency conflicts for {tool_name}")

        # Strategy 1: Try installing with --no-install-recommends to avoid optional deps
        try:
            logging.debug(f"Trying --no-install-recommends for {tool_name}")
            minimal_cmd = f"apt install -y --no-install-recommends {tool_name}"
            result, _, _ = run_command(minimal_cmd, capture_output=True)
            if result == 0:
                logging.info(f"Successfully installed {tool_name} with minimal dependencies")
                return True
        except Exception:
            pass

        # Strategy 2: Try installing with specific Python version pinning
        if "python3-" in tool_name or tool_name in ['enum4linux', 'xplico']:
            try:
                logging.debug(f"Trying Python version-specific installation for {tool_name}")
                # Try to install compatible Python dependencies first
                python_deps = [
                    "python3=3.12*",
                    "python3-dev=3.12*",
                    "python3-pip"
                ]

                for dep in python_deps:
                    dep_cmd = f"apt install -y {dep}"
                    run_command(dep_cmd, capture_output=True)

                # Now try installing the tool
                result, _, _ = run_command(f"apt install -y {tool_name}", capture_output=True)
                if result == 0:
                    logging.info(f"Successfully installed {tool_name} after Python version fix")
                    return True
            except Exception:
                pass

        # Strategy 3: Try using apt-get instead of apt (different solver)
        try:
            logging.debug(f"Trying apt-get instead of apt for {tool_name}")
            aptget_cmd = f"apt-get install -y {tool_name}"
            result, _, _ = run_command(aptget_cmd, capture_output=True)
            if result == 0:
                logging.info(f"Successfully installed {tool_name} using apt-get")
                return True
        except Exception:
            pass

        # Strategy 4: Try installing with aptitude (advanced dependency resolver)
        try:
            # Check if aptitude is available
            aptitude_check = run_command("which aptitude")
            if aptitude_check == 0:
                logging.debug(f"Trying aptitude for {tool_name}")
                aptitude_cmd = f"aptitude install -y {tool_name}"
                result, _, _ = run_command(aptitude_cmd, capture_output=True)
                if result == 0:
                    logging.info(f"Successfully installed {tool_name} using aptitude")
                    return True
        except Exception:
            pass

        return False

    def _get_alternative_package_names(self, tool_name: str) -> List[str]:
        """
        Get alternative package names to try
        
        Args:
            tool_name (str): Original package name
            
        Returns:
            List[str]: List of alternative names to try
        """
        alternatives = []

        # Common naming patterns for security tools
        name_variations = {
            'acccheck': ['acccheck-kali', 'smb-enum'],
            'dnmap': ['dnmap-kali', 'distributed-nmap'],
            'enum4linux': ['enum4linux-ng', 'samba-enum'],
            'fragroute': ['fragroute-kali', 'libnet-fragroute'],
            'ghost-phisher': ['ghost-phisher-kali'],
            'golismero': ['golismero-kali'],
            'xplico': ['xplico-kali']
        }

        if tool_name in name_variations:
            alternatives.extend(name_variations[tool_name])

        # Generic variations
        alternatives.extend([
            f"{tool_name}-kali",
            f"kali-{tool_name}",
            f"{tool_name.replace('-', '')}",
            f"{tool_name.replace('_', '-')}",
            f"python3-{tool_name}",
            f"{tool_name}-ng"  # "next generation" versions
        ])

        return alternatives

    def _is_skippable_error(self, stderr: str) -> bool:
        """
        Check if an error is non-critical and can be skipped
        
        Args:
            stderr (str): Error message from apt
            
        Returns:
            bool: True if error can be skipped, False otherwise
        """
        skippable_patterns = [
            "Unable to locate package",
            "has no installation candidate",
            "couldn't be found",
            "package not found"
        ]

        # Check if this is a known problematic package with location error
        if any(pattern in stderr for pattern in skippable_patterns):
            return True

        # Skip complex dependency conflicts that can't be easily resolved
        # These are typically due to Ubuntu vs Kali package version differences
        python_version_conflicts = [
            "python3-charset-normalizer" in stderr and "python3 (>= 3.13~)" in stderr,
            "python3-psycopg2" in stderr and "python3 (>= 3.13~)" in stderr,
            "python3-tk" in stderr and "python3 (>= 3.13~)" in stderr,
            "python3-zope.interface" in stderr and "python3 (>= 3.13~)" in stderr,
            "python3-pydantic-core" in stderr and "python3 (>= 3.13~)" in stderr,
            "python3-uvloop" in stderr and "python3 (>= 3.13~)" in stderr
        ]

        if any(python_version_conflicts):
            return True

        # Skip complex dependency resolver conflicts (common with Kali packages on Ubuntu)
        if "pkgProblemResolver::Resolve generated breaks" in stderr:
            return True

        # Skip conflicts involving specific Python version requirements
        if "python3 (>= 3.13~)" in stderr and "python3:amd64=3.12" in stderr:
            return True

        # Skip conflicts with held packages (common in mixed environments)
        if "caused by held packages" in stderr:
            return True

        return False

    def _get_error_reason(self, stderr: str) -> str:
        """
        Extract a human-readable error reason from stderr
        
        Args:
            stderr (str): Error message from apt
            
        Returns:
            str: Human-readable error reason
        """
        if "Unable to locate package" in stderr:
            return "Package not found in repositories"
        elif "python3-charset-normalizer" in stderr and "python3 (>= 3.13~)" in stderr:
            return "Python 3.13+ required but system has 3.12 (version conflict)"
        elif "python3-psycopg2" in stderr and "python3 (>= 3.13~)" in stderr:
            return "Python 3.13+ required but system has 3.12 (version conflict)"
        elif "dependency" in stderr.lower() and "conflict" in stderr.lower():
            return "Dependency conflicts (version mismatch)"
        elif "broken" in stderr.lower():
            return "Broken dependencies"
        elif "Permission denied" in stderr:
            return "Permission denied"
        elif "Could not resolve" in stderr or "Failed to fetch" in stderr:
            return "Network error"
        elif "No space left" in stderr:
            return "Insufficient disk space"
        elif "pkgProblemResolver::Resolve generated breaks" in stderr:
            return "Complex dependency conflicts detected"
        else:
            # Return first meaningful line of error for brevity
            lines = [line.strip() for line in stderr.split('\n') if line.strip()]
            error_line = next((line for line in lines if 'Error:' in line), lines[0] if lines else "Unknown error")
            return error_line[:80] + "..." if len(error_line) > 80 else error_line

    @profile
    def remove_tool(self, tool_name: str, skip_confirmation: bool = False) -> bool:
        """
        Remove a specific tool

        Args:
            tool_name (str): Name of the tool to remove
            skip_confirmation (bool): Whether to skip the confirmation prompt

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ToolInstallationError: If there's an error removing the tool
            PermissionError: If the script doesn't have permission to remove the tool
        """
        logging.info(f"Removing tool: {tool_name}")

        try:
            # Confirm removal if not skipped
            if not skip_confirmation:
                from core.utils import safe_input
                print(f"{Colors.RED}[!] Warning: You are about to remove: {Colors.YELLOW}{tool_name}{Colors.RESET}")
                print(f"{Colors.RED}[!] This action cannot be undone.{Colors.RESET}")
                confirm = safe_input(f"{Colors.YELLOW}Are you sure you want to continue? [y/N]: {Colors.RESET}")
                if confirm.lower() != 'y':
                    print(f"{Colors.YELLOW}[*] Removal cancelled.{Colors.RESET}")
                    return False

            print(f"{Colors.CYAN}[*] Removing {tool_name}...{Colors.RESET}")
            remove_cmd = f"apt remove -y {tool_name}"
            logging.debug(f"Running remove command: {remove_cmd}")

            result, stdout, stderr = run_command(remove_cmd, capture_output=True)

            if result == 0:
                success_msg = f"Successfully removed {tool_name}"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True
            else:
                # Check for specific error patterns in stderr
                if "Permission denied" in stderr or "requires root privileges" in stderr:
                    error_msg = f"Permission denied while removing {tool_name}. Please run as root."
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise PermissionError(error_msg)
                elif "Unable to locate package" in stderr or "is not installed" in stderr:
                    error_msg = f"Package {tool_name} is not installed"
                    logging.warning(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.YELLOW}[!] {error_msg}{Colors.RESET}")
                    # Not raising an exception here as this is more of a warning
                    return False
                else:
                    error_msg = f"Failed to remove {tool_name}"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise ToolInstallationError(error_msg)

        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error removing tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    @profile
    def remove_tools(self, tools: List[str], skip_confirmation: bool = False) -> bool:
        """
        Remove multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to remove
            skip_confirmation (bool): Whether to skip the confirmation prompt

        Returns:
            bool: True if all tools were removed successfully, False otherwise

        Raises:
            ToolInstallationError: If there's an error removing the tools
            PermissionError: If the script doesn't have permission to remove the tools
        """
        logging.info(f"Removing multiple tools: {len(tools)} tools")
        logging.debug(f"Tools to remove: {', '.join(tools)}")

        try:
            # Confirm removal if not skipped
            if not skip_confirmation:
                from core.utils import safe_input
                print(f"{Colors.RED}[!] Warning: You are about to remove {Colors.YELLOW}{len(tools)}{Colors.RED} tools:{Colors.RESET}")

                # Display the list of tools in a formatted way
                for i, tool in enumerate(tools, 1):
                    print(f"{Colors.YELLOW}   {i}. {tool}{Colors.RESET}")

                print(f"{Colors.RED}[!] This action cannot be undone.{Colors.RESET}")
                confirm = safe_input(f"\n{Colors.YELLOW}Are you sure you want to continue? [y/N]: {Colors.RESET}")
                if confirm.lower() != 'y':
                    print(f"{Colors.YELLOW}[*] Removal cancelled.{Colors.RESET}")
                    return False

            # Determine whether to use parallel removal or batch removal
            if len(tools) <= 3:
                # For a small number of tools, use batch removal
                return self._batch_remove_tools(tools)
            else:
                # For a larger number of tools, use parallel removal
                return self._parallel_remove_tools(tools)

        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error removing tools: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    def _batch_remove_tools(self, tools: List[str]) -> bool:
        """
        Remove multiple tools in a single batch

        Args:
            tools (List[str]): List of tool names to remove

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Batch removing {len(tools)} tools")

        print(f"{Colors.CYAN}[*] Removing {len(tools)} tools...{Colors.RESET}")
        tools_str = " ".join(tools)
        remove_cmd = f"apt remove -y {tools_str}"
        logging.debug(f"Running remove command: {remove_cmd}")

        result, stdout, stderr = run_command(remove_cmd, capture_output=True)

        if result == 0:
            success_msg = "Successfully removed all tools"
            logging.info(success_msg)
            print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
            return True
        else:
            # Check for specific error patterns in stderr
            if "Permission denied" in stderr or "requires root privileges" in stderr:
                error_msg = "Permission denied while removing tools. Please run as root."
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise PermissionError(error_msg)
            elif "Unable to locate package" in stderr or "is not installed" in stderr:
                # Try to extract which package was not found
                match = re.search(r"Unable to locate package ([^\s]+)", stderr)
                if match:
                    package = match.group(1)
                    error_msg = f"Package {package} is not installed"
                else:
                    error_msg = "Some packages are not installed"

                logging.warning(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.YELLOW}[!] {error_msg}{Colors.RESET}")
                # Not raising an exception here as this is more of a warning
                return False
            else:
                error_msg = "Failed to remove some tools"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise ToolInstallationError(error_msg)

    def _parallel_remove_tools(self, tools: List[str]) -> bool:
        """
        Remove multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to remove

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Parallel removing {len(tools)} tools")

        # Show progress message
        print(f"{Colors.CYAN}[*] Removing tools in parallel... This may take a while.{Colors.RESET}")

        # Create a parallel executor for I/O-bound operations (apt remove is mostly I/O-bound)
        executor = ParallelExecutor(max_workers=min(10, len(tools)), use_processes=False)

        # Track progress
        total_tools = len(tools)
        completed_tools = 0
        failed_tools = []
        not_installed = 0

        # Function to remove a single tool and update progress
        def remove_single_tool(tool_name):
            nonlocal completed_tools, failed_tools, not_installed

            try:
                # Remove the tool
                remove_cmd = f"apt remove -y {tool_name}"
                result, stdout, stderr = run_command(remove_cmd, capture_output=True)

                # Update progress
                completed_tools += 1
                display_progress(completed_tools, total_tools, 
                                prefix=f"{Colors.GREEN}[+] Removal progress:", 
                                suffix=f"{completed_tools}/{total_tools}", length=40)

                if result != 0:
                    # Check for specific error patterns
                    if "Unable to locate package" in stderr or "is not installed" in stderr:
                        not_installed += 1
                        logging.warning(f"Package {tool_name} is not installed")
                        return True  # Not considering this a failure
                    else:
                        logging.error(f"Failed to remove {tool_name}: {stderr}")
                        failed_tools.append((tool_name, stderr))
                        return False

                return True
            except Exception as e:
                logging.error(f"Error removing {tool_name}: {str(e)}")
                failed_tools.append((tool_name, str(e)))
                return False

        try:
            # Remove tools in parallel
            results = executor.map(remove_single_tool, tools)

            # Check if all tools were removed successfully
            if all(results):
                if not_installed == len(tools):
                    info_msg = "None of the specified tools were installed"
                    logging.info(info_msg)
                    print(f"\n{Colors.YELLOW}[!] {info_msg}{Colors.RESET}")
                    return False
                elif not_installed > 0:
                    success_msg = f"Successfully removed {len(tools) - not_installed} tools ({not_installed} were not installed)"
                    logging.info(success_msg)
                    print(f"\n{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                    return True
                else:
                    success_msg = "Successfully removed all tools"
                    logging.info(success_msg)
                    print(f"\n{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                    return True
            else:
                # Some tools failed to remove
                error_msg = f"Failed to remove {len(failed_tools)} out of {total_tools} tools"
                logging.error(error_msg)

                # Print details about failed tools
                print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")
                for tool, error in failed_tools:
                    print(f"{Colors.RED}    - {tool}: {error}{Colors.RESET}")

                raise ToolInstallationError(error_msg)
        except Exception as e:
            error_msg = f"Error during parallel removal: {str(e)}"
            logging.error(error_msg)
            print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    @profile
    def update_tool(self, tool_name: str) -> bool:
        """
        Update a specific tool

        Args:
            tool_name (str): Name of the tool to update

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ToolInstallationError: If there's an error updating the tool
            RepositoryError: If there's an error with the repository
            PermissionError: If the script doesn't have permission to update the tool
            NetworkError: If there's a network error during update
        """
        logging.info(f"Updating tool: {tool_name}")

        try:
            # Add repository if needed
            try:
                logging.debug("Adding repository before tool update")
                if not self.repository_manager.add_repository():
                    error_msg = "Failed to add repository"
                    logging.error(error_msg)
                    raise RepositoryError(error_msg)
            except RepositoryError:
                # Already logged and raised
                raise

            # Update the tool
            update_cmd = f"apt install --only-upgrade -y {tool_name}"
            logging.debug(f"Running update command: {update_cmd}")

            result, stdout, stderr = run_command(update_cmd, capture_output=True)

            if result == 0:
                success_msg = f"Successfully updated {tool_name}"
                logging.info(success_msg)
                print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True
            else:
                # Check for specific error patterns in stderr
                if "Could not resolve" in stderr or "Failed to fetch" in stderr:
                    error_msg = f"Network error while updating {tool_name}: Could not fetch packages"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise NetworkError(error_msg)
                elif "Permission denied" in stderr or "requires root privileges" in stderr:
                    error_msg = f"Permission denied while updating {tool_name}. Please run as root."
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise PermissionError(error_msg)
                elif "Unable to locate package" in stderr:
                    error_msg = f"Package {tool_name} not found in the repositories"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise ToolInstallationError(error_msg)
                elif "is already the newest version" in stderr:
                    info_msg = f"Package {tool_name} is already the newest version"
                    logging.info(info_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.GREEN}[+] {info_msg}{Colors.RESET}")
                    return True
                else:
                    error_msg = f"Failed to update {tool_name}"
                    logging.error(error_msg)
                    logging.debug(f"stderr: {stderr}")
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    raise ToolInstallationError(error_msg)

        except RepositoryError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error updating tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    @profile
    def update_tools(self, tools: List[str]) -> bool:
        """
        Update multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to update

        Returns:
            bool: True if all tools were updated successfully, False otherwise

        Raises:
            ToolInstallationError: If there's an error updating the tools
            RepositoryError: If there's an error with the repository
            PermissionError: If the script doesn't have permission to update the tools
            NetworkError: If there's a network error during update
        """
        logging.info(f"Updating multiple tools: {len(tools)} tools")
        logging.debug(f"Tools to update: {', '.join(tools)}")

        try:
            # Add repository if needed
            try:
                logging.debug("Adding repository before tools update")
                print(f"{Colors.CYAN}[*] Checking repositories...{Colors.RESET}")
                if not self.repository_manager.add_repository():
                    error_msg = "Failed to add repository"
                    logging.error(error_msg)
                    raise RepositoryError(error_msg)
            except RepositoryError:
                # Already logged and raised
                raise

            # Show a spinner while preparing for update
            print(f"{Colors.CYAN}[*] Preparing to update {len(tools)} tools...{Colors.RESET}")
            display_spinner("Preparing update", 1.0)

            # Determine whether to use parallel update or batch update
            if len(tools) <= 3:
                # For a small number of tools, use batch update
                return self._batch_update_tools(tools)
            else:
                # For a larger number of tools, use parallel update
                return self._parallel_update_tools(tools)

        except RepositoryError:
            # Already logged and raised
            raise
        except NetworkError:
            # Already logged and raised
            raise
        except PermissionError:
            # Already logged and raised
            raise
        except ToolInstallationError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error updating tools: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    def _batch_update_tools(self, tools: List[str]) -> bool:
        """
        Update multiple tools in a single batch

        Args:
            tools (List[str]): List of tool names to update

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Batch updating {len(tools)} tools")

        # Update the tools
        tools_str = " ".join(tools)
        update_cmd = f"apt install --only-upgrade -y {tools_str}"
        logging.debug(f"Running update command: {update_cmd}")

        # Show progress message
        print(f"{Colors.CYAN}[*] Updating tools... This may take a while.{Colors.RESET}")

        # Run the command
        result, stdout, stderr = run_command(update_cmd, capture_output=True)

        if result == 0:
            # Show progress completion
            display_progress(100, 100, prefix=f"{Colors.GREEN}[+] Update progress:", suffix="Complete", length=40)

            success_msg = "Successfully updated all tools"
            logging.info(success_msg)
            print(f"{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
            return True
        else:
            # Check for specific error patterns in stderr
            if "Could not resolve" in stderr or "Failed to fetch" in stderr:
                error_msg = "Network error while updating tools: Could not fetch packages"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise NetworkError(error_msg)
            elif "Permission denied" in stderr or "requires root privileges" in stderr:
                error_msg = "Permission denied while updating tools. Please run as root."
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise PermissionError(error_msg)
            elif "Unable to locate package" in stderr:
                # Try to extract which package was not found
                match = re.search(r"Unable to locate package ([^\s]+)", stderr)
                package = match.group(1) if match else "some packages"

                error_msg = f"Package {package} not found in the repositories"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise ToolInstallationError(error_msg)
            elif "is already the newest version" in stderr and "0 upgraded" in stderr:
                info_msg = "All packages are already at their newest version"
                logging.info(info_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.GREEN}[+] {info_msg}{Colors.RESET}")
                return True
            else:
                error_msg = "Failed to update some tools"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                raise ToolInstallationError(error_msg)

    def _parallel_update_tools(self, tools: List[str]) -> bool:
        """
        Update multiple tools in parallel

        Args:
            tools (List[str]): List of tool names to update

        Returns:
            bool: True if successful, False otherwise
        """
        logging.debug(f"Parallel updating {len(tools)} tools")

        # Show progress message
        print(f"{Colors.CYAN}[*] Updating tools in parallel... This may take a while.{Colors.RESET}")

        # Create a parallel executor for I/O-bound operations (apt update is mostly I/O-bound)
        executor = ParallelExecutor(max_workers=min(10, len(tools)), use_processes=False)

        # Track progress
        total_tools = len(tools)
        completed_tools = 0
        failed_tools = []
        already_newest = 0

        # Function to update a single tool and update progress
        def update_single_tool(tool_name):
            nonlocal completed_tools, failed_tools, already_newest

            try:
                # Update the tool
                update_cmd = f"apt install --only-upgrade -y {tool_name}"
                result, stdout, stderr = run_command(update_cmd, capture_output=True)

                # Update progress
                completed_tools += 1
                display_progress(completed_tools, total_tools, 
                                prefix=f"{Colors.GREEN}[+] Update progress:", 
                                suffix=f"{completed_tools}/{total_tools}", length=40)

                if result != 0:
                    # Check for specific error patterns
                    if "is already the newest version" in stderr:
                        already_newest += 1
                        return True
                    else:
                        logging.error(f"Failed to update {tool_name}: {stderr}")
                        failed_tools.append((tool_name, stderr))
                        return False

                return True
            except Exception as e:
                logging.error(f"Error updating {tool_name}: {str(e)}")
                failed_tools.append((tool_name, str(e)))
                return False

        try:
            # Update tools in parallel
            results = executor.map(update_single_tool, tools)

            # Check if all tools were updated successfully
            if all(results):
                if already_newest == len(tools):
                    info_msg = "All packages are already at their newest version"
                    logging.info(info_msg)
                    print(f"\n{Colors.GREEN}[+] {info_msg}{Colors.RESET}")
                else:
                    success_msg = "Successfully updated all tools"
                    if already_newest > 0:
                        success_msg += f" ({already_newest} were already at the newest version)"
                    logging.info(success_msg)
                    print(f"\n{Colors.GREEN}[+] {success_msg}{Colors.RESET}")
                return True
            else:
                # Some tools failed to update
                error_msg = f"Failed to update {len(failed_tools)} out of {total_tools} tools"
                logging.error(error_msg)

                # Print details about failed tools
                print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")
                for tool, error in failed_tools:
                    print(f"{Colors.RED}    - {tool}: {error}{Colors.RESET}")

                raise ToolInstallationError(error_msg)
        except Exception as e:
            error_msg = f"Error during parallel update: {str(e)}"
            logging.error(error_msg)
            print(f"\n{Colors.RED}[!] {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    def check_installed(self, tool_name: str) -> bool:
        """
        Check if a tool is installed

        Args:
            tool_name (str): Name of the tool to check

        Returns:
            bool: True if installed, False otherwise

        Raises:
            ToolInstallationError: If there's an error checking if the tool is installed
        """
        logging.info(f"Checking if tool is installed: {tool_name}")

        try:
            check_cmd = f"dpkg -s {tool_name} 2>/dev/null | grep -q 'Status: install ok installed'"
            logging.debug(f"Running check command: {check_cmd}")

            result = run_command(check_cmd)

            if result == 0:
                logging.info(f"Tool {tool_name} is installed")
                return True
            else:
                logging.info(f"Tool {tool_name} is not installed")
                return False

        except Exception as e:
            error_msg = f"Error checking if tool {tool_name} is installed: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise ToolInstallationError(error_msg) from e

    @cached(ttl=3600, key_prefix="tool_version")
    def get_installed_version(self, tool_name: str) -> Optional[str]:
        """
        Get the installed version of a tool

        Args:
            tool_name (str): Name of the tool to check

        Returns:
            Optional[str]: Version string if installed, None otherwise
        """
        logging.info(f"Getting installed version for tool: {tool_name}")

        try:
            # Check if the tool is installed
            if not self.check_installed(tool_name):
                return None

            # Get the installed version
            version_cmd = f"dpkg-query -W -f='${{Version}}' {tool_name} 2>/dev/null"
            logging.debug(f"Running version command: {version_cmd}")

            result, stdout, stderr = run_command(version_cmd, capture_output=True)

            if result == 0 and stdout:
                version = stdout.strip()
                logging.info(f"Tool {tool_name} version: {version}")
                return version
            else:
                logging.warning(f"Could not determine version for {tool_name}")
                return None

        except Exception as e:
            error_msg = f"Error getting version for tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            return None

    def check_for_updates(self, tools: List[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Check for updates to installed tools

        Args:
            tools (List[str], optional): List of tool names to check. If None, checks all installed tools.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping tool names to update information
                {
                    'tool_name': {
                        'installed_version': 'x.y.z',
                        'available_version': 'a.b.c',
                        'status': 'update_available' | 'up_to_date' | 'not_installed'
                    }
                }
        """
        logging.info("Checking for tool updates")

        update_info = {}

        try:
            # If no tools specified, get all installed packages
            if tools is None:
                # Get list of all installed packages
                list_cmd = "dpkg-query -W -f='${Package}\\n'"
                result, stdout, stderr = run_command(list_cmd, capture_output=True)

                if result == 0:
                    tools = [line.strip() for line in stdout.splitlines() if line.strip()]
                    logging.info(f"Found {len(tools)} installed packages")
                else:
                    error_msg = "Failed to get list of installed packages"
                    logging.error(error_msg)
                    print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                    return {}

            # Update package lists
            print(f"{Colors.CYAN}[*] Updating package lists...{Colors.RESET}")
            update_cmd = "apt update -qq"
            run_command(update_cmd)

            # Check each tool for updates
            print(f"{Colors.CYAN}[*] Checking for updates to {len(tools)} tools...{Colors.RESET}")

            # Use parallel processing for checking updates
            executor = ParallelExecutor(max_workers=min(20, len(tools)), use_processes=False)

            def check_tool_update(tool_name):
                # Get installed version
                installed_version = self.get_installed_version(tool_name)

                if installed_version is None:
                    return tool_name, {
                        'installed_version': None,
                        'available_version': None,
                        'status': 'not_installed'
                    }

                # Check if an update is available
                check_cmd = f"apt-get --simulate --quiet upgrade | grep -q '^Inst {tool_name} '"
                result = run_command(check_cmd)

                if result == 0:
                    # Update available, get available version
                    version_cmd = f"apt-cache policy {tool_name} | grep 'Candidate:' | awk '{{print $2}}'"
                    _, available_version, _ = run_command(version_cmd, capture_output=True)
                    available_version = available_version.strip()

                    return tool_name, {
                        'installed_version': installed_version,
                        'available_version': available_version,
                        'status': 'update_available'
                    }
                else:
                    # No update available
                    return tool_name, {
                        'installed_version': installed_version,
                        'available_version': installed_version,
                        'status': 'up_to_date'
                    }

            # Process tools in parallel
            results = executor.map(check_tool_update, tools)

            # Convert results to dictionary
            for tool_name, info in results:
                update_info[tool_name] = info

            return update_info

        except Exception as e:
            error_msg = f"Error checking for updates: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
            return {}

    @cached(ttl=3600, key_prefix="tool_info")
    def get_tool_info(self, tool_name: str) -> dict:
        """
        Get detailed information about a tool

        Args:
            tool_name (str): Name of the tool to get information about

        Returns:
            dict: Dictionary containing tool information (name, version, description, etc.)

        Raises:
            ToolInstallationError: If there's an error getting tool information
        """
        logging.info(f"Getting information for tool: {tool_name}")

        try:
            # Get tool information using apt-cache
            info_cmd = f"apt-cache show {tool_name}"
            logging.debug(f"Running info command: {info_cmd}")

            result, stdout, stderr = run_command(info_cmd, capture_output=True)

            if result != 0:
                error_msg = f"Error getting information for tool {tool_name}"
                logging.error(error_msg)
                logging.debug(f"stderr: {stderr}")
                print(f"{Colors.RED}[!] {error_msg}{Colors.RESET}")
                return {}

            # Parse the output to extract relevant information
            info = {}
            description_lines = []
            in_description = False

            for line in stdout.splitlines():
                if line.startswith("Package:"):
                    info["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("Version:"):
                    info["version"] = line.split(":", 1)[1].strip()
                elif line.startswith("Description:"):
                    in_description = True
                    description_lines.append(line.split(":", 1)[1].strip())
                elif line.startswith(" ") and in_description:
                    description_lines.append(line.strip())
                elif line.startswith("Homepage:"):
                    info["homepage"] = line.split(":", 1)[1].strip()
                    in_description = False
                elif not line.strip():
                    in_description = False

            if description_lines:
                info["description"] = " ".join(description_lines)

            logging.debug(f"Tool information: {info}")
            return info

        except Exception as e:
            error_msg = f"Error getting information for tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            logging.debug("Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            return {}
