#!/usr/bin/env python3

"""
Plugin system for Katoolin tool categories and repositories.
This module provides functionality for loading and managing plugins that can add
new tool categories and custom repositories to Katoolin.
"""

import os
import importlib.util
import sys
from typing import Dict, List, Any, Optional, Tuple

class PluginInterface:
    """
    Interface that all plugins must implement.
    """
    def get_name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: Name of the plugin
        """
        raise NotImplementedError("Plugin must implement get_name method")
    
    def get_categories(self) -> Dict[int, List[Any]]:
        """
        Get the categories provided by this plugin.
        
        Returns:
            Dict[int, List[Any]]: Dictionary of category IDs and their data
                                 (similar to the format in core.categories)
        """
        raise NotImplementedError("Plugin must implement get_categories method")
    
    def get_repositories(self) -> List[Dict[str, str]]:
        """
        Get the repositories provided by this plugin.
        
        Returns:
            List[Dict[str, str]]: List of repository information dictionaries
                                 Each dictionary should contain:
                                 - 'name': Repository name
                                 - 'url': Repository URL
                                 - 'components': Repository components (e.g., 'main contrib non-free')
                                 - 'key_url': URL for the repository's GPG key (optional)
                                 - 'key_id': ID of the repository's GPG key (optional)
        """
        return []  # Default implementation returns an empty list (no repositories)

class PluginManager:
    """
    Class for managing plugins.
    """
    def __init__(self, plugin_dir: str = "plugins"):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dir (str): Directory where plugins are stored
        """
        self.plugin_dir = plugin_dir
        self.plugins = []
        self.plugin_categories = {}
        self.plugin_repositories = []
        
        # Create plugin directory if it doesn't exist
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), plugin_dir), exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugin directory.
        
        Returns:
            List[str]: List of plugin module names
        """
        plugin_modules = []
        plugin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.plugin_dir)
        
        if not os.path.exists(plugin_path):
            return plugin_modules
        
        for filename in os.listdir(plugin_path):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_modules.append(filename[:-3])  # Remove .py extension
        
        return plugin_modules
    
    def load_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Load a plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin module
        
        Returns:
            Optional[PluginInterface]: Plugin instance or None if loading failed
        """
        try:
            plugin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                self.plugin_dir, 
                f"{plugin_name}.py"
            )
            
            if not os.path.exists(plugin_path):
                print(f"Plugin {plugin_name} not found at {plugin_path}")
                return None
            
            # Load the module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                print(f"Failed to load plugin {plugin_name}: Invalid module specification")
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # Find the plugin class (a class that implements PluginInterface)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr is not PluginInterface and 
                    issubclass(attr, PluginInterface)):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                print(f"No plugin class found in {plugin_name}")
                return None
            
            # Create an instance of the plugin
            plugin_instance = plugin_class()
            return plugin_instance
            
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {str(e)}")
            return None
    
    def load_all_plugins(self) -> None:
        """
        Load all available plugins.
        """
        plugin_modules = self.discover_plugins()
        
        for plugin_name in plugin_modules:
            plugin = self.load_plugin(plugin_name)
            if plugin:
                self.plugins.append(plugin)
                
                # Get categories from the plugin
                categories = plugin.get_categories()
                if categories:
                    self.plugin_categories.update(categories)
                
                # Get repositories from the plugin
                repositories = plugin.get_repositories()
                if repositories:
                    self.plugin_repositories.extend(repositories)
    
    def get_plugin_categories(self) -> Dict[int, List[Any]]:
        """
        Get all categories from loaded plugins.
        
        Returns:
            Dict[int, List[Any]]: Dictionary of category IDs and their data
        """
        return self.plugin_categories
    
    def get_plugin_repositories(self) -> List[Dict[str, str]]:
        """
        Get all repositories from loaded plugins.
        
        Returns:
            List[Dict[str, str]]: List of repository information dictionaries
        """
        return self.plugin_repositories
    
    def get_plugin_names(self) -> List[str]:
        """
        Get the names of all loaded plugins.
        
        Returns:
            List[str]: List of plugin names
        """
        return [plugin.get_name() for plugin in self.plugins]