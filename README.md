# Vik Renamer

A powerful and user-friendly bulk file renaming tool with both CLI and GUI interfaces.

## Features

- **Bulk Rename**: Handle files with all kinds of extensions
- **Dual Interface**: GUI for ease of use, CLI for power users
- **Multiple Rename Modes**: Sequential numbering, custom patterns, case changes, and regex support
- **Preview Before Action**: See exactly what will be renamed in both CLI and GUI versions
- **Comprehensive Logging**: Track operations with INFO, DEBUG, ERROR, and WARN levels
- **Safety First**: Backup option to protect your original files
- **Test Mode**: Dry run functionality to test changes without applying them

## Installation & Usage

### Quick Start
```bash
git clone https://github.com/your-username/vik-renamer.git
cd vik-renamer
python renamer.py
```

### Requirements
- Python 3.6+
- Standard library dependencies

## Build (Optional)

Want a standalone executable? Here's how:

### Prerequisites
Make sure your pip is up-to-date first:
```bash
python -m pip install --upgrade pip
```

### Build Steps
1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Create executable**:
   ```bash
   pyinstaller --onefile renamer.py
   ```

3. **Find your executable**:
   Let it do its thing and you'll have the built `.exe` in the `/dist` subfolder from wherever you've run the compiler.

## Examples

```bash
# GUI mode (default)
python renamer.py

# CLI mode with preview
python renamer.py --p --preview

# Dry run to test changes
python renamer.py [args] --dry-run #make sure the dry run arg is last
```

## Contributing

⚠️ **Newbie-Friendly Zone!** ⚠️

I'm a newbie coder and mostly a "vibe coder" who loves learning this way, so don't hesitate to:
- Leave reviews and suggestions
- Open issues for bugs or improvements
- Submit pull requests (I'll learn from them!)
- Share your renaming use cases

Every contribution helps me grow as a developer! 🚀

## Support

Having issues? Found a bug? Want to suggest a feature?
- Open an issue on GitHub
- Be patient with me as I learn and improve the code
- Help is always appreciated!

## License

This project is open source. Feel free to use, modify, and distribute.

---

**Made with ❤️ by a learning developer**
