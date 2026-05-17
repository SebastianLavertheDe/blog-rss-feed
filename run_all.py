#!/usr/bin/env python3
"""
Run all RSS feed generators in sequence.
Configuration is loaded from config.yaml or config.json.
"""

import asyncio
import subprocess
import sys
import os
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urljoin

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class RSSRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scripts = config.get("scripts", [])
        self.options = config.get("options", {})
        self.output_dir = self.options.get("output_dir", "rss")
        self.script_dir = self.options.get("script_dir", "script")
        self.opml_config = self.options.get("opml", {})
        self.base_url = self.options.get("base_url", "")

    def get_script_path(self, script_file: str) -> str:
        """Get full path to script file"""
        return os.path.join(self.script_dir, script_file)

    async def run_script(self, script_config: Dict[str, Any]) -> bool:
        """Run a single RSS generator script"""
        script_name = script_config["name"]
        script_file = script_config["file"]
        enabled = script_config.get("enabled", True)

        if not enabled:
            print(f"⊘ Skipping {script_name} (disabled)")
            return True

        print(f"\n{'=' * 60}")
        print(f"Running: {script_name}")
        print(f"{'=' * 60}")

        script_path = self.get_script_path(script_file)
        if not os.path.exists(script_path):
            print(f"✗ Error: Script file '{script_path}' not found")
            return False

        try:
            # Build command with optional arguments
            cmd = [sys.executable, script_path]

            # Auto-add --rss-url from rssUrl field if present
            rss_url = script_config.get("rssUrl")
            if rss_url:
                cmd.extend(["--rss-url", rss_url])

            # Auto-add --output if not present in args and output is defined in config
            output_file = script_config.get("output")
            if output_file and "--output" not in str(script_config.get("args", [])):
                cmd.extend(["--output", output_file])

            # Add script arguments if provided
            script_args = script_config.get("args", [])
            if script_args:
                if isinstance(script_args, list):
                    cmd.extend(script_args)
                elif isinstance(script_args, str):
                    # Parse string arguments (simple split by space)
                    cmd.extend(script_args.split())

            # Run the script using asyncio subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            # Print output
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode(), file=sys.stderr)

            if process.returncode == 0:
                print(f"✓ {script_name} completed successfully")
                return True
            else:
                print(f"✗ {script_name} failed with return code {process.returncode}")
                return False

        except Exception as e:
            print(f"✗ Error running {script_name}: {e}")
            return False

    async def run_all(self) -> Dict[str, bool]:
        """Run all enabled scripts in sequence"""
        # Create output directory if needed
        if self.options.get("create_output_dir", True):
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"Output directory: {self.output_dir}/")

        results = {}

        # Stop on first error if configured
        stop_on_error = self.options.get("stop_on_error", False)

        for script_config in self.scripts:
            script_name = script_config["name"]
            success = await self.run_script(script_config)
            results[script_name] = success

            if not success and stop_on_error:
                print(f"\n✗ Stopping due to error (stop_on_error=True)")
                break

        return results

    def generate_opml(self, results: Dict[str, bool]) -> bool:
        """Generate OPML file(s) aggregating RSS feeds"""
        if not self.opml_config.get("enabled", False):
            return True

        # Check if using new multi-OPML format
        opml_outputs = self.opml_config.get("outputs", [])

        if opml_outputs:
            # New format: generate multiple OPML files by category
            return self.generate_multiple_opml(results, opml_outputs)
        else:
            # Legacy format: single OPML file
            return self.generate_single_opml(results)

    def generate_single_opml(self, results: Dict[str, bool]) -> bool:
        """Generate single OPML file (legacy format)"""
        print(f"\n{'=' * 60}")
        print("Generating OPML file...")
        print(f"{'=' * 60}")

        try:
            # Create root element
            opml = ET.Element("opml")
            opml.set("version", "2.0")

            # Create head element
            head = ET.SubElement(opml, "head")
            title = self.opml_config.get("title", "All Articles RSS Subscriptions")
            title_elem = ET.SubElement(head, "title")
            title_elem.text = title

            # Create body element
            body = ET.SubElement(opml, "body")

            # Get base URL for XML URLs
            base_url = self.opml_config.get("base_url", "")

            feeds_added = 0

            # First, add dynamically generated feeds
            for script_config in self.scripts:
                script_name = script_config["name"]
                enabled = script_config.get("enabled", True)

                # Skip disabled scripts or failed scripts
                if not enabled or not results.get(script_name, False):
                    continue

                output_file = script_config.get("output")
                if not output_file:
                    continue

                # Build the full URL or relative path
                if base_url:
                    xml_url = urljoin(base_url.rstrip("/") + "/", output_file)
                    # Convert GitHub blob URL to raw URL if needed
                    if "github.com" in xml_url and "/blob/" in xml_url:
                        xml_url = xml_url.replace(
                            "github.com", "raw.githubusercontent.com"
                        ).replace("/blob/", "/")
                else:
                    xml_url = output_file

                # Get display name
                display_name = script_config.get("title", script_name)

                # Create outline element
                outline = ET.SubElement(body, "outline")
                outline.set("text", display_name)
                outline.set("title", display_name)
                outline.set("type", "rss")
                outline.set("xmlUrl", xml_url)

                feeds_added += 1
                print(f"  + {display_name}: {xml_url}")

            # Then, add static feeds (always included regardless of script results)
            static_feeds = self.opml_config.get("static_feeds", [])
            for feed in static_feeds:
                if not feed.get("enabled", True):
                    continue

                display_name = feed.get("title", feed.get("name", "Unknown"))
                xml_url = feed.get("url", "")

                if not xml_url:
                    continue

                # Create outline element
                outline = ET.SubElement(body, "outline")
                outline.set("text", display_name)
                outline.set("title", display_name)
                outline.set("type", "rss")
                outline.set("xmlUrl", xml_url)

                feeds_added += 1
                print(f"  * {display_name}: {xml_url} (static)")

            # Create output directory if needed
            output_file = self.opml_config.get("output_file", "rss/blog_rss.xml")
            output_path = os.path.dirname(output_file)
            if output_path:
                os.makedirs(output_path, exist_ok=True)

            # Write OPML file
            tree = ET.ElementTree(opml)
            ET.indent(tree, space="    ")

            # Add XML declaration manually
            with open(output_file, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                tree.write(f, encoding="unicode", xml_declaration=False)

            print(f"\n✓ OPML file generated: {output_file}")
            print(f"  Total feeds: {feeds_added}")
            return True

        except Exception as e:
            print(f"✗ Error generating OPML: {e}")
            return False

    def generate_multiple_opml(
        self, results: Dict[str, bool], opml_outputs: list
    ) -> bool:
        """Generate multiple OPML files by category"""
        base_url = self.opml_config.get("base_url", "")

        for opml_output in opml_outputs:
            output_file = opml_output.get("name", "opml.xml")
            title = opml_output.get("title", "RSS Subscriptions")
            categories = opml_output.get("categories", [])
            static_feeds = opml_output.get("static_feeds", [])

            print(f"\n{'=' * 60}")
            print(f"Generating OPML: {output_file}")
            print(f"  Categories: {', '.join(categories)}")
            print(f"{'=' * 60}")

            try:
                # Create root element
                opml = ET.Element("opml")
                opml.set("version", "2.0")

                # Create head element
                head = ET.SubElement(opml, "head")
                title_elem = ET.SubElement(head, "title")
                title_elem.text = title

                # Create body element
                body = ET.SubElement(opml, "body")

                feeds_added = 0

                # Add dynamically generated feeds that match category
                for script_config in self.scripts:
                    script_name = script_config["name"]
                    enabled = script_config.get("enabled", True)
                    category = script_config.get("category", "blog")

                    # Skip disabled scripts, failed scripts, or wrong category
                    if not enabled or not results.get(script_name, False):
                        continue
                    if category not in categories:
                        continue

                    output_feed_file = script_config.get("output")
                    if not output_feed_file:
                        continue

                    # Build the full URL or relative path
                    if base_url:
                        xml_url = urljoin(base_url.rstrip("/") + "/", output_feed_file)
                        if "github.com" in xml_url and "/blob/" in xml_url:
                            xml_url = xml_url.replace(
                                "github.com", "raw.githubusercontent.com"
                            ).replace("/blob/", "/")
                    else:
                        xml_url = output_feed_file

                    # Get display name
                    display_name = script_config.get("title", script_name)

                    # Create outline element
                    outline = ET.SubElement(body, "outline")
                    outline.set("text", display_name)
                    outline.set("title", display_name)
                    outline.set("type", "rss")
                    outline.set("xmlUrl", xml_url)

                    feeds_added += 1
                    print(f"  + {display_name}: {xml_url}")

                # Add static feeds
                for feed in static_feeds:
                    if not feed.get("enabled", True):
                        continue

                    display_name = feed.get("title", feed.get("name", "Unknown"))
                    xml_url = feed.get("url", "")

                    if not xml_url:
                        continue

                    # Create outline element
                    outline = ET.SubElement(body, "outline")
                    outline.set("text", display_name)
                    outline.set("title", display_name)
                    outline.set("type", "rss")
                    outline.set("xmlUrl", xml_url)

                    feeds_added += 1
                    print(f"  * {display_name}: {xml_url} (static)")

                # Create output directory if needed
                output_path = os.path.dirname(output_file)
                if output_path:
                    os.makedirs(output_path, exist_ok=True)

                # Write OPML file
                tree = ET.ElementTree(opml)
                ET.indent(tree, space="    ")

                # Add XML declaration manually
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                    tree.write(f, encoding="unicode", xml_declaration=False)

                print(f"\n✓ OPML file generated: {output_file}")
                print(f"  Total feeds: {feeds_added}")

            except Exception as e:
                print(f"✗ Error generating OPML {output_file}: {e}")
                return False

        return True

    def print_summary(self, results: Dict[str, bool]) -> tuple[int, Dict[str, bool]]:
        """Print execution summary and return exit code with results"""
        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")

        total = len(results)
        successful = sum(1 for v in results.values() if v)
        failed = total - successful
        failed_sources = [name for name, success in results.items() if not success]

        for script_name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status}: {script_name}")

        print(f"\nTotal: {total}, Successful: {successful}, Failed: {failed}")

        if failed == 0:
            print("\n✓ All RSS feeds generated successfully!")
            return 0, results
        else:
            print(f"\n✗ {failed} feed(s) failed to generate")
            print(f"✗ Failed sources: {', '.join(failed_sources)}")
            return 0, results


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file"""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise ImportError(
                    "PyYAML is required to parse YAML config files. Install with: pip install pyyaml"
                )
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "options": {
            "output_dir": "rss",
            "script_dir": "script",
            "create_output_dir": True,
            "stop_on_error": False,
            "base_url": "",
            "opml": {
                "enabled": True,
                "output_file": "rss/blog_rss.xml",
                "title": "All Articles RSS Subscriptions for bestblogs.dev",
                "base_url": "",
            },
        },
        "scripts": [
            {
                "name": "Anthropic Engineering",
                "file": "anthropic_rss.py",
                "output": "anthropic_engineering_rss.xml",
                "title": "Anthropic Engineering",
                "enabled": True,
            },
            {
                "name": "Cursor Blog",
                "file": "cursor_rss.py",
                "output": "cursor_blog_rss.xml",
                "title": "Cursor Blog",
                "enabled": True,
            },
            {
                "name": "Claude Blog",
                "file": "claude_blog_rss.py",
                "output": "claude_blog_rss.xml",
                "title": "Claude Blog",
                "enabled": True,
            },
        ],
    }


async def main():
    parser = argparse.ArgumentParser(
        description="Run all RSS feed generators in sequence"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to config file (YAML or JSON, default: config.yaml)",
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample config file and exit",
    )
    parser.add_argument(
        "--stop-on-error", action="store_true", help="Stop execution on first error"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )
    parser.add_argument("--no-opml", action="store_true", help="Skip OPML generation")

    args = parser.parse_args()

    # Handle --create-config
    if args.create_config:
        config = get_default_config()
        config_path = "config.yaml"

        # Save as YAML if available, otherwise JSON
        if HAS_YAML:
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"✓ Created sample config: {config_path}")
        else:
            config_path = "config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            print(f"✓ Created sample config: {config_path}")
        return

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"⚠ Config file not found: {args.config}")
        print(f"Creating default config...")
        config = get_default_config()

        # Try to save the default config
        try:
            if HAS_YAML and not args.config.endswith(".json"):
                with open(args.config, "w") as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                config_path = (
                    args.config if args.config.endswith(".json") else "config.json"
                )
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)
                config = load_config(config_path)
            print(
                f"✓ Created default config: {args.config if HAS_YAML else config_path}"
            )
        except Exception as e:
            print(f"⚠ Could not create config file: {e}")
            print("Using built-in default configuration")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return 1

    # Override config with command line options
    if args.stop_on_error:
        config["options"]["stop_on_error"] = True
    if args.no_opml:
        config["options"]["opml"]["enabled"] = False

    # Dry run
    if args.dry_run:
        print("Dry run - would execute the following scripts:")
        for script in config.get("scripts", []):
            enabled = script.get("enabled", True)
            status = "✓" if enabled else "⊘"
            print(f"  {status} {script['name']} ({script['file']})")
        return 0

    # Run all scripts
    runner = RSSRunner(config)
    results = await runner.run_all()

    # Generate OPML
    runner.generate_opml(results)

    exit_code, results = runner.print_summary(results)

    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
