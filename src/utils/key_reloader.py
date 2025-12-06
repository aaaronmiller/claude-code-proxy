import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple, Dict
from src.core.logging import logger
from src.core.config import config

class KeyReloader:
    """
    Handles reloading API keys from the user's shell profile.
    Used for seamless key rotation when 401 errors occur.
    """
    
    def __init__(self):
        self.profile_path = self._find_shell_profile()
        self.last_check_time = 0
        self.cached_keys: Dict[str, str] = {}

    def _find_shell_profile(self) -> Optional[Path]:
        """Detect the config file."""
        # Use local .env in project root
        project_root = Path(__file__).parent.parent.parent
        path = project_root / ".env"
        
        if path.exists():
            logger.debug(f"KeyReloader: Watching config at {path}")
            return path
        
        # If not exists, we can't watch it yet, but we'll try to find it later if it's created
        logger.debug(f"KeyReloader: Config file {path} does not exist yet")
        return path

    def extract_key_from_profile(self, var_name: str) -> Optional[str]:
        """
        Read the profile and extract the value of an exported variable.
        """
        if not self.profile_path:
            return None

        try:
            content = self.profile_path.read_text()
            # Look for export VAR="value" or export VAR='value' or export VAR=value
            # We look for the LAST occurrence to get the effective value
            pattern = f'export\\s+{var_name}=[\'"]?([^\'"\\n]+)[\'"]?'
            matches = list(re.finditer(pattern, content))
            
            if matches:
                # Return the last match
                return matches[-1].group(1).strip()
            
            return None
        except Exception as e:
            logger.error(f"KeyReloader: Error reading profile: {e}")
            return None

    def check_for_updates(self) -> bool:
        """
        Check if any relevant keys have changed in the profile.
        Returns True if updates were found and applied.
        """
        if not self.profile_path:
            return False

        # Check file modification time first
        try:
            mtime = self.profile_path.stat().st_mtime
            if mtime <= self.last_check_time:
                return False
            self.last_check_time = mtime
        except OSError:
            return False

        logger.info("KeyReloader: Profile modification detected, checking for key updates...")
        
        # List of keys to check
        keys_to_check = [
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "PERPLEXITY_API_KEY"
        ]
        
        updated = False
        
        for var_name in keys_to_check:
            new_value = self.extract_key_from_profile(var_name)
            if new_value:
                # Check if it's different from current env
                current_value = os.environ.get(var_name)
                
                # If we have a cached value, compare against that too
                # (in case env wasn't updated yet)
                
                if new_value != current_value:
                    logger.info(f"KeyReloader: Found new value for {var_name}")
                    
                    # Update environment
                    os.environ[var_name] = new_value
                    
                    # Update Config object
                    # We need to map specific provider keys to the generic ones config uses
                    # logic similar to config.py
                    
                    if var_name == "OPENROUTER_API_KEY":
                        # If OpenRouter key updated, update OPENAI_API_KEY if we are using OpenRouter
                        # Or just update it generally if it seems to be the primary
                        pass 
                        
                    # For now, just updating os.environ might be enough if we re-init the client
                    # But Config is a singleton, so we should update it explicitly
                    
                    if var_name == "ANTHROPIC_API_KEY":
                        config.anthropic_api_key = new_value
                    elif var_name in ["OPENAI_API_KEY", "OPENROUTER_API_KEY"]:
                        # If we are in "server mode", OPENAI_API_KEY is the main one
                        # If the user updated OPENROUTER_API_KEY, we might want to set OPENAI_API_KEY to that
                        # IF the base URL is OpenRouter.
                        
                        if "openrouter" in config.openai_base_url:
                             if var_name == "OPENROUTER_API_KEY":
                                 config.openai_api_key = new_value
                                 os.environ["OPENAI_API_KEY"] = new_value
                        elif "openai" in config.openai_base_url:
                            if var_name == "OPENAI_API_KEY":
                                config.openai_api_key = new_value
                    
                    updated = True

        return updated

# Global instance
key_reloader = KeyReloader()
