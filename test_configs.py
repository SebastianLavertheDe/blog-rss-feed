#!/usr/bin/env python3
"""
Test script to validate each RSS configuration in config.yaml
Runs external_rss_importer.py for each enabled source using external_rss_importer.py
Shows execution time for each configuration
"""

import yaml
import subprocess
import sys
import time
from pathlib import Path

def load_config():
    """Load config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def build_command(script_config):
    """Build command line for external_rss_importer.py"""
    cmd = [
        'python3', 'script/external_rss_importer.py',
        '--rss-url', script_config['rssUrl'],
        '--output', script_config['output'],
        '--title', script_config['title']
    ]

    # Add args if present
    if 'args' in script_config:
        args = script_config['args']
        if '--use-atom' in args:
            cmd.append('--use-atom')
        if '--use-feedparser' in args:
            cmd.append('--use-feedparser')
        if '--max-retries' in args:
            idx = args.index('--max-retries')
            if idx + 1 < len(args):
                cmd.extend(['--max-retries', args[idx + 1]])

    return cmd

def test_config(script_config, slow_threshold=10):
    """Test a single configuration and return result with timing"""
    name = script_config.get('name', 'Unknown')
    print(f"\nTesting: {name}")

    cmd = build_command(script_config)

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per config
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            # Extract item count from output
            lines = result.stdout.strip().split('\n')
            items = "N/A"
            for line in lines:
                if 'Processed' in line:
                    items = line.split('Processed')[1].strip().split()[0]
                    break

            status = "✓"
            if elapsed > slow_threshold:
                status = f"⚠ SLOW ({elapsed:.1f}s)"
                print(f"  {status} - {items} items")
            else:
                print(f"  ✓ SUCCESS ({elapsed:.1f}s) - {items} items")

            return {
                'name': name,
                'success': True,
                'time': elapsed,
                'items': items,
                'slow': elapsed > slow_threshold
            }
        else:
            print(f"  ✗ FAILED ({elapsed:.1f}s)")
            print(f"    Error: {result.stderr[:100]}")
            return {
                'name': name,
                'success': False,
                'time': elapsed,
                'items': 0,
                'slow': False
            }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"  ✗ TIMEOUT ({elapsed:.1f}s)")
        return {
            'name': name,
            'success': False,
            'time': elapsed,
            'items': 0,
            'slow': True
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ✗ ERROR ({elapsed:.1f}s): {e}")
        return {
            'name': name,
            'success': False,
            'time': elapsed,
            'items': 0,
            'slow': False
        }

def main():
    """Main test runner"""
    config = load_config()

    # Get all scripts using external_rss_importer.py
    external_configs = [
        s for s in config.get('scripts', [])
        if s.get('file') == 'external_rss_importer.py' and s.get('enabled', True)
    ]

    if not external_configs:
        print("No configurations found using external_rss_importer.py")
        return 1

    print(f"Found {len(external_configs)} configurations to test")
    print("="*60)

    results = []
    slow_configs = []
    failed_configs = []

    for i, script_config in enumerate(external_configs, 1):
        print(f"[{i}/{len(external_configs)}]", end=" ")
        result = test_config(script_config, slow_threshold=10)
        results.append(result)

        if result['slow']:
            slow_configs.append(result)
        if not result['success']:
            failed_configs.append(result)

    # Sort by time (slowest first)
    results_by_time = sorted(results, key=lambda x: x['time'], reverse=True)

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total: {len(results)}")
    success_count = sum(1 for r in results if r['success'])
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed: {len(failed_configs)}")
    print(f"⚠ Slow (>10s): {len(slow_configs)}")

    # Print top 10 slowest configs
    print(f"\n{'='*60}")
    print("TOP 10 SLOWEST CONFIGURATIONS")
    print(f"{'='*60}")
    for i, r in enumerate(results_by_time[:10], 1):
        status = "✗" if not r['success'] else ("⚠" if r['slow'] else "✓")
        print(f"{i}. {status} {r['name']}: {r['time']:.1f}s ({r['items']} items)")

    # Print failed configs
    if failed_configs:
        print(f"\n{'='*60}")
        print("FAILED CONFIGURATIONS")
        print(f"{'='*60}")
        for r in failed_configs:
            print(f"  ✗ {r['name']}: {r['time']:.1f}s")

    # Print slow configs
    if slow_configs:
        print(f"\n{'='*60}")
        print("SLOW CONFIGURATIONS (>10s)")
        print(f"{'='*60}")
        for r in sorted(slow_configs, key=lambda x: x['time'], reverse=True):
            print(f"  ⚠ {r['name']}: {r['time']:.1f}s")

    return 0 if not failed_configs else 1

if __name__ == '__main__':
    sys.exit(main())
