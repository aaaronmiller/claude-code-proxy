"""
CLI Tool Session Collector

Collects and aggregates session data from popular AI coding CLI tools:
- Claude Code (~/.claude/)
- OpenCode (~/.config/opencode/)
- OpenClaw (~/.openclaw/)
- Hermes (~/.hermes/)
- Aider (~/.aider/)
- And more...

Collects:
- Session count and duration
- Token usage (if available)
- Model preferences
- Tool/plugin usage
- Command history
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class CLISessionCollector:
    """Collects session data from AI coding CLI tools."""
    
    # Known CLI tool configurations
    CLI_TOOLS = {
        'claude': {
            'name': 'Claude Code',
            'dirs': ['~/.claude'],
            'files': {
                'settings': 'settings.json',
                'history': 'history.jsonl',
                'sessions': 'session-env',
                'stats': 'stats-cache.json'
            },
            'config_files': ['CLAUDE.md', 'RTK.md', 'AGENTS.md']
        },
        'opencode': {
            'name': 'OpenCode',
            'dirs': ['~/.config/opencode'],
            'files': {
                'settings': 'settings.json',
                'sessions': 'sessions',
            },
            'config_files': ['CLAUDE.md', 'AGENTS.md', 'GEMINI.md']
        },
        'openclaw': {
            'name': 'OpenClaw',
            'dirs': ['~/.openclaw'],
            'files': {
                'sessions': 'agents/main/sessions/sessions.json',
                'workspace': 'workspace/AGENTS.md'
            },
            'config_files': ['AGENTS.md']
        },
        'hermes': {
            'name': 'Hermes Agent',
            'dirs': ['~/.hermes'],
            'files': {
                'sessions': 'sessions/sessions.json',
                'agent': 'hermes-agent/AGENTS.md'
            },
            'config_files': ['AGENTS.md', 'CLAUDE.md']
        },
        'aider': {
            'name': 'Aider',
            'dirs': ['~/.aider'],
            'files': {
                'history': 'history.json',
                'settings': 'settings.yml'
            },
            'config_files': []
        },
        'qwen': {
            'name': 'Qwen Code',
            'dirs': ['~/.qwen'],
            'files': {
                'settings': 'settings.json'
            },
            'config_files': ['AGENTS.md', 'CLAUDE.md']
        }
    }
    
    def __init__(self):
        self.home = Path.home()
        self.collected_data: Dict[str, Any] = {}
    
    def expand_path(self, path: str) -> Path:
        """Expand ~ to home directory."""
        if path.startswith('~'):
            return self.home / path[2:]  # Remove ~ and prepend home
        return Path(path)
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect data from all available CLI tools."""
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'tools': {},
            'summary': {
                'total_tools': 0,
                'total_sessions': 0,
                'total_config_files': 0
            }
        }
        
        for tool_id, config in self.CLI_TOOLS.items():
            tool_data = self.collect_tool(tool_id, config)
            if tool_data['available']:
                results['tools'][tool_id] = tool_data
                results['summary']['total_tools'] += 1
                results['summary']['total_sessions'] += tool_data.get('sessions', {}).get('count', 0)
                results['summary']['total_config_files'] += len(tool_data.get('config_files', []))
        
        self.collected_data = results
        return results
    
    def collect_tool(self, tool_id: str, config: Dict) -> Dict[str, Any]:
        """Collect data from a specific CLI tool."""
        tool_data = {
            'name': config['name'],
            'available': False,
            'settings': None,
            'sessions': {'count': 0, 'items': []},
            'config_files': [],
            'models_used': [],
            'plugins': [],
            'errors': []
        }
        
        # Check each directory
        for dir_path in config.get('dirs', []):
            expanded = self.expand_path(dir_path)
            if expanded.exists():
                tool_data['available'] = True
                
                # Collect settings
                if 'settings' in config.get('files', {}):
                    settings_file = expanded / config['files']['settings']
                    if settings_file.exists():
                        try:
                            with open(settings_file, 'r') as f:
                                if settings_file.suffix == '.json':
                                    tool_data['settings'] = json.load(f)
                                else:
                                    tool_data['settings'] = {'raw': settings_file.read_text()[:1000]}
                        except Exception as e:
                            tool_data['errors'].append(f"Settings error: {e}")
                
                # Collect sessions
                if 'sessions' in config.get('files', {}):
                    sessions_path = expanded / config['files']['sessions']
                    if sessions_path.exists():
                        if sessions_path.is_file() and sessions_path.suffix == '.json':
                            try:
                                with open(sessions_path, 'r') as f:
                                    sessions = json.load(f)
                                    if isinstance(sessions, list):
                                        tool_data['sessions']['count'] = len(sessions)
                                        tool_data['sessions']['items'] = sessions[:10]  # Last 10
                                    elif isinstance(sessions, dict):
                                        tool_data['sessions']['count'] = len(sessions.get('sessions', []))
                                        tool_data['sessions']['items'] = sessions.get('sessions', [])[:10]
                            except Exception as e:
                                tool_data['errors'].append(f"Sessions error: {e}")
                        elif sessions_path.is_dir():
                            # Count subdirectories as sessions
                            session_dirs = [d for d in sessions_path.iterdir() if d.is_dir()]
                            tool_data['sessions']['count'] = len(session_dirs)
                            tool_data['sessions']['items'] = [
                                {'id': d.name, 'path': str(d)}
                                for d in sorted(session_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
                            ]
                
                # Collect session-env directories (Claude Code specific)
                session_env = expanded / 'session-env'
                if session_env.exists() and session_env.is_dir():
                    env_sessions = [d for d in session_env.iterdir() if d.is_dir()]
                    tool_data['sessions']['count'] += len(env_sessions)
                
                # Collect config files
                for config_file in config.get('config_files', []):
                    config_path = expanded / config_file
                    if config_path.exists():
                        try:
                            content = config_path.read_text()
                            tool_data['config_files'].append({
                                'name': config_file,
                                'size': len(content),
                                'lines': content.count('\n') + 1,
                                'preview': content[:500]
                            })
                        except Exception as e:
                            tool_data['errors'].append(f"Config file error: {e}")
                
                # Extract model preferences from settings
                if tool_data['settings']:
                    settings = tool_data['settings']
                    if isinstance(settings, dict):
                        if 'model' in settings:
                            tool_data['models_used'].append(settings['model'])
                        if 'models' in settings:
                            models = settings['models']
                            if isinstance(models, list):
                                tool_data['models_used'].extend(models[:5])
                            elif isinstance(models, dict):
                                tool_data['models_used'].extend(list(models.keys())[:5])
                        
                        # Extract plugins
                        if 'enabledPlugins' in settings:
                            plugins = settings['enabledPlugins']
                            if isinstance(plugins, dict):
                                tool_data['plugins'] = [k for k, v in plugins.items() if v]
                            elif isinstance(plugins, list):
                                tool_data['plugins'] = plugins[:10]
        
        return tool_data
    
    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all CLI tools."""
        if not self.collected_data:
            self.collect_all()
        
        stats = {
            'total_tools': self.collected_data['summary']['total_tools'],
            'total_sessions': self.collected_data['summary']['total_sessions'],
            'total_config_files': self.collected_data['summary']['total_config_files'],
            'tools_breakdown': {},
            'all_models': [],
            'all_plugins': [],
            'config_file_types': defaultdict(int)
        }
        
        for tool_id, tool_data in self.collected_data.get('tools', {}).items():
            stats['tools_breakdown'][tool_id] = {
                'name': tool_data['name'],
                'sessions': tool_data['sessions']['count'],
                'config_files': len(tool_data['config_files'])
            }
            
            stats['all_models'].extend(tool_data.get('models_used', []))
            stats['all_plugins'].extend(tool_data.get('plugins', []))
            
            for config_file in tool_data.get('config_files', []):
                stats['config_file_types'][config_file['name']] += 1
        
        # Deduplicate
        stats['all_models'] = list(set(stats['all_models']))
        stats['all_plugins'] = list(set(stats['all_plugins']))
        stats['config_file_types'] = dict(stats['config_file_types'])
        
        return stats
    
    def get_session_timeline(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get timeline of recent sessions across all tools."""
        timeline = []
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        for tool_id, tool_data in self.collected_data.get('tools', {}).items():
            for session in tool_data.get('sessions', {}).get('items', []):
                try:
                    # Try to extract timestamp from session
                    session_time = None
                    if 'created_at' in session:
                        session_time = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                    elif 'timestamp' in session:
                        session_time = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
                    elif 'id' in session and tool_id == 'claude':
                        # Claude session IDs don't have timestamps, use directory mtime
                        if 'path' in session:
                            session_path = Path(session['path'])
                            if session_path.exists():
                                session_time = datetime.fromtimestamp(session_path.stat().st_mtime)
                    
                    if session_time and session_time.replace(tzinfo=None) >= cutoff:
                        timeline.append({
                            'tool': tool_id,
                            'tool_name': tool_data['name'],
                            'session_id': session.get('id', 'unknown'),
                            'timestamp': session_time.isoformat() if session_time else None,
                            'data': session
                        })
                except Exception:
                    continue
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        return timeline[:50]  # Last 50 sessions


# Global collector instance
_collector: Optional[CLISessionCollector] = None


def get_collector() -> CLISessionCollector:
    """Get or create global collector instance."""
    global _collector
    if _collector is None:
        _collector = CLISessionCollector()
    return _collector


def collect_cli_sessions() -> Dict[str, Any]:
    """Collect session data from all CLI tools."""
    return get_collector().collect_all()


def get_cli_stats() -> Dict[str, Any]:
    """Get aggregate CLI tool statistics."""
    return get_collector().get_aggregate_stats()


def get_cli_timeline(days: int = 7) -> List[Dict[str, Any]]:
    """Get session timeline from CLI tools."""
    return get_collector().get_session_timeline(days)
