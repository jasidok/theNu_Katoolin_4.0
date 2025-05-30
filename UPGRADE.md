# Upgrade Guide: Katoolin3 to NuKatoo4

## What's New

NuKatoo4 is a complete rewrite of the original katoolin3 script, providing better:

- **Modular architecture** - Making the code more maintainable and extensible
- **Plugin system** - Allowing easy addition of new tool categories and repositories
- **Improved error handling** - More robust operation with better user feedback
- **Modern Python code** - Using classes, typing, and better practices

## How to Upgrade

1. If you're using the old katoolin3.py, please first remove any Kali repositories you may have added
2. Update your local repository: `git pull origin master`
3. Make the new script executable: `chmod +x NuKatoo4.py`
4. Run with: `sudo ./NuKatoo4.py`

## Command Changes

All commands remain the same, but the underlying implementation is more robust.

- `back`: Go back to previous menu
- `gohome`: Return to main menu
- `exit` or `quit`: Exit the program
- `help`: Display help information

## Reporting Issues

If you encounter any issues with the new version, please report them on our GitHub issue tracker.
