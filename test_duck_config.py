#!/usr/bin/env python3
"""
Duck Configuration Test Runner

This script runs the duck configuration test from the command line.
"""

from app.config.duck_config import duck_config
import json


def print_separator(title):
    """Print a section separator with a title."""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def test_duck_config():
    """Test and demonstrate the duck configuration system."""
    # Get all duck types
    print_separator("All Duck Types")
    duck_types = duck_config.list_duck_types()
    print(json.dumps(duck_types, indent=2))

    # Get a specific duck type
    print_separator("Specific Duck Type (open_duck_mini)")
    duck_type = duck_config.get_duck_type('open_duck_mini')
    if duck_type:
        print(json.dumps({k: v for k, v in duck_type.items() if k != 'variants'}, indent=2))
        print(f"Variants: {list(duck_type.get('variants', {}).keys())}")
    else:
        print("Duck type 'open_duck_mini' not found")

    # Get a specific variant
    print_separator("Specific Variant (open_duck_mini, v2)")
    variant = duck_config.get_variant('open_duck_mini', 'v2')
    if variant:
        print(json.dumps(variant, indent=2))
    else:
        print("Variant 'v2' for duck type 'open_duck_mini' not found")

    # Get internal name
    print_separator("Internal Name Lookup")
    internal_name = duck_config.get_internal_name('open_duck_mini', 'v2')
    print(f"Internal name for open_duck_mini/v2: {internal_name}")

    # Find by internal name
    print_separator("Find by Internal Name")
    duck_info = duck_config.find_by_internal_name('open_duck_mini_v2')
    print(f"Duck info for internal name 'open_duck_mini_v2': {duck_info}")

    # Full config by internal name
    print_separator("Full Config by Internal Name")
    full_config = duck_config.get_config_by_internal_name('open_duck_mini_v2')
    if full_config:
        print(f"Duck type: {full_config['duck_type']}")
        print(f"Variant: {full_config['variant']}")
        print(f"Duck name: {full_config['duck'].get('name')}")
        print(f"Variant name: {full_config['variant_config'].get('name')}")
    else:
        print("No configuration found for internal name 'open_duck_mini_v2'")

    # List all variants
    print_separator("All Variants")
    all_variants = duck_config.list_all_variants()
    print(json.dumps(all_variants, indent=2))


if __name__ == "__main__":
    test_duck_config() 