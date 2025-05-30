# Katoolin Plugin System

This directory contains plugins for Katoolin. Plugins allow you to extend Katoolin with new tool categories and custom repositories without modifying the core code.

## Creating a Plugin

To create a plugin, create a new Python file in this directory with a class that implements the `PluginInterface` from `core.plugins`. The file name should be descriptive of the plugin's purpose, and the class name should follow PEP 8 naming conventions.

### Plugin Interface

Your plugin class must implement the following methods:

- `get_name()`: Returns the name of the plugin as a string.
- `get_categories()`: Returns a dictionary of category IDs and their data.
- `get_repositories()` (optional): Returns a list of repository information dictionaries.

### Example Plugin

Here's an example of a simple plugin that adds a custom tool category and repositories:

```python
#!/usr/bin/env python3

from core.plugins import PluginInterface
from typing import Dict, List, Any

class MyPlugin(PluginInterface):
    def get_name(self) -> str:
        return "My Custom Plugin"
    
    def get_categories(self) -> Dict[int, List[Any]]:
        # Use a high category ID to avoid conflicts with built-in categories
        return {
            100: ['my_custom_category', 
                 ['tool1', 'tool2', 'tool3']
                 ]
        }
    
    def get_repositories(self) -> List[Dict[str, str]]:
        return [
            {
                'name': 'My Custom Repository',
                'url': 'http://my-repo.com/repo',
                'components': 'main',
                'key_url': 'http://my-repo.com/repo/key.asc'
            }
        ]
```

### Category Format

The format for categories is the same as in `core/categories.py`:

```python
{
    category_id: [category_name, [tool1, tool2, ...]]
}
```

- `category_id`: A unique integer identifier for the category. Use a high number (e.g., 100+) to avoid conflicts with built-in categories.
- `category_name`: A string name for the category. This will be formatted for display.
- `[tool1, tool2, ...]`: A list of tool names in the category.

### Repository Format

The format for repositories is:

```python
{
    'name': 'Repository Name',
    'url': 'http://repository-url.com/repo',
    'components': 'main contrib non-free',
    'key_url': 'http://repository-url.com/repo/key.asc',  # Optional
    'key_id': 'GPG_KEY_ID',  # Optional
    'keyserver': 'keyserver.ubuntu.com'  # Optional, defaults to keyserver.ubuntu.com
}
```

You must provide either `key_url` or `key_id` for the repository key, or neither if the repository doesn't require a key.

## Installing Plugins

To install a plugin, simply place the plugin file in this directory. Katoolin will automatically discover and load all plugins in this directory when it starts.

## Using Plugins

Once a plugin is installed, its categories will appear in the category list, and its repositories will be available in the "Manage custom repositories" menu under the "Add Kali repositories & Update" option.