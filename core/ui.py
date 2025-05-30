#!/usr/bin/env python3

import os
import logging
from typing import Dict, List, Optional

from core.repository import RepositoryManager
from core.tools import ToolManager
from core.utils import (
    Colors, clear_screen, format_category_name, safe_input,
    KatoolinError, RepositoryError, ToolInstallationError, 
    PermissionError, FileOperationError, NetworkError, UserInputError,
    display_progress, display_spinner
)
from core.plugins import PluginManager
from core.profiler import global_profiler

class CategoryManager:
    """
    Class for managing categories and tools data
    """
    def __init__(self):
        logging.info("Initializing CategoryManager")
        try:
            # Import categories from core module
            from core.categories import categories
            self.categories = categories.copy()
            logging.debug(f"Loaded {len(self.categories)} built-in categories")

            # Load categories from plugins
            try:
                self.plugin_manager = PluginManager()
                self.plugin_manager.load_all_plugins()
                logging.debug(f"Loaded plugins: {', '.join(self.plugin_manager.get_plugin_names())}")
            except Exception as e:
                error_msg = f"Error loading plugins: {str(e)}"
                logging.error(error_msg)
                print(f"{Colors.YELLOW}Warning: {error_msg}{Colors.RESET}")
                # Continue without plugins
                self.plugin_manager = None

            if self.plugin_manager:
                # Merge plugin categories with built-in categories
                plugin_categories = self.plugin_manager.get_plugin_categories()
                logging.debug(f"Found {len(plugin_categories)} plugin categories")

                # Find the highest category ID to avoid conflicts
                max_id = max(self.categories.keys()) if self.categories else 0
                logging.debug(f"Highest built-in category ID: {max_id}")

                # Add plugin categories with new IDs to avoid conflicts
                for plugin_id, category_data in plugin_categories.items():
                    # Use the plugin's ID if it doesn't conflict, otherwise generate a new ID
                    new_id = plugin_id if plugin_id not in self.categories else max_id + 1
                    self.categories[new_id] = category_data
                    logging.debug(f"Added plugin category {category_data[0]} with ID {new_id}")
                    if new_id != plugin_id:
                        max_id = new_id

                logging.info(f"Total categories after merging: {len(self.categories)}")
            else:
                logging.warning("No plugins loaded, using only built-in categories")

        except ImportError as e:
            error_msg = f"Error importing categories module: {str(e)}"
            logging.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            # Initialize with empty categories as fallback
            self.categories = {}
            self.plugin_manager = None
        except Exception as e:
            error_msg = f"Unexpected error initializing CategoryManager: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            # Initialize with empty categories as fallback
            self.categories = {}
            self.plugin_manager = None

    def get_category_name(self, category_id: int) -> Optional[str]:
        """
        Get the name of a category by its ID

        Args:
            category_id (int): ID of the category

        Returns:
            Optional[str]: Name of the category or None if not found

        Raises:
            ValueError: If category_id is not a valid integer
        """
        try:
            logging.debug(f"Getting name for category ID: {category_id}")
            if category_id in self.categories:
                category_name = self.categories[category_id][0]
                logging.debug(f"Found category name: {category_name}")
                return category_name

            logging.warning(f"Category ID {category_id} not found")
            return None
        except TypeError as e:
            error_msg = f"Invalid category ID: {category_id}. Must be an integer."
            logging.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error getting category name: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            return None

    def get_category_tools(self, category_id: int) -> Optional[List[str]]:
        """
        Get the tools in a category by its ID

        Args:
            category_id (int): ID of the category

        Returns:
            Optional[List[str]]: List of tools in the category or None if not found

        Raises:
            ValueError: If category_id is not a valid integer
        """
        try:
            logging.debug(f"Getting tools for category ID: {category_id}")
            if category_id in self.categories:
                tools = self.categories[category_id][1]
                logging.debug(f"Found {len(tools)} tools in category")
                return tools

            logging.warning(f"Category ID {category_id} not found")
            return None
        except TypeError as e:
            error_msg = f"Invalid category ID: {category_id}. Must be an integer."
            logging.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error getting category tools: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            return None

    def get_all_categories(self) -> Dict[int, str]:
        """
        Get all categories

        Returns:
            Dict[int, str]: Dictionary of category IDs and names
        """
        try:
            logging.debug("Getting all categories")
            formatted_categories = {
                key: self.format_category_name(value[0]) 
                for key, value in self.categories.items()
            }
            logging.debug(f"Found {len(formatted_categories)} categories")
            return formatted_categories
        except Exception as e:
            error_msg = f"Unexpected error getting all categories: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            # Return empty dict as fallback
            return {}

    def format_category_name(self, category_name: str) -> str:
        """
        Format a category name for display

        Args:
            category_name (str): Name of the category

        Returns:
            str: Formatted category name

        Raises:
            ValueError: If category_name is not a string
        """
        try:
            logging.debug(f"Formatting category name: {category_name}")
            if not isinstance(category_name, str):
                error_msg = f"Invalid category name: {category_name}. Must be a string."
                logging.error(error_msg)
                raise ValueError(error_msg)

            formatted_name = format_category_name(category_name)
            logging.debug(f"Formatted name: {formatted_name}")
            return formatted_name
        except Exception as e:
            error_msg = f"Unexpected error formatting category name: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            # Return original name as fallback
            return category_name

    def search_tool(self, tool_name: str) -> Dict[int, str]:
        """
        Search for a tool in all categories

        Args:
            tool_name (str): Name of the tool to search for

        Returns:
            Dict[int, str]: Dictionary of category IDs and names where the tool was found

        Raises:
            ValueError: If tool_name is not a string
        """
        try:
            logging.info(f"Searching for tool: {tool_name}")
            if not isinstance(tool_name, str):
                error_msg = f"Invalid tool name: {tool_name}. Must be a string."
                logging.error(error_msg)
                raise ValueError(error_msg)

            results = {}
            for category_id, category_data in self.categories.items():
                if tool_name in category_data[1]:
                    category_name = self.format_category_name(category_data[0])
                    results[category_id] = category_name
                    logging.debug(f"Found tool in category: {category_name}")

            logging.info(f"Found tool in {len(results)} categories")
            return results
        except Exception as e:
            error_msg = f"Unexpected error searching for tool: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            # Return empty dict as fallback
            return {}

class UserInterface:
    """
    Class for handling the user interface
    """
    def __init__(self, category_manager: CategoryManager, tool_manager: ToolManager, repository_manager: RepositoryManager):
        logging.info("Initializing UserInterface")
        try:
            if not isinstance(category_manager, CategoryManager):
                error_msg = "Invalid category_manager parameter. Must be a CategoryManager instance."
                logging.error(error_msg)
                raise TypeError(error_msg)

            if not isinstance(tool_manager, ToolManager):
                error_msg = "Invalid tool_manager parameter. Must be a ToolManager instance."
                logging.error(error_msg)
                raise TypeError(error_msg)

            if not isinstance(repository_manager, RepositoryManager):
                error_msg = "Invalid repository_manager parameter. Must be a RepositoryManager instance."
                logging.error(error_msg)
                raise TypeError(error_msg)

            self.category_manager = category_manager
            self.tool_manager = tool_manager
            self.repository_manager = repository_manager
            logging.debug("UserInterface initialized successfully")
        except TypeError:
            # Already logged and raised
            raise
        except Exception as e:
            error_msg = f"Unexpected error initializing UserInterface: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            raise

    def display_banner(self):
        """Display the application banner"""
        version = "v4.0"
        total_tools = sum(len(tools) for _, tools in self.category_manager.categories.values())

        print(f"""
 $$\\   $$\\             $$\\                         $$\\ $$\\           
 $$ | $$  |            $$ |                        $$ |\\__|          
 $$ |$$  /  $$$$$$\\  $$$$$$\\    $$$$$$\\   $$$$$$\\  $$ |$$\\ $$$$$$$\\  
 $$$$$  /   \\____$$\\ \\_$$  _|  $$  __$$\\ $$  __$$\\ $$ |$$ |$$  __$$\\ 
 $$  $$<    $$$$$$$ |  {Colors.CYAN}the Nu Katoolin 4.0{Colors.RESET} |$$ |$$ |$$ |  $$ |{Colors.CYAN}
 $$ | \\$$\\  $$  __$$ |  $$ |$$\\ $$ |  $$ |$$ |  $$ |$$ |$$ |$$ |  $$ |
 $$ | \\$$\\ $$ |  $$ |  $$ | $$ |\\$$$$$$  |\\$$$$$$  |$$ |$$ |$$ |  $$ |
 \\__|  \\__|\\__|  \\__|  \\__| \\__| \\______/  \\______/ \\__|\\__|\\__|  \\__| {version}{Colors.RESET}

 {Colors.GREEN}+ -- -- +=[ Original project: https://github.com/LionSec/katoolin | LionSec
 + -- -- +=[ Updated by: 0xGuigui | https://github.com/0xGuigui/Katoolin3
 + -- -- +=[ Nu Katoolin 4.0: Improved version with better structure and features
 + -- -- +=[ {total_tools} Tools{Colors.RESET}
        """)

        print(f"{Colors.RED}[W] Before updating and upgrading your system, please remove all Kali-linux repositories to avoid any kind of problem.{Colors.RESET}")
        print(f"{Colors.RED}[W] In some cases, Kali-Linux repositories can destabilize your system or worse, completely destroy it.{Colors.RESET}")
        print("")

    def display_main_menu(self):
        """Display the main menu options"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}           KATOOLIN MAIN MENU             {Colors.CYAN}║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║ {Colors.GREEN}1){Colors.RESET} Add Kali repositories & Update       {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}2){Colors.RESET} View Categories                      {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}3){Colors.RESET} Install classicmenu indicator        {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}4){Colors.RESET} Install Kali menu                    {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}5){Colors.RESET} Tool Management                      {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}6){Colors.RESET} Help                                 {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}7){Colors.RESET} View Performance Statistics          {Colors.CYAN}║")
        print(f"╚══════════════════════════════════════════╝{Colors.RESET}")
        print(f"{Colors.YELLOW}Type 'exit' or 'quit' to exit the program{Colors.RESET}")
        print("")

    def display_repository_menu(self):
        """Display the repository management menu"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}           REPOSITORY MANAGEMENT MENU            {Colors.CYAN}║")
        print(f"╠══════════════════════════════════════════════════╣")
        print(f"║ {Colors.GREEN}1){Colors.RESET} Add kali linux repositories               {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}2){Colors.RESET} Update                                    {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}3){Colors.RESET} Remove all kali linux repositories        {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}4){Colors.RESET} View the contents of sources.list file    {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}5){Colors.RESET} Manage custom repositories                {Colors.CYAN}║")
        print(f"╚══════════════════════════════════════════════════╝{Colors.RESET}")
        print(f"{Colors.YELLOW}Type 'back' to return to the main menu{Colors.RESET}")
        print("")

    def display_categories(self):
        """Display all available categories"""
        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}                      AVAILABLE CATEGORIES                    {Colors.CYAN}║")
        print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

        categories = self.category_manager.get_all_categories()

        # Get sorted category IDs to ensure consistent ordering
        category_ids = sorted(categories.keys())

        # Calculate the number of categories per row (2 columns)
        categories_per_row = 2
        rows = (len(category_ids) + categories_per_row - 1) // categories_per_row

        # Display categories in a grid
        for row in range(rows):
            line = ""
            for col in range(categories_per_row):
                idx = row * categories_per_row + col
                if idx < len(category_ids):
                    category_id = category_ids[idx]
                    category_name = categories[category_id]
                    # Color the category number in green and make sure each column is aligned
                    line += f"{Colors.GREEN}{category_id}){Colors.RESET} {category_name.ljust(30)}"
            print(line)

        print(f"\n{Colors.GREEN}0){Colors.RESET} All Kali Linux Tools\n")
        print(f"{Colors.YELLOW}Select a category number or press (0) to install all Kali linux tools.{Colors.RESET}")
        print(f"{Colors.YELLOW}Type 'back' to return to the main menu{Colors.RESET}\n")

    def display_tools(self, category_id: int):
        """
        Display all tools in a category

        Args:
            category_id (int): ID of the category

        Raises:
            ValueError: If category_id is not a valid integer
        """
        logging.info(f"Displaying tools for category ID: {category_id}")

        try:
            # Get category name
            try:
                category_name = self.category_manager.get_category_name(category_id)
                if not category_name:
                    error_msg = f"Invalid category ID: {category_id}"
                    logging.error(error_msg)
                    print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
                    return
            except ValueError as e:
                # Already logged in get_category_name
                print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
                return

            # Format category name
            try:
                formatted_name = self.category_manager.format_category_name(category_name)
                logging.debug(f"Formatted category name: {formatted_name}")
            except ValueError as e:
                # Use unformatted name as fallback
                formatted_name = category_name
                logging.warning(f"Using unformatted category name due to error: {str(e)}")

            # Get tools in category
            try:
                tools = self.category_manager.get_category_tools(category_id)
                if not tools:
                    error_msg = f"No tools found in category: {formatted_name}"
                    logging.warning(error_msg)
                    print(f"{Colors.YELLOW}Warning: {error_msg}{Colors.RESET}")
                    return

                logging.debug(f"Found {len(tools)} tools in category")
            except ValueError as e:
                # Already logged in get_category_tools
                print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
                return

            # Display tools with a nice border
            print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
            print(f"║{Colors.YELLOW} {formatted_name.center(55)} {Colors.CYAN}║")
            print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

            # Calculate the number of tools per row (3 columns)
            tools_per_row = 3
            rows = (len(tools) + tools_per_row - 1) // tools_per_row

            # Display tools in a grid
            for row in range(rows):
                line = ""
                for col in range(tools_per_row):
                    idx = row * tools_per_row + col + 1
                    if idx <= len(tools):
                        tool_name = tools[idx-1]
                        # Color the tool number in green and make sure each column is aligned
                        line += f"{Colors.GREEN}{str(idx).rjust(2)}){Colors.RESET} {tool_name.ljust(25)}"
                print(line)

            print(f"\n{Colors.GREEN}0){Colors.RESET} Install all tools in this category\n")
            print(f"{Colors.YELLOW}Insert the number of the tool to install it.{Colors.RESET}")
            print(f"{Colors.YELLOW}Type 'back' to return to the categories menu{Colors.RESET}\n")
            logging.debug("Tools displayed successfully")

        except Exception as e:
            error_msg = f"Unexpected error displaying tools: {str(e)}"
            logging.error(error_msg)
            logging.debug(f"Exception details:", exc_info=True)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")

    def display_help(self, context: str = "main"):
        """
        Display help information

        Args:
            context (str): Context for which to display help (main or category)
        """
        print("\n****************** +Commands+ ******************\n")

        if context == "main":
            print(f"{Colors.GREEN}back{Colors.RESET} \t{Colors.YELLOW}Go back{Colors.RESET}")
            print(f"{Colors.GREEN}gohome{Colors.RESET}\t{Colors.YELLOW}Go to the main menu{Colors.RESET}")
            print(f"{Colors.GREEN}help{Colors.RESET} \t{Colors.YELLOW}Show this help menu{Colors.RESET}")
            print(f"{Colors.GREEN}exit{Colors.RESET}\t{Colors.YELLOW}Exit the script{Colors.RESET}")
        elif context == "category":
            print(f"{Colors.GREEN}<option>{Colors.RESET}  {Colors.YELLOW}Install tool{Colors.RESET}")
            print(f"{Colors.GREEN}99{Colors.RESET}        {Colors.YELLOW}Install all tools in the category{Colors.RESET}")
            print(f"{Colors.GREEN}back{Colors.RESET}      {Colors.YELLOW}Return to previous menu{Colors.RESET}")
            print(f"{Colors.GREEN}clear{Colors.RESET}     {Colors.YELLOW}Clean screen{Colors.RESET}")
            print(f"{Colors.GREEN}show{Colors.RESET}      {Colors.YELLOW}Show tools{Colors.RESET}")
            print(f"{Colors.GREEN}help{Colors.RESET}      {Colors.YELLOW}Show help{Colors.RESET}")

    def clear_screen(self):
        """Clear the terminal screen"""
        clear_screen()

    def display_custom_repositories_menu(self):
        """Display the custom repositories management menu"""
        print("")
        print("1) List available custom repositories")
        print("2) Add a custom repository")
        print("3) Remove a custom repository")
        print("4) Back to repository menu")
        print("")

    def display_classicmenu_info(self):
        """Display information about classicmenu indicator"""
        print(''' 
ClassicMenu Indicator is a notification area applet (application indicator) for the top panel of Ubuntu's Unity desktop environment.

It provides a simple way to get a classic GNOME-style application menu for those who prefer this over the Unity dash menu.

Like the classic GNOME menu, it includes Wine games and applications if you have those installed.

For more information, please visit: http://www.florian-diesch.de/software/classicmenu-indicator/
''')

    def display_profiling_stats(self):
        """Display profiling statistics"""
        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}                   PROFILING STATISTICS                     {Colors.CYAN}║")
        print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

        stats = global_profiler.print_stats()
        print(stats)

        print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        input()

    def display_tool_management_menu(self):
        """Display the tool management menu"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}             TOOL MANAGEMENT MENU               {Colors.CYAN}║")
        print(f"╠══════════════════════════════════════════════════╣")
        print(f"║ {Colors.GREEN}1){Colors.RESET} Check for tool updates                    {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}2){Colors.RESET} Update all tools                          {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}3){Colors.RESET} Update specific tools                     {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}4){Colors.RESET} Remove tools                              {Colors.CYAN}║")
        print(f"║ {Colors.GREEN}5){Colors.RESET} Back to main menu                         {Colors.CYAN}║")
        print(f"╚══════════════════════════════════════════════════╝{Colors.RESET}")
        print(f"{Colors.YELLOW}Type 'back' to return to the main menu{Colors.RESET}")
        print("")

    def display_tool_updates(self, update_info: Dict[str, Dict[str, str]]):
        """
        Display information about tool updates

        Args:
            update_info (Dict[str, Dict[str, str]]): Dictionary mapping tool names to update information
        """
        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}                      TOOL UPDATE STATUS                     {Colors.CYAN}║")
        print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

        # Count tools by status
        update_available = []
        up_to_date = []
        not_installed = []

        for tool_name, info in update_info.items():
            status = info.get('status')
            if status == 'update_available':
                update_available.append((tool_name, info))
            elif status == 'up_to_date':
                up_to_date.append((tool_name, info))
            elif status == 'not_installed':
                not_installed.append((tool_name, info))

        # Display summary
        print(f"{Colors.GREEN}Summary:{Colors.RESET}")
        print(f"  {Colors.YELLOW}{len(update_available)}{Colors.RESET} tools have updates available")
        print(f"  {Colors.GREEN}{len(up_to_date)}{Colors.RESET} tools are up to date")
        print(f"  {Colors.RED}{len(not_installed)}{Colors.RESET} tools are not installed\n")

        # Display tools with updates available
        if update_available:
            print(f"{Colors.YELLOW}Tools with updates available:{Colors.RESET}")
            print(f"{Colors.CYAN}{'Tool Name':<30} {'Installed Version':<20} {'Available Version':<20}{Colors.RESET}")
            print("-" * 70)

            for tool_name, info in sorted(update_available):
                installed = info.get('installed_version', 'N/A')
                available = info.get('available_version', 'N/A')
                print(f"{tool_name:<30} {installed:<20} {available:<20}")

            print("")

        # Ask if user wants to see more details
        if up_to_date or not_installed:
            from core.utils import safe_input
            show_more = safe_input(f"{Colors.YELLOW}Show details for up-to-date and not installed tools? [y/N]: {Colors.RESET}")

            if show_more.lower() == 'y':
                # Display up-to-date tools
                if up_to_date:
                    print(f"\n{Colors.GREEN}Up-to-date tools:{Colors.RESET}")
                    print(f"{Colors.CYAN}{'Tool Name':<30} {'Version':<20}{Colors.RESET}")
                    print("-" * 50)

                    for tool_name, info in sorted(up_to_date):
                        version = info.get('installed_version', 'N/A')
                        print(f"{tool_name:<30} {version:<20}")

                    print("")

                # Display not installed tools
                if not_installed:
                    print(f"\n{Colors.RED}Not installed tools:{Colors.RESET}")
                    for tool_name, _ in sorted(not_installed):
                        print(f"  {tool_name}")

                    print("")

        print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        input()
