#!/usr/bin/env python3

import os
import sys
import traceback
from typing import List, Dict, Any, Optional, Callable

# Import classes from core modules
from core.repository import RepositoryManager
from core.tools import ToolManager
from core.ui import CategoryManager, UserInterface
from core.utils import Colors, check_root, safe_input, safe_exit, run_command, with_error_handling
from core.plugins import PluginManager

# Main application class
class Application:
    def __init__(self):
        # Initialize plugin manager first so it can be used by other managers
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_all_plugins()

        # Initialize other managers with plugin support
        self.repository_manager = RepositoryManager(self.plugin_manager)
        self.tool_manager = ToolManager(self.repository_manager)
        self.category_manager = CategoryManager()  # CategoryManager already loads plugins internally
        self.ui = UserInterface(self.category_manager, self.tool_manager, self.repository_manager)

    def check_root(self) -> bool:
        """
        Check if the script is running with root privileges

        Returns:
            bool: True if running as root, False otherwise
        """
        return check_root()

    def handle_repository_menu(self):
        """Handle the repository management menu"""
        self.ui.display_repository_menu()

        while True:
            option = safe_input(f"{Colors.GREEN}What do you want to do ?> {Colors.RESET}")

            if option == '1':
                self.repository_manager.add_repository()
            elif option == '2':
                run_command("apt-get update -m")
            elif option == '3':
                self.repository_manager.delete_repository()
            elif option == '4':
                content = self.repository_manager.view_sources_list()
                if content:
                    print(content)
            elif option == '5':
                self.handle_custom_repositories_menu()
            elif option == 'back' or option == 'gohome':
                break
            elif option == 'exit' or option == 'quit':
                safe_exit(0, "Shutdown requested...Goodbye...")
            elif option == '':
                # User cancelled with Ctrl+C
                break
            else:
                print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")

    def handle_custom_repositories_menu(self):
        """Handle the custom repositories management menu"""
        self.ui.display_custom_repositories_menu()

        while True:
            option = safe_input(f"{Colors.GREEN}What do you want to do ?> {Colors.RESET}")

            if option == '1':
                # List available custom repositories
                plugin_repos = self.plugin_manager.get_plugin_repositories()
                if not plugin_repos:
                    print(f"{Colors.YELLOW}No custom repositories available from plugins{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}Available custom repositories:{Colors.RESET}")
                    for i, repo in enumerate(plugin_repos, 1):
                        name = repo.get('name', 'Unnamed repository')
                        url = repo.get('url', 'No URL')
                        print(f"{i}) {name} - {url}")
                    print()
            elif option == '2':
                # Add a custom repository
                plugin_repos = self.plugin_manager.get_plugin_repositories()
                if not plugin_repos:
                    print(f"{Colors.YELLOW}No custom repositories available from plugins{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}Available custom repositories to add:{Colors.RESET}")
                    for i, repo in enumerate(plugin_repos, 1):
                        name = repo.get('name', 'Unnamed repository')
                        url = repo.get('url', 'No URL')
                        print(f"{i}) {name} - {url}")
                    print()

                    repo_index = safe_input(f"{Colors.GREEN}Enter the number of the repository to add (or 'cancel'): {Colors.RESET}")
                    if repo_index.lower() == 'cancel':
                        continue

                    try:
                        repo_index = int(repo_index) - 1
                        if 0 <= repo_index < len(plugin_repos):
                            self.repository_manager.add_repository(plugin_repos[repo_index])
                        else:
                            print(f"{Colors.RED}Invalid repository number{Colors.RESET}")
                    except ValueError:
                        print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")
            elif option == '3':
                # Remove a custom repository
                plugin_repos = self.plugin_manager.get_plugin_repositories()
                if not plugin_repos:
                    print(f"{Colors.YELLOW}No custom repositories available from plugins{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}Available custom repositories to remove:{Colors.RESET}")
                    for i, repo in enumerate(plugin_repos, 1):
                        name = repo.get('name', 'Unnamed repository')
                        print(f"{i}) {name}")
                    print()

                    repo_index = safe_input(f"{Colors.GREEN}Enter the number of the repository to remove (or 'cancel'): {Colors.RESET}")
                    if repo_index.lower() == 'cancel':
                        continue

                    try:
                        repo_index = int(repo_index) - 1
                        if 0 <= repo_index < len(plugin_repos):
                            repo_name = plugin_repos[repo_index].get('name', 'custom')
                            self.repository_manager.delete_repository(repo_name)
                        else:
                            print(f"{Colors.RED}Invalid repository number{Colors.RESET}")
                    except ValueError:
                        print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")
            elif option == '4' or option == 'back':
                break
            elif option == 'gohome':
                return True  # Signal to return to main menu
            elif option == 'exit' or option == 'quit':
                safe_exit(0, "Shutdown requested...Goodbye...")
            elif option == '':
                # User cancelled with Ctrl+C
                break
            else:
                print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")

    def handle_category_menu(self, category_id: int):
        """
        Handle the tools menu for a specific category

        Args:
            category_id (int): ID of the category
        """
        category_name = self.category_manager.get_category_name(category_id)
        if not category_name:
            print(f"{Colors.RED}Error: Invalid category ID{Colors.RESET}")
            return

        tools = self.category_manager.get_category_tools(category_id)
        if not tools:
            print(f"{Colors.RED}Error: No tools found in this category{Colors.RESET}")
            return

        self.ui.clear_screen()
        self.ui.display_tools(category_id)

        while True:
            option = safe_input(f"{Colors.CYAN}kat > {Colors.RESET}")

            if option == 'back':
                break
            elif option == 'gohome':
                return True  # Signal to return to main menu
            elif option == 'exit' or option == 'quit':
                safe_exit(0, "Shutdown requested...Goodbye...")
            elif option == 'help':
                self.ui.display_help("category")
            elif option == 'clear':
                self.ui.clear_screen()
                self.ui.display_tools(category_id)
            elif option == 'show':
                self.ui.display_tools(category_id)
            elif option == '0' or option == '99':
                self.tool_manager.install_tools(tools)
            elif option == '':
                # User cancelled with Ctrl+C
                break
            else:
                # Try to parse as a tool index
                success, result, error = with_error_handling(lambda: int(option) - 1)
                if success and result is not None:
                    tool_index = result
                    if 0 <= tool_index < len(tools):
                        self.tool_manager.install_tool(tools[tool_index])
                    else:
                        print(f"{Colors.RED}Invalid tool number. Please try again.{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")

        return False  # Signal to return to categories menu

    def handle_categories_menu(self):
        """Handle the categories menu"""
        self.ui.clear_screen()
        self.ui.display_categories()

        while True:
            option = safe_input(f"{Colors.CYAN}kat > {Colors.RESET}")

            if option == 'back' or option == 'gohome':
                break
            elif option == 'exit' or option == 'quit':
                safe_exit(0, "Shutdown requested...Goodbye...")
            elif option == 'help':
                self.ui.display_help()
            elif option == '0':
                # Install all tools from all categories
                all_tools = []
                for category_id in self.category_manager.categories:
                    all_tools.extend(self.category_manager.get_category_tools(category_id))
                self.tool_manager.install_tools(all_tools)
            elif option == '':
                # User cancelled with Ctrl+C
                break
            else:
                # Try to parse as a category ID
                success, result, error = with_error_handling(lambda: int(option))
                if success and result is not None:
                    category_id = result
                    if category_id in self.category_manager.categories:
                        go_home = self.handle_category_menu(category_id)
                        if go_home:
                            break
                        self.ui.clear_screen()
                        self.ui.display_categories()
                    else:
                        print(f"{Colors.RED}Invalid category number. Please try again.{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")

    def handle_classicmenu_indicator(self):
        """Handle the installation of classicmenu indicator"""
        self.ui.display_classicmenu_info()

        option = safe_input(f"{Colors.GREEN}Do you want to install classicmenu indicator ? [y/n]> {Colors.RESET}")
        if option.lower() == 'y':
            run_command("add-apt-repository ppa:diesch/testing && apt-get update")
            run_command("sudo apt-get install classicmenu-indicator")

    def handle_kali_menu(self):
        """Handle the installation of Kali menu"""
        option = safe_input(f"{Colors.GREEN}Do you want to install Kali menu ? [y/n]> {Colors.RESET}")
        if option.lower() == 'y':
            run_command("apt-get install kali-menu")

    def handle_tool_management(self):
        """Handle the tool management menu"""
        self.ui.clear_screen()
        self.ui.display_tool_management_menu()

        while True:
            option = safe_input(f"{Colors.GREEN}What do you want to do ?> {Colors.RESET}")

            if option == '1':
                # Check for tool updates
                print(f"{Colors.CYAN}[*] Checking for tool updates...{Colors.RESET}")
                update_info = self.tool_manager.check_for_updates()
                self.ui.display_tool_updates(update_info)
                self.ui.clear_screen()
                self.ui.display_tool_management_menu()
            elif option == '2':
                # Update all tools
                print(f"{Colors.CYAN}[*] Updating all tools...{Colors.RESET}")

                # First check for updates
                update_info = self.tool_manager.check_for_updates()

                # Filter tools that have updates available
                tools_to_update = [
                    tool_name for tool_name, info in update_info.items()
                    if info.get('status') == 'update_available'
                ]

                if not tools_to_update:
                    print(f"{Colors.GREEN}[+] All tools are already up to date.{Colors.RESET}")
                else:
                    print(f"{Colors.CYAN}[*] Found {len(tools_to_update)} tools with updates available.{Colors.RESET}")
                    self.tool_manager.update_tools(tools_to_update)

                print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                input()
                self.ui.clear_screen()
                self.ui.display_tool_management_menu()
            elif option == '3':
                # Update specific tools
                self.handle_specific_tool_updates()
                self.ui.clear_screen()
                self.ui.display_tool_management_menu()
            elif option == '4':
                # Remove tools
                self.handle_tool_removal()
                self.ui.clear_screen()
                self.ui.display_tool_management_menu()
            elif option == '5' or option == 'back':
                break
            elif option == 'gohome':
                return True  # Signal to return to main menu
            elif option == 'exit' or option == 'quit':
                safe_exit(0, "Shutdown requested...Goodbye...")
            elif option == '':
                # User cancelled with Ctrl+C
                break
            else:
                print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")

    def handle_specific_tool_updates(self):
        """Handle updating specific tools"""
        # First check for updates
        print(f"{Colors.CYAN}[*] Checking for tool updates...{Colors.RESET}")
        update_info = self.tool_manager.check_for_updates()

        # Filter tools that have updates available
        tools_with_updates = [
            (tool_name, info) for tool_name, info in update_info.items()
            if info.get('status') == 'update_available'
        ]

        if not tools_with_updates:
            print(f"{Colors.GREEN}[+] All tools are already up to date.{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            input()
            return

        # Display tools with updates available
        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}                 TOOLS WITH UPDATES AVAILABLE                {Colors.CYAN}║")
        print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

        print(f"{Colors.CYAN}{'#':<4} {'Tool Name':<30} {'Installed Version':<20} {'Available Version':<20}{Colors.RESET}")
        print("-" * 74)

        for i, (tool_name, info) in enumerate(sorted(tools_with_updates), 1):
            installed = info.get('installed_version', 'N/A')
            available = info.get('available_version', 'N/A')
            print(f"{i:<4} {tool_name:<30} {installed:<20} {available:<20}")

        print(f"\n{Colors.YELLOW}Enter the numbers of the tools to update (comma-separated), 'all' to update all, or 'cancel' to go back.{Colors.RESET}")
        selection = safe_input(f"{Colors.GREEN}Selection: {Colors.RESET}")

        if selection.lower() == 'cancel':
            return

        tools_to_update = []

        if selection.lower() == 'all':
            tools_to_update = [tool_name for tool_name, _ in tools_with_updates]
        else:
            try:
                # Parse comma-separated list of numbers
                indices = [int(idx.strip()) for idx in selection.split(',') if idx.strip()]
                for idx in indices:
                    if 1 <= idx <= len(tools_with_updates):
                        tools_to_update.append(tools_with_updates[idx-1][0])
                    else:
                        print(f"{Colors.RED}[!] Invalid selection: {idx}{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}[!] Invalid input. Please enter numbers separated by commas.{Colors.RESET}")
                print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                input()
                return

        if not tools_to_update:
            print(f"{Colors.RED}[!] No valid tools selected.{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            input()
            return

        # Update the selected tools
        print(f"{Colors.CYAN}[*] Updating {len(tools_to_update)} tools...{Colors.RESET}")
        self.tool_manager.update_tools(tools_to_update)

        print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        input()

    def handle_tool_removal(self):
        """Handle removing tools"""
        # Get list of installed tools
        print(f"{Colors.CYAN}[*] Getting list of installed tools...{Colors.RESET}")

        # Get list of all installed packages
        list_cmd = "dpkg-query -W -f='${Package}\\n'"
        result, stdout, stderr = run_command(list_cmd, capture_output=True)

        if result != 0:
            print(f"{Colors.RED}[!] Failed to get list of installed packages{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            input()
            return

        installed_tools = [line.strip() for line in stdout.splitlines() if line.strip()]

        # Display options for tool removal
        print(f"\n{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}                      TOOL REMOVAL OPTIONS                   {Colors.CYAN}║")
        print(f"╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

        print(f"{Colors.GREEN}1){Colors.RESET} Remove specific tools")
        print(f"{Colors.GREEN}2){Colors.RESET} Remove all tools from a category")
        print(f"{Colors.GREEN}3){Colors.RESET} Back to tool management menu\n")

        option = safe_input(f"{Colors.GREEN}What do you want to do ?> {Colors.RESET}")

        if option == '1':
            # Remove specific tools
            print(f"{Colors.CYAN}[*] Enter the names of the tools to remove (comma-separated) or 'cancel' to go back:{Colors.RESET}")
            tools_input = safe_input(f"{Colors.GREEN}Tools: {Colors.RESET}")

            if tools_input.lower() == 'cancel':
                return

            tools_to_remove = [tool.strip() for tool in tools_input.split(',') if tool.strip()]

            if not tools_to_remove:
                print(f"{Colors.RED}[!] No valid tools entered.{Colors.RESET}")
                print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                input()
                return

            # Remove the tools
            self.tool_manager.remove_tools(tools_to_remove)

        elif option == '2':
            # Remove all tools from a category
            self.ui.clear_screen()
            self.ui.display_categories()

            category_id = safe_input(f"{Colors.GREEN}Enter the category number to remove all tools from, or 'cancel' to go back: {Colors.RESET}")

            if category_id.lower() == 'cancel':
                return

            try:
                category_id = int(category_id)
                if category_id in self.category_manager.categories:
                    category_name = self.category_manager.get_category_name(category_id)
                    tools = self.category_manager.get_category_tools(category_id)

                    if not tools:
                        print(f"{Colors.RED}[!] No tools found in category {category_name}{Colors.RESET}")
                        print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                        input()
                        return

                    print(f"{Colors.CYAN}[*] You are about to remove all tools from category: {Colors.YELLOW}{category_name}{Colors.RESET}")
                    confirm = safe_input(f"{Colors.RED}Are you sure? This cannot be undone. [y/N]: {Colors.RESET}")

                    if confirm.lower() != 'y':
                        print(f"{Colors.YELLOW}[*] Operation cancelled.{Colors.RESET}")
                        print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                        input()
                        return

                    # Remove the tools
                    self.tool_manager.remove_tools(tools)
                else:
                    print(f"{Colors.RED}[!] Invalid category number.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}[!] Invalid input. Please enter a number.{Colors.RESET}")

            print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            input()

        elif option == '3':
            return
        else:
            print(f"{Colors.RED}[!] Invalid option.{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            input()

    def run(self):
        """Run the application"""
        try:
            if not self.check_root():
                return 1

            self.ui.clear_screen()
            self.ui.display_banner()
            self.ui.display_main_menu()

            while True:
                option = safe_input(f"{Colors.CYAN}kat > {Colors.RESET}")

                if option == 'exit' or option == 'quit':
                    safe_exit(0, "Shutdown requested...Goodbye...")
                elif option == 'help' or option == '5':
                    self.ui.display_help()
                elif option == '1':
                    self.handle_repository_menu()
                    self.ui.clear_screen()
                    self.ui.display_banner()
                    self.ui.display_main_menu()
                elif option == '2':
                    self.handle_categories_menu()
                    self.ui.clear_screen()
                    self.ui.display_banner()
                    self.ui.display_main_menu()
                elif option == '3':
                    self.handle_classicmenu_indicator()
                elif option == '4':
                    self.handle_kali_menu()
                elif option == '5':
                    self.handle_tool_management()
                    self.ui.clear_screen()
                    self.ui.display_banner()
                    self.ui.display_main_menu()
                elif option == '6':
                    self.ui.display_help()
                elif option == '7':
                    self.ui.display_profiling_stats()
                    self.ui.clear_screen()
                    self.ui.display_banner()
                    self.ui.display_main_menu()
                elif option == '':
                    # User cancelled with Ctrl+C
                    break
                else:
                    print(f"{Colors.RED}Sorry, that was an invalid command!{Colors.RESET}")
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(f"{Colors.RED}An unexpected error occurred: {str(e)}{Colors.RESET}")
            return 1

        return 0

if __name__ == "__main__":
    app = Application()
    sys.exit(app.run())
