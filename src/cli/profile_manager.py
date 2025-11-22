#!/usr/bin/env python3
"""
Profile Manager CLI for Claude Code Proxy

Manage configuration profiles for easy switching between different setups.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import questionary
from questionary import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Custom style for the CLI
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])


class ProfileManager:
    """Manage configuration profiles"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.profiles_dir = self.project_root / "profiles"
        self.env_file = self.project_root / ".env"
        self.profiles_dir.mkdir(exist_ok=True)

    def list_profiles(self) -> List[Dict]:
        """List all saved profiles"""
        profiles = []

        for profile_file in sorted(self.profiles_dir.glob("*.env")):
            # Get file stats
            stats = profile_file.stat()
            modified = datetime.fromtimestamp(stats.st_mtime)

            # Read first few lines to get description
            description = ""
            try:
                with open(profile_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("# Description:"):
                            description = line.replace("# Description:", "").strip()
                            break
                        if line and not line.startswith("#"):
                            break
            except Exception:
                pass

            # Extract key config values
            config = self._read_profile_config(profile_file)

            profiles.append({
                "name": profile_file.stem,
                "path": profile_file,
                "modified": modified,
                "description": description,
                "provider": config.get("PROVIDER_BASE_URL", "").replace("https://", "").replace("/v1", ""),
                "big_model": config.get("BIG_MODEL", ""),
                "size": stats.st_size,
            })

        return profiles

    def _read_profile_config(self, profile_path: Path) -> Dict[str, str]:
        """Read configuration from a profile file"""
        config = {}
        try:
            with open(profile_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            config[key] = value
        except Exception as e:
            console.print(f"[yellow]⚠️  Error reading profile: {e}[/yellow]")
        return config

    def display_profiles(self):
        """Display profiles in a nice table"""
        profiles = self.list_profiles()

        if not profiles:
            console.print("\n[yellow]No profiles found in profiles/[/yellow]")
            console.print("Create a profile with: [cyan]python -m src.cli.profile_manager create[/cyan]\n")
            return

        table = Table(title="💾 Saved Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("BIG Model", style="yellow")
        table.add_column("Modified", style="dim")
        table.add_column("Description", style="dim")

        for profile in profiles:
            modified_str = profile['modified'].strftime("%Y-%m-%d %H:%M")
            provider = profile['provider'] or "Not set"
            big_model = profile['big_model'] or "Not set"
            description = profile['description'] or ""

            table.add_row(
                profile['name'],
                provider,
                big_model,
                modified_str,
                description,
            )

        console.print()
        console.print(table)
        console.print()

    def switch_profile(self, profile_name: str) -> bool:
        """Switch to a profile by copying it to .env"""
        profile_path = self.profiles_dir / f"{profile_name}.env"

        if not profile_path.exists():
            console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
            return False

        try:
            # Backup current .env if it exists
            if self.env_file.exists():
                backup_path = self.env_file.with_suffix(f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(self.env_file, backup_path)
                console.print(f"[dim]📦 Backed up current .env to {backup_path.name}[/dim]")

            # Copy profile to .env
            shutil.copy2(profile_path, self.env_file)
            console.print(f"\n[green]✅ Switched to profile: {profile_name}[/green]\n")

            # Show profile info
            config = self._read_profile_config(profile_path)
            console.print("[bold]Active Configuration:[/bold]")
            console.print(f"  Provider: [cyan]{config.get('PROVIDER_BASE_URL', 'Not set')}[/cyan]")
            console.print(f"  BIG Model: [yellow]{config.get('BIG_MODEL', 'Not set')}[/yellow]")
            console.print(f"  MIDDLE Model: [yellow]{config.get('MIDDLE_MODEL', 'Not set')}[/yellow]")
            console.print(f"  SMALL Model: [yellow]{config.get('SMALL_MODEL', 'Not set')}[/yellow]")
            console.print()

            return True

        except Exception as e:
            console.print(f"[red]❌ Error switching profile: {e}[/red]")
            return False

    def create_profile(self, profile_name: str, description: str = "") -> bool:
        """Create a new profile from current .env"""
        if not self.env_file.exists():
            console.print("[red]❌ No .env file found to save as profile[/red]")
            console.print("[yellow]💡 Run: python setup_wizard.py[/yellow]")
            return False

        profile_path = self.profiles_dir / f"{profile_name}.env"

        if profile_path.exists():
            overwrite = questionary.confirm(
                f"Profile '{profile_name}' already exists. Overwrite?",
                default=False,
                style=custom_style
            ).ask()

            if not overwrite:
                console.print("[yellow]❌ Profile creation cancelled[/yellow]")
                return False

        try:
            # Read current .env
            with open(self.env_file, 'r') as f:
                content = f.read()

            # Write to profile with description
            with open(profile_path, 'w') as f:
                if description:
                    f.write(f"# Description: {description}\n")
                f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"#\n")
                f.write(content)

            console.print(f"\n[green]✅ Profile '{profile_name}' created successfully[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error creating profile: {e}[/red]")
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile"""
        profile_path = self.profiles_dir / f"{profile_name}.env"

        if not profile_path.exists():
            console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
            return False

        # Confirm deletion
        confirm = questionary.confirm(
            f"Are you sure you want to delete profile '{profile_name}'?",
            default=False,
            style=custom_style
        ).ask()

        if not confirm:
            console.print("[yellow]❌ Deletion cancelled[/yellow]")
            return False

        try:
            profile_path.unlink()
            console.print(f"\n[green]✅ Profile '{profile_name}' deleted[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error deleting profile: {e}[/red]")
            return False

    def compare_profiles(self, profile1_name: str, profile2_name: str):
        """Compare two profiles"""
        profile1_path = self.profiles_dir / f"{profile1_name}.env"
        profile2_path = self.profiles_dir / f"{profile2_name}.env"

        if not profile1_path.exists():
            console.print(f"[red]❌ Profile '{profile1_name}' not found[/red]")
            return

        if not profile2_path.exists():
            console.print(f"[red]❌ Profile '{profile2_name}' not found[/red]")
            return

        config1 = self._read_profile_config(profile1_path)
        config2 = self._read_profile_config(profile2_path)

        # Get all keys
        all_keys = sorted(set(config1.keys()) | set(config2.keys()))

        # Create comparison table
        table = Table(title=f"Comparing: {profile1_name} vs {profile2_name}", show_header=True)
        table.add_column("Variable", style="cyan")
        table.add_column(profile1_name, style="green")
        table.add_column(profile2_name, style="yellow")
        table.add_column("Status", style="bold")

        for key in all_keys:
            val1 = config1.get(key, "[dim]Not set[/dim]")
            val2 = config2.get(key, "[dim]Not set[/dim]")

            if val1 == val2:
                status = "[green]✓ Same[/green]"
            elif key not in config1:
                status = "[yellow]← Missing[/yellow]"
            elif key not in config2:
                status = "[yellow]Missing →[/yellow]"
            else:
                status = "[red]✗ Different[/red]"

            table.add_row(key, val1, val2, status)

        console.print()
        console.print(table)
        console.print()

    def export_profile(self, profile_name: str, export_path: Path):
        """Export a profile to a file"""
        profile_path = self.profiles_dir / f"{profile_name}.env"

        if not profile_path.exists():
            console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
            return False

        try:
            shutil.copy2(profile_path, export_path)
            console.print(f"\n[green]✅ Profile exported to: {export_path}[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error exporting profile: {e}[/red]")
            return False

    def import_profile(self, import_path: Path, profile_name: str = None):
        """Import a profile from a file"""
        if not import_path.exists():
            console.print(f"[red]❌ File not found: {import_path}[/red]")
            return False

        # Use filename if no name provided
        if not profile_name:
            profile_name = import_path.stem

        profile_path = self.profiles_dir / f"{profile_name}.env"

        if profile_path.exists():
            overwrite = questionary.confirm(
                f"Profile '{profile_name}' already exists. Overwrite?",
                default=False,
                style=custom_style
            ).ask()

            if not overwrite:
                console.print("[yellow]❌ Import cancelled[/yellow]")
                return False

        try:
            shutil.copy2(import_path, profile_path)
            console.print(f"\n[green]✅ Profile imported as: {profile_name}[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error importing profile: {e}[/red]")
            return False

    def interactive_menu(self):
        """Show interactive menu for profile management"""
        while True:
            console.print("\n" + "="*70)
            console.print("[bold cyan]💾 Profile Manager[/bold cyan]")
            console.print("="*70 + "\n")

            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "📋 List profiles",
                    "🔄 Switch to profile",
                    "➕ Create new profile",
                    "❌ Delete profile",
                    "🔍 Compare profiles",
                    "📤 Export profile",
                    "📥 Import profile",
                    "🚪 Exit",
                ],
                style=custom_style
            ).ask()

            if action is None or "Exit" in action:
                console.print("\n[green]👋 Goodbye![/green]\n")
                break

            if "List" in action:
                self.display_profiles()

            elif "Switch" in action:
                profiles = self.list_profiles()
                if not profiles:
                    console.print("[yellow]No profiles available[/yellow]")
                    continue

                choices = [p['name'] for p in profiles]
                profile_name = questionary.select(
                    "Select profile to switch to:",
                    choices=choices,
                    style=custom_style
                ).ask()

                if profile_name:
                    self.switch_profile(profile_name)

            elif "Create" in action:
                profile_name = questionary.text(
                    "Profile name:",
                    style=custom_style
                ).ask()

                if profile_name:
                    description = questionary.text(
                        "Description (optional):",
                        default="",
                        style=custom_style
                    ).ask()

                    self.create_profile(profile_name, description)

            elif "Delete" in action:
                profiles = self.list_profiles()
                if not profiles:
                    console.print("[yellow]No profiles available[/yellow]")
                    continue

                choices = [p['name'] for p in profiles]
                profile_name = questionary.select(
                    "Select profile to delete:",
                    choices=choices,
                    style=custom_style
                ).ask()

                if profile_name:
                    self.delete_profile(profile_name)

            elif "Compare" in action:
                profiles = self.list_profiles()
                if len(profiles) < 2:
                    console.print("[yellow]Need at least 2 profiles to compare[/yellow]")
                    continue

                choices = [p['name'] for p in profiles]

                profile1 = questionary.select(
                    "First profile:",
                    choices=choices,
                    style=custom_style
                ).ask()

                profile2 = questionary.select(
                    "Second profile:",
                    choices=choices,
                    style=custom_style
                ).ask()

                if profile1 and profile2:
                    self.compare_profiles(profile1, profile2)

            elif "Export" in action:
                profiles = self.list_profiles()
                if not profiles:
                    console.print("[yellow]No profiles available[/yellow]")
                    continue

                choices = [p['name'] for p in profiles]
                profile_name = questionary.select(
                    "Select profile to export:",
                    choices=choices,
                    style=custom_style
                ).ask()

                if profile_name:
                    export_path = questionary.path(
                        "Export to:",
                        default=f"{profile_name}.env",
                    ).ask()

                    if export_path:
                        self.export_profile(profile_name, Path(export_path))

            elif "Import" in action:
                import_path = questionary.path(
                    "Import from:",
                ).ask()

                if import_path:
                    profile_name = questionary.text(
                        "Save as profile name (leave blank to use filename):",
                        default="",
                        style=custom_style
                    ).ask()

                    self.import_profile(Path(import_path), profile_name or None)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code Proxy Profile Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Interactive menu
  %(prog)s list                         # List all profiles
  %(prog)s switch production            # Switch to production profile
  %(prog)s create dev "Development"     # Create new profile
  %(prog)s delete old-config            # Delete a profile
  %(prog)s compare dev production       # Compare two profiles
  %(prog)s export production prod.env   # Export profile
  %(prog)s import custom.env custom     # Import profile
        """
    )

    parser.add_argument('action', nargs='?', choices=[
        'list', 'switch', 'create', 'delete', 'compare', 'export', 'import'
    ], help='Action to perform (omit for interactive menu)')

    parser.add_argument('args', nargs='*', help='Arguments for the action')

    args = parser.parse_args()

    manager = ProfileManager()

    if not args.action:
        # Interactive menu
        manager.interactive_menu()
        return

    # Handle CLI commands
    if args.action == 'list':
        manager.display_profiles()

    elif args.action == 'switch':
        if not args.args:
            console.print("[red]❌ Profile name required[/red]")
            console.print("Usage: profile_manager switch <profile_name>")
            sys.exit(1)

        manager.switch_profile(args.args[0])

    elif args.action == 'create':
        if not args.args:
            console.print("[red]❌ Profile name required[/red]")
            console.print("Usage: profile_manager create <profile_name> [description]")
            sys.exit(1)

        profile_name = args.args[0]
        description = ' '.join(args.args[1:]) if len(args.args) > 1 else ""
        manager.create_profile(profile_name, description)

    elif args.action == 'delete':
        if not args.args:
            console.print("[red]❌ Profile name required[/red]")
            console.print("Usage: profile_manager delete <profile_name>")
            sys.exit(1)

        manager.delete_profile(args.args[0])

    elif args.action == 'compare':
        if len(args.args) < 2:
            console.print("[red]❌ Two profile names required[/red]")
            console.print("Usage: profile_manager compare <profile1> <profile2>")
            sys.exit(1)

        manager.compare_profiles(args.args[0], args.args[1])

    elif args.action == 'export':
        if len(args.args) < 2:
            console.print("[red]❌ Profile name and export path required[/red]")
            console.print("Usage: profile_manager export <profile_name> <export_path>")
            sys.exit(1)

        manager.export_profile(args.args[0], Path(args.args[1]))

    elif args.action == 'import':
        if not args.args:
            console.print("[red]❌ Import path required[/red]")
            console.print("Usage: profile_manager import <import_path> [profile_name]")
            sys.exit(1)

        import_path = Path(args.args[0])
        profile_name = args.args[1] if len(args.args) > 1 else None
        manager.import_profile(import_path, profile_name)


if __name__ == "__main__":
    main()
