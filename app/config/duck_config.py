import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class DuckConfig:
    """Duck configuration manager that loads and provides access to duck configurations."""

    def __init__(self, config_dir: Path = None):
        """
        Initialize the duck configuration manager.
        
        Args:
            config_dir: Directory containing duck configuration files. If None, 
                        uses the default 'ducks' directory under the current module.
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent / 'ducks'
        else:
            self.config_dir = config_dir
            
        self.duck_types = {}
        self.internal_name_map = {}
        self.load_all_configs()
    
    def load_all_configs(self) -> None:
        """Load all duck configuration files from the config directory."""
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Duck configuration directory does not exist: {self.config_dir}")
            
        for file_path in self.config_dir.glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                    duck_id = config.get('id')
                    if duck_id:
                        self.duck_types[duck_id] = config
                        
                        # Build internal name mapping
                        for variant_id, variant in config.get('variants', {}).items():
                            internal_name = variant.get('internal_name')
                            if internal_name:
                                self.internal_name_map[internal_name] = {
                                    'duck_type': duck_id,
                                    'variant': variant_id
                                }
            except Exception as e:
                print(f"Error loading duck configuration file {file_path}: {e}")
    
    def get_duck_types(self) -> Dict[str, Any]:
        """Get all duck types."""
        return self.duck_types
    
    def get_duck_type(self, duck_type: str) -> Optional[Dict[str, Any]]:
        """Get a specific duck type configuration."""
        return self.duck_types.get(duck_type)
    
    def get_variant(self, duck_type: str, variant: str) -> Optional[Dict[str, Any]]:
        """Get a specific variant configuration within a duck type."""
        duck_config = self.get_duck_type(duck_type)
        if duck_config and 'variants' in duck_config:
            return duck_config['variants'].get(variant)
        return None
    
    def get_internal_name(self, duck_type: str, variant: str) -> Optional[str]:
        """Get the internal name for a duck type and variant."""
        variant_config = self.get_variant(duck_type, variant)
        if variant_config:
            return variant_config.get('internal_name')
        return None
    
    def find_by_internal_name(self, internal_name: str) -> Optional[Dict[str, str]]:
        """Find the duck type and variant for a given internal name."""
        return self.internal_name_map.get(internal_name)
    
    def get_config_by_internal_name(self, internal_name: str) -> Optional[Dict[str, Any]]:
        """Get the full configuration for a duck by its internal name."""
        info = self.find_by_internal_name(internal_name)
        if not info:
            return None
            
        duck_type = info['duck_type']
        variant = info['variant']
        
        return {
            'duck_type': duck_type,
            'variant': variant,
            'duck': self.get_duck_type(duck_type),
            'variant_config': self.get_variant(duck_type, variant)
        }
    
    def list_duck_types(self) -> List[Dict[str, Any]]:
        """List all available duck types with basic information."""
        result = []
        for duck_id, config in self.duck_types.items():
            result.append({
                'id': duck_id,
                'name': config.get('name', duck_id),
                'description': config.get('description', ''),
                'variants': list(config.get('variants', {}).keys())
            })
        return result
    
    def list_all_variants(self) -> List[Dict[str, Any]]:
        """List all available variants across all duck types."""
        result = []
        for duck_id, config in self.duck_types.items():
            for variant_id, variant in config.get('variants', {}).items():
                result.append({
                    'duck_type': duck_id,
                    'duck_name': config.get('name', duck_id),
                    'variant': variant_id,
                    'variant_name': variant.get('name', variant_id),
                    'internal_name': variant.get('internal_name', '')
                })
        return result
    
    def save_config(self, duck_type: str, config: Dict[str, Any]) -> bool:
        """Save a duck configuration to file."""
        try:
            file_path = self.config_dir / f"{duck_type}.json"
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Reload the configuration
            self.duck_types[duck_type] = config
            
            # Update internal name mapping
            for variant_id, variant in config.get('variants', {}).items():
                internal_name = variant.get('internal_name')
                if internal_name:
                    self.internal_name_map[internal_name] = {
                        'duck_type': duck_type,
                        'variant': variant_id
                    }
                    
            return True
        except Exception as e:
            print(f"Error saving duck configuration: {e}")
            return False


# Create a singleton instance
duck_config = DuckConfig() 