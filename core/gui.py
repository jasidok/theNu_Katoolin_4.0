#!/usr/bin/env python3
"""
GUI module for Katoolin.
Provides a graphical user interface for the Katoolin application.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Callable

from core.repository import RepositoryManager
from core.tools import ToolManager
from core.ui import CategoryManager
from core.utils import Colors, check_root, safe_exit, run_command, with_error_handling
from core.plugins import PluginManager


class KatoolinGUI:
    """
    Main GUI class for Katoolin application.
    Provides a graphical interface for all functionality available in the CLI version.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the GUI.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Katoolin - Kali Linux Tools Installer")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # Initialize managers
        self.category_manager = CategoryManager()
        self.repository_manager = RepositoryManager()
        self.tool_manager = ToolManager(self.repository_manager)
        self.plugin_manager = PluginManager()
        
        # Check if running as root
        if not check_root():
            messagebox.showerror(
                "Permission Error", 
                "Katoolin requires root privileges to run. Please restart with sudo."
            )
            self.root.after(1000, self.root.destroy)
            return
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_main_tab()
        self.create_repository_tab()
        self.create_categories_tab()
        self.create_tool_management_tab()
        self.create_reporting_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # Set up styles
        self.setup_styles()
    
    def setup_styles(self):
        """Set up custom styles for the GUI."""
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("Danger.TButton", foreground="red")
        style.configure("Success.TButton", foreground="green")
        style.configure("Info.TButton", foreground="blue")
    
    def create_main_tab(self):
        """Create the main tab with welcome message and basic information."""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Home")
        
        # Banner
        banner_frame = ttk.Frame(main_tab)
        banner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        banner_text = """
        ██╗  ██╗ █████╗ ████████╗ ██████╗  ██████╗ ██╗     ██╗███╗   ██╗
        ██║ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██║████╗  ██║
        █████╔╝ ███████║   ██║   ██║   ██║██║   ██║██║     ██║██╔██╗ ██║
        ██╔═██╗ ██╔══██║   ██║   ██║   ██║██║   ██║██║     ██║██║╚██╗██║
        ██║  ██╗██║  ██║   ██║   ╚██████╔╝╚██████╔╝███████╗██║██║ ╚████║
        ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝
        """
        
        banner_label = ttk.Label(
            banner_frame, 
            text=banner_text, 
            font=("Courier", 10),
            justify=tk.CENTER
        )
        banner_label.pack(pady=10)
        
        # Welcome message
        welcome_frame = ttk.Frame(main_tab)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        welcome_text = """
        Welcome to Katoolin - Kali Linux Tools Installer
        
        This application allows you to install Kali Linux tools on your Ubuntu/Debian system.
        
        Use the tabs above to navigate through different functionalities:
        - Repository: Manage Kali Linux repositories
        - Categories: Browse and install tools by category
        - Tool Management: Update and remove installed tools
        - Reporting: Generate reports about installed tools
        
        Note: This application requires root privileges to run.
        """
        
        welcome_label = ttk.Label(
            welcome_frame, 
            text=welcome_text, 
            justify=tk.LEFT,
            wraplength=700
        )
        welcome_label.pack(pady=20)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(main_tab, text="Quick Actions")
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        add_repo_btn = ttk.Button(
            actions_frame, 
            text="Add Kali Repository", 
            command=lambda: self.notebook.select(1)  # Switch to repository tab
        )
        add_repo_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        browse_tools_btn = ttk.Button(
            actions_frame, 
            text="Browse Tools", 
            command=lambda: self.notebook.select(2)  # Switch to categories tab
        )
        browse_tools_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        update_btn = ttk.Button(
            actions_frame, 
            text="Update Repositories", 
            command=self.update_repositories
        )
        update_btn.pack(side=tk.LEFT, padx=10, pady=10)
    
    def create_repository_tab(self):
        """Create the repository management tab."""
        repo_tab = ttk.Frame(self.notebook)
        self.notebook.add(repo_tab, text="Repository")
        
        # Repository actions
        actions_frame = ttk.LabelFrame(repo_tab, text="Repository Actions")
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_repo_btn = ttk.Button(
            actions_frame, 
            text="Add Kali Repository", 
            command=self.add_repository
        )
        add_repo_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        add_key_btn = ttk.Button(
            actions_frame, 
            text="Add Kali GPG Key", 
            command=self.add_key
        )
        add_key_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        delete_repo_btn = ttk.Button(
            actions_frame, 
            text="Delete Kali Repository", 
            command=self.delete_repository,
            style="Danger.TButton"
        )
        delete_repo_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        update_repo_btn = ttk.Button(
            actions_frame, 
            text="Update Repositories", 
            command=self.update_repositories
        )
        update_repo_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Custom repository frame
        custom_frame = ttk.LabelFrame(repo_tab, text="Add Custom Repository")
        custom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(custom_frame, text="Repository Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_repo_name = ttk.Entry(custom_frame, width=30)
        self.custom_repo_name.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(custom_frame, text="Repository URL:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_repo_url = ttk.Entry(custom_frame, width=50)
        self.custom_repo_url.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(custom_frame, text="Distribution:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_repo_dist = ttk.Entry(custom_frame, width=30)
        self.custom_repo_dist.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(custom_frame, text="Components:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_repo_comp = ttk.Entry(custom_frame, width=30)
        self.custom_repo_comp.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(custom_frame, text="GPG Key URL (optional):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_repo_key = ttk.Entry(custom_frame, width=50)
        self.custom_repo_key.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        add_custom_btn = ttk.Button(
            custom_frame, 
            text="Add Custom Repository", 
            command=self.add_custom_repository
        )
        add_custom_btn.grid(row=5, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Sources list display
        sources_frame = ttk.LabelFrame(repo_tab, text="Current Sources List")
        sources_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sources_text = tk.Text(sources_frame, wrap=tk.WORD, height=10)
        self.sources_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        refresh_btn = ttk.Button(
            sources_frame, 
            text="Refresh", 
            command=self.refresh_sources_list
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Initial load of sources list
        self.refresh_sources_list()
    
    def create_categories_tab(self):
        """Create the categories and tools tab."""
        categories_tab = ttk.Frame(self.notebook)
        self.notebook.add(categories_tab, text="Categories")
        
        # Split into two panes
        paned = ttk.PanedWindow(categories_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left pane - Categories
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Categories", font=("", 12, "bold")).pack(pady=5)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        search_btn = ttk.Button(
            search_frame, 
            text="Search", 
            command=self.search_tools
        )
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # Categories listbox
        categories_frame = ttk.Frame(left_frame)
        categories_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.categories_listbox = tk.Listbox(categories_frame, selectmode=tk.SINGLE)
        self.categories_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        categories_scrollbar = ttk.Scrollbar(categories_frame, orient=tk.VERTICAL, command=self.categories_listbox.yview)
        categories_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.categories_listbox.config(yscrollcommand=categories_scrollbar.set)
        
        # Bind selection event
        self.categories_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        # Right pane - Tools
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        self.tools_label = ttk.Label(right_frame, text="Tools", font=("", 12, "bold"))
        self.tools_label.pack(pady=5)
        
        # Tools listbox with checkboxes
        tools_frame = ttk.Frame(right_frame)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tools_listbox = ttk.Treeview(
            tools_frame, 
            columns=("Name", "Description", "Status"),
            show="headings",
            selectmode="extended"
        )
        self.tools_listbox.heading("Name", text="Name")
        self.tools_listbox.heading("Description", text="Description")
        self.tools_listbox.heading("Status", text="Status")
        
        self.tools_listbox.column("Name", width=150, anchor=tk.W)
        self.tools_listbox.column("Description", width=400, anchor=tk.W)
        self.tools_listbox.column("Status", width=100, anchor=tk.CENTER)
        
        self.tools_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tools_scrollbar = ttk.Scrollbar(tools_frame, orient=tk.VERTICAL, command=self.tools_listbox.yview)
        tools_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tools_listbox.config(yscrollcommand=tools_scrollbar.set)
        
        # Action buttons
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X, pady=10)
        
        install_selected_btn = ttk.Button(
            actions_frame, 
            text="Install Selected", 
            command=self.install_selected_tools,
            style="Success.TButton"
        )
        install_selected_btn.pack(side=tk.LEFT, padx=5)
        
        install_all_btn = ttk.Button(
            actions_frame, 
            text="Install All in Category", 
            command=self.install_all_tools
        )
        install_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Load categories
        self.load_categories()
    
    def create_tool_management_tab(self):
        """Create the tool management tab for updating and removing tools."""
        tool_tab = ttk.Frame(self.notebook)
        self.notebook.add(tool_tab, text="Tool Management")
        
        # Split into two panes
        paned = ttk.PanedWindow(tool_tab, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top pane - Updates
        update_frame = ttk.LabelFrame(paned, text="Tool Updates")
        paned.add(update_frame, weight=1)
        
        update_actions = ttk.Frame(update_frame)
        update_actions.pack(fill=tk.X, pady=5)
        
        check_updates_btn = ttk.Button(
            update_actions, 
            text="Check for Updates", 
            command=self.check_for_updates
        )
        check_updates_btn.pack(side=tk.LEFT, padx=5)
        
        update_all_btn = ttk.Button(
            update_actions, 
            text="Update All Tools", 
            command=self.update_all_tools,
            style="Success.TButton"
        )
        update_all_btn.pack(side=tk.LEFT, padx=5)
        
        update_selected_btn = ttk.Button(
            update_actions, 
            text="Update Selected", 
            command=self.update_selected_tools
        )
        update_selected_btn.pack(side=tk.LEFT, padx=5)
        
        # Updates treeview
        updates_tree_frame = ttk.Frame(update_frame)
        updates_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.updates_tree = ttk.Treeview(
            updates_tree_frame, 
            columns=("Tool", "Current Version", "Available Version", "Status"),
            show="headings",
            selectmode="extended"
        )
        self.updates_tree.heading("Tool", text="Tool")
        self.updates_tree.heading("Current Version", text="Current Version")
        self.updates_tree.heading("Available Version", text="Available Version")
        self.updates_tree.heading("Status", text="Status")
        
        self.updates_tree.column("Tool", width=150, anchor=tk.W)
        self.updates_tree.column("Current Version", width=150, anchor=tk.CENTER)
        self.updates_tree.column("Available Version", width=150, anchor=tk.CENTER)
        self.updates_tree.column("Status", width=100, anchor=tk.CENTER)
        
        self.updates_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        updates_scrollbar = ttk.Scrollbar(updates_tree_frame, orient=tk.VERTICAL, command=self.updates_tree.yview)
        updates_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.updates_tree.config(yscrollcommand=updates_scrollbar.set)
        
        # Bottom pane - Tool Removal
        removal_frame = ttk.LabelFrame(paned, text="Tool Removal")
        paned.add(removal_frame, weight=1)
        
        removal_actions = ttk.Frame(removal_frame)
        removal_actions.pack(fill=tk.X, pady=5)
        
        refresh_installed_btn = ttk.Button(
            removal_actions, 
            text="Refresh Installed Tools", 
            command=self.refresh_installed_tools
        )
        refresh_installed_btn.pack(side=tk.LEFT, padx=5)
        
        remove_selected_btn = ttk.Button(
            removal_actions, 
            text="Remove Selected", 
            command=self.remove_selected_tools,
            style="Danger.TButton"
        )
        remove_selected_btn.pack(side=tk.LEFT, padx=5)
        
        # Installed tools treeview
        installed_tree_frame = ttk.Frame(removal_frame)
        installed_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.installed_tree = ttk.Treeview(
            installed_tree_frame, 
            columns=("Tool", "Version", "Description"),
            show="headings",
            selectmode="extended"
        )
        self.installed_tree.heading("Tool", text="Tool")
        self.installed_tree.heading("Version", text="Version")
        self.installed_tree.heading("Description", text="Description")
        
        self.installed_tree.column("Tool", width=150, anchor=tk.W)
        self.installed_tree.column("Version", width=100, anchor=tk.CENTER)
        self.installed_tree.column("Description", width=400, anchor=tk.W)
        
        self.installed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        installed_scrollbar = ttk.Scrollbar(installed_tree_frame, orient=tk.VERTICAL, command=self.installed_tree.yview)
        installed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.installed_tree.config(yscrollcommand=installed_scrollbar.set)
    
    def create_reporting_tab(self):
        """Create the reporting tab for generating reports about installed tools."""
        report_tab = ttk.Frame(self.notebook)
        self.notebook.add(report_tab, text="Reporting")
        
        # Report options
        options_frame = ttk.LabelFrame(report_tab, text="Report Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Report type
        ttk.Label(options_frame, text="Report Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.report_type = tk.StringVar(value="installed")
        installed_radio = ttk.Radiobutton(
            options_frame, 
            text="Installed Tools", 
            variable=self.report_type, 
            value="installed"
        )
        installed_radio.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        updates_radio = ttk.Radiobutton(
            options_frame, 
            text="Available Updates", 
            variable=self.report_type, 
            value="updates"
        )
        updates_radio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        history_radio = ttk.Radiobutton(
            options_frame, 
            text="Installation History", 
            variable=self.report_type, 
            value="history"
        )
        history_radio.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Format options
        ttk.Label(options_frame, text="Format:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.report_format = tk.StringVar(value="txt")
        txt_radio = ttk.Radiobutton(
            options_frame, 
            text="Text", 
            variable=self.report_format, 
            value="txt"
        )
        txt_radio.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        csv_radio = ttk.Radiobutton(
            options_frame, 
            text="CSV", 
            variable=self.report_format, 
            value="csv"
        )
        csv_radio.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        json_radio = ttk.Radiobutton(
            options_frame, 
            text="JSON", 
            variable=self.report_format, 
            value="json"
        )
        json_radio.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Generate button
        generate_frame = ttk.Frame(options_frame)
        generate_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        generate_btn = ttk.Button(
            generate_frame, 
            text="Generate Report", 
            command=self.generate_report
        )
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(
            generate_frame, 
            text="Export Configuration", 
            command=self.export_configuration
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Report preview
        preview_frame = ttk.LabelFrame(report_tab, text="Report Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(preview_frame, wrap=tk.WORD)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(report_tab)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        save_btn = ttk.Button(
            action_frame, 
            text="Save Report to File", 
            command=self.save_report
        )
        save_btn.pack(side=tk.RIGHT, padx=5)
    
    # Repository tab methods
    def add_repository(self):
        """Add the Kali Linux repository."""
        try:
            self.status_var.set("Adding Kali repository...")
            self.root.update_idletasks()
            
            self.repository_manager.add_repository()
            
            messagebox.showinfo(
                "Success", 
                "Kali Linux repository added successfully."
            )
            self.refresh_sources_list()
            self.status_var.set("Kali repository added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add repository: {str(e)}")
            self.status_var.set("Failed to add repository")
    
    def add_key(self):
        """Add the Kali Linux GPG key."""
        try:
            self.status_var.set("Adding Kali GPG key...")
            self.root.update_idletasks()
            
            self.repository_manager.add_key()
            
            messagebox.showinfo(
                "Success", 
                "Kali Linux GPG key added successfully."
            )
            self.status_var.set("Kali GPG key added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add GPG key: {str(e)}")
            self.status_var.set("Failed to add GPG key")
    
    def delete_repository(self):
        """Delete the Kali Linux repository."""
        if messagebox.askyesno(
            "Confirm Deletion", 
            "Are you sure you want to delete the Kali Linux repository? This will remove the ability to install Kali tools."
        ):
            try:
                self.status_var.set("Deleting Kali repository...")
                self.root.update_idletasks()
                
                self.repository_manager.delete_repository()
                
                messagebox.showinfo(
                    "Success", 
                    "Kali Linux repository deleted successfully."
                )
                self.refresh_sources_list()
                self.status_var.set("Kali repository deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete repository: {str(e)}")
                self.status_var.set("Failed to delete repository")
    
    def update_repositories(self):
        """Update the package repositories."""
        try:
            self.status_var.set("Updating repositories...")
            self.root.update_idletasks()
            
            self.repository_manager.update_repositories()
            
            messagebox.showinfo(
                "Success", 
                "Repositories updated successfully."
            )
            self.status_var.set("Repositories updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update repositories: {str(e)}")
            self.status_var.set("Failed to update repositories")
    
    def add_custom_repository(self):
        """Add a custom repository."""
        name = self.custom_repo_name.get().strip()
        url = self.custom_repo_url.get().strip()
        dist = self.custom_repo_dist.get().strip()
        comp = self.custom_repo_comp.get().strip()
        key_url = self.custom_repo_key.get().strip()
        
        if not name or not url or not dist or not comp:
            messagebox.showerror(
                "Input Error", 
                "Please fill in all required fields (Name, URL, Distribution, Components)."
            )
            return
        
        try:
            self.status_var.set("Adding custom repository...")
            self.root.update_idletasks()
            
            repo_info = {
                "name": name,
                "url": url,
                "distribution": dist,
                "components": comp,
                "key_url": key_url if key_url else None
            }
            
            self.repository_manager.add_repository(repo_info)
            
            if key_url:
                self.repository_manager.add_custom_key(repo_info)
            
            messagebox.showinfo(
                "Success", 
                "Custom repository added successfully."
            )
            self.refresh_sources_list()
            
            # Clear the fields
            self.custom_repo_name.delete(0, tk.END)
            self.custom_repo_url.delete(0, tk.END)
            self.custom_repo_dist.delete(0, tk.END)
            self.custom_repo_comp.delete(0, tk.END)
            self.custom_repo_key.delete(0, tk.END)
            
            self.status_var.set("Custom repository added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add custom repository: {str(e)}")
            self.status_var.set("Failed to add custom repository")
    
    def refresh_sources_list(self):
        """Refresh the sources list display."""
        try:
            sources = self.repository_manager.view_sources_list()
            
            self.sources_text.delete(1.0, tk.END)
            self.sources_text.insert(tk.END, sources)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh sources list: {str(e)}")
    
    # Categories tab methods
    def load_categories(self):
        """Load the categories into the listbox."""
        try:
            categories = self.category_manager.get_all_categories()
            
            self.categories_listbox.delete(0, tk.END)
            
            for i, category in enumerate(categories):
                formatted_name = self.category_manager.format_category_name(category)
                self.categories_listbox.insert(tk.END, formatted_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories: {str(e)}")
    
    def on_category_select(self, event):
        """Handle category selection event."""
        try:
            selection = self.categories_listbox.curselection()
            if not selection:
                return
            
            category_id = selection[0]
            category_name = self.category_manager.get_category_name(category_id)
            
            self.tools_label.config(text=f"Tools in {category_name}")
            
            # Clear the tools listbox
            for item in self.tools_listbox.get_children():
                self.tools_listbox.delete(item)
            
            # Get tools for the selected category
            tools = self.category_manager.get_category_tools(category_id)
            
            # Add tools to the listbox
            for tool_name, tool_info in tools.items():
                description = tool_info.get('description', 'No description available')
                
                # Check if the tool is installed
                try:
                    is_installed = self.tool_manager.check_installed(tool_name)
                    status = "Installed" if is_installed else "Not Installed"
                except:
                    status = "Unknown"
                
                self.tools_listbox.insert("", tk.END, values=(tool_name, description, status))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tools: {str(e)}")
    
    def search_tools(self):
        """Search for tools by name."""
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showinfo("Search", "Please enter a search term.")
            return
        
        try:
            # Clear the tools listbox
            for item in self.tools_listbox.get_children():
                self.tools_listbox.delete(item)
            
            # Search for tools
            results = self.category_manager.search_tool(search_term)
            
            if not results:
                self.tools_label.config(text=f"No tools found for '{search_term}'")
                return
            
            self.tools_label.config(text=f"Search results for '{search_term}'")
            
            # Add results to the listbox
            for tool_name, tool_info in results.items():
                description = tool_info.get('description', 'No description available')
                category = tool_info.get('category', 'Unknown')
                
                # Check if the tool is installed
                try:
                    is_installed = self.tool_manager.check_installed(tool_name)
                    status = "Installed" if is_installed else "Not Installed"
                except:
                    status = "Unknown"
                
                self.tools_listbox.insert("", tk.END, values=(tool_name, f"{description} (Category: {category})", status))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search tools: {str(e)}")
    
    def install_selected_tools(self):
        """Install the selected tools."""
        selection = self.tools_listbox.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select tools to install.")
            return
        
        tools_to_install = []
        for item_id in selection:
            tool_name = self.tools_listbox.item(item_id, "values")[0]
            tools_to_install.append(tool_name)
        
        if not tools_to_install:
            return
        
        if messagebox.askyesno(
            "Confirm Installation", 
            f"Are you sure you want to install the following tools?\n\n{', '.join(tools_to_install)}"
        ):
            try:
                self.status_var.set(f"Installing {len(tools_to_install)} tools...")
                self.root.update_idletasks()
                
                # Create a progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Installation Progress")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text="Installing tools...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=10)
                
                # Start installation in a separate thread
                import threading
                
                def install_thread():
                    try:
                        for i, tool in enumerate(tools_to_install):
                            progress_window.after(
                                0, 
                                status_label.config, 
                                {"text": f"Installing {tool} ({i+1}/{len(tools_to_install)})"}
                            )
                            self.tool_manager.install_tool(tool, skip_confirmation=True)
                        
                        progress_window.after(
                            0, 
                            messagebox.showinfo, 
                            "Success", 
                            "Tools installed successfully."
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Tools installed successfully")
                        
                        # Refresh the tools list to update status
                        selection = self.categories_listbox.curselection()
                        if selection:
                            self.on_category_select(None)
                    except Exception as e:
                        progress_window.after(
                            0, 
                            messagebox.showerror, 
                            "Error", 
                            f"Failed to install tools: {str(e)}"
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Failed to install tools")
                
                thread = threading.Thread(target=install_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to install tools: {str(e)}")
                self.status_var.set("Failed to install tools")
    
    def install_all_tools(self):
        """Install all tools in the current category."""
        selection = self.categories_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a category first.")
            return
        
        category_id = selection[0]
        category_name = self.category_manager.get_category_name(category_id)
        tools = self.category_manager.get_category_tools(category_id)
        
        if not tools:
            messagebox.showinfo("Empty Category", "This category has no tools to install.")
            return
        
        tools_to_install = list(tools.keys())
        
        if messagebox.askyesno(
            "Confirm Installation", 
            f"Are you sure you want to install all tools in the '{category_name}' category?\n\nThis will install {len(tools_to_install)} tools."
        ):
            try:
                self.status_var.set(f"Installing all tools in {category_name}...")
                self.root.update_idletasks()
                
                # Create a progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Installation Progress")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text=f"Installing all tools in {category_name}...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=10)
                
                # Start installation in a separate thread
                import threading
                
                def install_thread():
                    try:
                        for i, tool in enumerate(tools_to_install):
                            progress_window.after(
                                0, 
                                status_label.config, 
                                {"text": f"Installing {tool} ({i+1}/{len(tools_to_install)})"}
                            )
                            self.tool_manager.install_tool(tool, skip_confirmation=True)
                        
                        progress_window.after(
                            0, 
                            messagebox.showinfo, 
                            "Success", 
                            f"All tools in {category_name} installed successfully."
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set(f"All tools in {category_name} installed successfully")
                        
                        # Refresh the tools list to update status
                        self.on_category_select(None)
                    except Exception as e:
                        progress_window.after(
                            0, 
                            messagebox.showerror, 
                            "Error", 
                            f"Failed to install tools: {str(e)}"
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Failed to install tools")
                
                thread = threading.Thread(target=install_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to install tools: {str(e)}")
                self.status_var.set("Failed to install tools")
    
    # Tool management tab methods
    def check_for_updates(self):
        """Check for updates to installed tools."""
        try:
            self.status_var.set("Checking for updates...")
            self.root.update_idletasks()
            
            # Clear the updates tree
            for item in self.updates_tree.get_children():
                self.updates_tree.delete(item)
            
            # Check for updates
            update_info = self.tool_manager.check_for_updates()
            
            if not update_info:
                messagebox.showinfo(
                    "Updates", 
                    "No installed tools found or all tools are up to date."
                )
                self.status_var.set("No updates available")
                return
            
            # Add updates to the tree
            for tool_name, info in update_info.items():
                current_version = info.get('current_version', 'Unknown')
                available_version = info.get('available_version', 'Unknown')
                status = info.get('status', 'Unknown')
                
                self.updates_tree.insert(
                    "", 
                    tk.END, 
                    values=(tool_name, current_version, available_version, status)
                )
            
            self.status_var.set("Update check completed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")
            self.status_var.set("Failed to check for updates")
    
    def update_all_tools(self):
        """Update all installed tools."""
        if messagebox.askyesno(
            "Confirm Update", 
            "Are you sure you want to update all installed tools?"
        ):
            try:
                self.status_var.set("Updating all tools...")
                self.root.update_idletasks()
                
                # Create a progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Update Progress")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text="Updating all tools...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=10)
                
                # Start update in a separate thread
                import threading
                
                def update_thread():
                    try:
                        # First check for updates to get the list of tools
                        update_info = self.tool_manager.check_for_updates()
                        tools_to_update = [tool for tool, info in update_info.items() 
                                          if info.get('status') == 'Update Available']
                        
                        if not tools_to_update:
                            progress_window.after(
                                0, 
                                messagebox.showinfo, 
                                "Updates", 
                                "All tools are already up to date."
                            )
                            progress_window.after(0, progress_window.destroy)
                            self.status_var.set("All tools are up to date")
                            return
                        
                        for i, tool in enumerate(tools_to_update):
                            progress_window.after(
                                0, 
                                status_label.config, 
                                {"text": f"Updating {tool} ({i+1}/{len(tools_to_update)})"}
                            )
                            self.tool_manager.update_tool(tool)
                        
                        progress_window.after(
                            0, 
                            messagebox.showinfo, 
                            "Success", 
                            "All tools updated successfully."
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("All tools updated successfully")
                        
                        # Refresh the updates tree
                        self.check_for_updates()
                    except Exception as e:
                        progress_window.after(
                            0, 
                            messagebox.showerror, 
                            "Error", 
                            f"Failed to update tools: {str(e)}"
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Failed to update tools")
                
                thread = threading.Thread(target=update_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update tools: {str(e)}")
                self.status_var.set("Failed to update tools")
    
    def update_selected_tools(self):
        """Update the selected tools."""
        selection = self.updates_tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select tools to update.")
            return
        
        tools_to_update = []
        for item_id in selection:
            tool_name = self.updates_tree.item(item_id, "values")[0]
            tools_to_update.append(tool_name)
        
        if not tools_to_update:
            return
        
        if messagebox.askyesno(
            "Confirm Update", 
            f"Are you sure you want to update the following tools?\n\n{', '.join(tools_to_update)}"
        ):
            try:
                self.status_var.set(f"Updating {len(tools_to_update)} tools...")
                self.root.update_idletasks()
                
                # Create a progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Update Progress")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text="Updating tools...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=10)
                
                # Start update in a separate thread
                import threading
                
                def update_thread():
                    try:
                        for i, tool in enumerate(tools_to_update):
                            progress_window.after(
                                0, 
                                status_label.config, 
                                {"text": f"Updating {tool} ({i+1}/{len(tools_to_update)})"}
                            )
                            self.tool_manager.update_tool(tool)
                        
                        progress_window.after(
                            0, 
                            messagebox.showinfo, 
                            "Success", 
                            "Tools updated successfully."
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Tools updated successfully")
                        
                        # Refresh the updates tree
                        self.check_for_updates()
                    except Exception as e:
                        progress_window.after(
                            0, 
                            messagebox.showerror, 
                            "Error", 
                            f"Failed to update tools: {str(e)}"
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Failed to update tools")
                
                thread = threading.Thread(target=update_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update tools: {str(e)}")
                self.status_var.set("Failed to update tools")
    
    def refresh_installed_tools(self):
        """Refresh the list of installed tools."""
        try:
            self.status_var.set("Refreshing installed tools...")
            self.root.update_idletasks()
            
            # Clear the installed tools tree
            for item in self.installed_tree.get_children():
                self.installed_tree.delete(item)
            
            # Get all categories and tools
            categories = self.category_manager.get_all_categories()
            all_tools = {}
            
            for i, _ in enumerate(categories):
                tools = self.category_manager.get_category_tools(i)
                all_tools.update(tools)
            
            # Check which tools are installed
            installed_tools = []
            for tool_name, tool_info in all_tools.items():
                try:
                    if self.tool_manager.check_installed(tool_name):
                        version = self.tool_manager.get_installed_version(tool_name)
                        description = tool_info.get('description', 'No description available')
                        installed_tools.append((tool_name, version, description))
                except:
                    pass
            
            # Add installed tools to the tree
            for tool_name, version, description in installed_tools:
                self.installed_tree.insert(
                    "", 
                    tk.END, 
                    values=(tool_name, version, description)
                )
            
            self.status_var.set(f"Found {len(installed_tools)} installed tools")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh installed tools: {str(e)}")
            self.status_var.set("Failed to refresh installed tools")
    
    def remove_selected_tools(self):
        """Remove the selected tools."""
        selection = self.installed_tree.selection()
        if not selection:
            messagebox.showinfo("Selection", "Please select tools to remove.")
            return
        
        tools_to_remove = []
        for item_id in selection:
            tool_name = self.installed_tree.item(item_id, "values")[0]
            tools_to_remove.append(tool_name)
        
        if not tools_to_remove:
            return
        
        if messagebox.askyesno(
            "Confirm Removal", 
            f"Are you sure you want to remove the following tools?\n\n{', '.join(tools_to_remove)}"
        ):
            try:
                self.status_var.set(f"Removing {len(tools_to_remove)} tools...")
                self.root.update_idletasks()
                
                # Create a progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Removal Progress")
                progress_window.geometry("400x200")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text="Removing tools...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill=tk.X, padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=10)
                
                # Start removal in a separate thread
                import threading
                
                def remove_thread():
                    try:
                        for i, tool in enumerate(tools_to_remove):
                            progress_window.after(
                                0, 
                                status_label.config, 
                                {"text": f"Removing {tool} ({i+1}/{len(tools_to_remove)})"}
                            )
                            self.tool_manager.remove_tool(tool, skip_confirmation=True)
                        
                        progress_window.after(
                            0, 
                            messagebox.showinfo, 
                            "Success", 
                            "Tools removed successfully."
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Tools removed successfully")
                        
                        # Refresh the installed tools list
                        self.refresh_installed_tools()
                    except Exception as e:
                        progress_window.after(
                            0, 
                            messagebox.showerror, 
                            "Error", 
                            f"Failed to remove tools: {str(e)}"
                        )
                        progress_window.after(0, progress_window.destroy)
                        self.status_var.set("Failed to remove tools")
                
                thread = threading.Thread(target=remove_thread)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove tools: {str(e)}")
                self.status_var.set("Failed to remove tools")
    
    # Reporting tab methods
    def generate_report(self):
        """Generate a report based on the selected options."""
        report_type = self.report_type.get()
        report_format = self.report_format.get()
        
        try:
            self.status_var.set(f"Generating {report_type} report...")
            self.root.update_idletasks()
            
            # Clear the report text
            self.report_text.delete(1.0, tk.END)
            
            if report_type == "installed":
                report_content = self.generate_installed_tools_report(report_format)
            elif report_type == "updates":
                report_content = self.generate_updates_report(report_format)
            elif report_type == "history":
                report_content = self.generate_history_report(report_format)
            else:
                messagebox.showerror("Error", f"Unknown report type: {report_type}")
                return
            
            self.report_text.insert(tk.END, report_content)
            self.status_var.set(f"{report_type.capitalize()} report generated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            self.status_var.set("Failed to generate report")
    
    def generate_installed_tools_report(self, format_type):
        """Generate a report of installed tools."""
        import datetime
        import json
        import csv
        import io
        
        # Get all categories and tools
        categories = self.category_manager.get_all_categories()
        all_tools = {}
        
        for i, _ in enumerate(categories):
            tools = self.category_manager.get_category_tools(i)
            all_tools.update(tools)
        
        # Check which tools are installed
        installed_tools = []
        for tool_name, tool_info in all_tools.items():
            try:
                if self.tool_manager.check_installed(tool_name):
                    version = self.tool_manager.get_installed_version(tool_name)
                    description = tool_info.get('description', 'No description available')
                    category = tool_info.get('category', 'Unknown')
                    installed_tools.append({
                        'name': tool_name,
                        'version': version,
                        'description': description,
                        'category': category
                    })
            except:
                pass
        
        # Generate report based on format
        if format_type == "txt":
            report = f"Installed Tools Report\n"
            report += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"Total tools installed: {len(installed_tools)}\n\n"
            
            # Group by category
            by_category = {}
            for tool in installed_tools:
                category = tool['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(tool)
            
            for category, tools in by_category.items():
                report += f"Category: {category}\n"
                report += "-" * 50 + "\n"
                
                for tool in tools:
                    report += f"Tool: {tool['name']}\n"
                    report += f"Version: {tool['version']}\n"
                    report += f"Description: {tool['description']}\n"
                    report += "-" * 30 + "\n"
                
                report += "\n"
            
            return report
        
        elif format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Name", "Version", "Description", "Category"])
            for tool in installed_tools:
                writer.writerow([
                    tool['name'],
                    tool['version'],
                    tool['description'],
                    tool['category']
                ])
            
            return output.getvalue()
        
        elif format_type == "json":
            report_data = {
                "report_type": "installed_tools",
                "generated_at": datetime.datetime.now().isoformat(),
                "total_tools": len(installed_tools),
                "tools": installed_tools
            }
            
            return json.dumps(report_data, indent=2)
        
        else:
            return f"Unsupported format: {format_type}"
    
    def generate_updates_report(self, format_type):
        """Generate a report of available updates."""
        import datetime
        import json
        import csv
        import io
        
        # Check for updates
        update_info = self.tool_manager.check_for_updates()
        
        # Filter to only include tools with updates available
        updates_available = {
            tool: info for tool, info in update_info.items()
            if info.get('status') == 'Update Available'
        }
        
        # Generate report based on format
        if format_type == "txt":
            report = f"Available Updates Report\n"
            report += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"Total updates available: {len(updates_available)}\n\n"
            
            for tool_name, info in updates_available.items():
                report += f"Tool: {tool_name}\n"
                report += f"Current Version: {info.get('current_version', 'Unknown')}\n"
                report += f"Available Version: {info.get('available_version', 'Unknown')}\n"
                report += "-" * 30 + "\n"
            
            return report
        
        elif format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Name", "Current Version", "Available Version"])
            for tool_name, info in updates_available.items():
                writer.writerow([
                    tool_name,
                    info.get('current_version', 'Unknown'),
                    info.get('available_version', 'Unknown')
                ])
            
            return output.getvalue()
        
        elif format_type == "json":
            report_data = {
                "report_type": "available_updates",
                "generated_at": datetime.datetime.now().isoformat(),
                "total_updates": len(updates_available),
                "updates": {
                    tool: {
                        "current_version": info.get('current_version', 'Unknown'),
                        "available_version": info.get('available_version', 'Unknown')
                    }
                    for tool, info in updates_available.items()
                }
            }
            
            return json.dumps(report_data, indent=2)
        
        else:
            return f"Unsupported format: {format_type}"
    
    def generate_history_report(self, format_type):
        """Generate a report of installation history."""
        import datetime
        import json
        import csv
        import io
        
        # Note: This is a placeholder since we don't currently track installation history
        # In a real implementation, we would retrieve this from a database or log file
        
        # Generate report based on format
        if format_type == "txt":
            report = f"Installation History Report\n"
            report += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"Note: Installation history tracking is not yet implemented.\n"
            report += f"This feature will be available in a future update.\n"
            
            return report
        
        elif format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Note"])
            writer.writerow(["Installation history tracking is not yet implemented."])
            writer.writerow(["This feature will be available in a future update."])
            
            return output.getvalue()
        
        elif format_type == "json":
            report_data = {
                "report_type": "installation_history",
                "generated_at": datetime.datetime.now().isoformat(),
                "note": "Installation history tracking is not yet implemented. This feature will be available in a future update."
            }
            
            return json.dumps(report_data, indent=2)
        
        else:
            return f"Unsupported format: {format_type}"
    
    def export_configuration(self):
        """Export the current configuration to a file."""
        try:
            self.status_var.set("Exporting configuration...")
            self.root.update_idletasks()
            
            # Get the sources list
            sources = self.repository_manager.view_sources_list()
            
            # Get installed tools
            categories = self.category_manager.get_all_categories()
            all_tools = {}
            
            for i, _ in enumerate(categories):
                tools = self.category_manager.get_category_tools(i)
                all_tools.update(tools)
            
            installed_tools = []
            for tool_name in all_tools:
                try:
                    if self.tool_manager.check_installed(tool_name):
                        installed_tools.append(tool_name)
                except:
                    pass
            
            # Create configuration data
            import datetime
            import json
            
            config_data = {
                "exported_at": datetime.datetime.now().isoformat(),
                "sources_list": sources,
                "installed_tools": installed_tools
            }
            
            # Ask user where to save the file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Configuration As"
            )
            
            if not file_path:
                self.status_var.set("Export cancelled")
                return
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            messagebox.showinfo(
                "Success", 
                f"Configuration exported successfully to {file_path}"
            )
            self.status_var.set("Configuration exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export configuration: {str(e)}")
            self.status_var.set("Failed to export configuration")
    
    def save_report(self):
        """Save the current report to a file."""
        report_type = self.report_type.get()
        report_format = self.report_format.get()
        
        # Get the report content
        report_content = self.report_text.get(1.0, tk.END)
        
        if not report_content.strip():
            messagebox.showinfo("Empty Report", "Please generate a report first.")
            return
        
        # Determine file extension
        if report_format == "txt":
            file_ext = ".txt"
            file_type = "Text files"
        elif report_format == "csv":
            file_ext = ".csv"
            file_type = "CSV files"
        elif report_format == "json":
            file_ext = ".json"
            file_type = "JSON files"
        else:
            file_ext = ".txt"
            file_type = "Text files"
        
        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=[(file_type, f"*{file_ext}"), ("All files", "*.*")],
            title="Save Report As"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                f.write(report_content)
            
            messagebox.showinfo(
                "Success", 
                f"Report saved successfully to {file_path}"
            )
            self.status_var.set("Report saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")
            self.status_var.set("Failed to save report")


def main():
    """Main function to start the GUI application."""
    root = tk.Tk()
    app = KatoolinGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()