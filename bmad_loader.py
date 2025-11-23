"""
BMAD Loader
This module provides functions to load BMAD agent definitions and story files from
the `.bmad` directory. BMAD (Breakthrough Method for Agile AI‑Driven Development)
defines each agent as a Markdown file containing a YAML block with its
configuration. Story files are also Markdown documents with structured fields.

The loader reads these files and constructs Python objects that can be used by
the rest of the Vessels system. It relies on the `pyyaml` package to parse
YAML blocks when available.
"""

import os
import re
from typing import Dict, List

from agent_zero_core import AgentSpecification

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - pyyaml may not be installed
    yaml = None


def _extract_yaml_block(markdown: str) -> str:
    """
    Extract the first YAML block enclosed in ```yaml fences from a Markdown
    string. Returns the YAML content as a string, or an empty string if no
    block is found.
    """
    # Use a regular expression to capture the first YAML fenced block.
    match = re.search(r"```yaml\s*(.*?)\s*```", markdown, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def load_agents(bmad_dir: str = ".bmad") -> List[AgentSpecification]:
    """
    Load all agent definitions from the `.bmad/agents` directory. Each agent
    definition must be stored in a Markdown file with a YAML block defining
    at least an `agent` section. The YAML block can optionally include a
    `commands` section. Returns a list of AgentSpecification instances.

    Parameters
    ----------
    bmad_dir: str
        Base directory where the `.bmad` folder resides. By default the
        current working directory is used.
    """
    agents: List[AgentSpecification] = []
    agents_path = os.path.join(bmad_dir, "agents")
    if not os.path.isdir(agents_path):
        return agents

    for filename in os.listdir(agents_path):
        if not filename.lower().endswith(".md"):
            continue
        filepath = os.path.join(agents_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read agent file {filepath}: {e}")
            continue
        except UnicodeDecodeError as e:
            logger.warning(f"File encoding error in {filepath}: {e}")
            continue
        yaml_content = _extract_yaml_block(content)
        if not yaml_content:
            continue
        if yaml:
            try:
                data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                logger.warning(f"YAML parsing error in {filepath}: {e}")
                data = None
        else:
            data = None
        if not data or "agent" not in data:
            continue
        agent_info = data.get("agent", {})
        name = agent_info.get("name") or agent_info.get("agent_name") or filename.rsplit(".", 1)[0]
        role = agent_info.get("role", "specialist")
        persona = agent_info.get("persona", "")
        # Use commands as capabilities if provided
        commands = data.get("commands", {})
        capabilities: List[str] = []
        if isinstance(commands, dict):
            for command_name, command_details in commands.items():
                capabilities.append(command_name)
                # Also incorporate keys of command details into capabilities
                # (e.g., description) to provide more context
                if isinstance(command_details, dict):
                    capabilities.extend(command_details.keys())
        # Remove duplicates
        capabilities = list({c for c in capabilities})
        # Create an AgentSpecification
        spec = AgentSpecification(
            name=name,
            description=f"{role} agent loaded from BMAD definition. Persona: {persona}",
            capabilities=capabilities or ["general"],
            tools_needed=[],
            communication_style="collaborative",
            autonomy_level="high",
            memory_type="shared",
            specialization=role.lower().replace(" ", "_")
        )
        agents.append(spec)
    return agents


def load_stories(bmad_dir: str = ".bmad") -> Dict[str, Dict[str, str]]:
    """
    Load story files from `.bmad/stories`. Each story is represented as a
    dictionary mapping section names (e.g., `metadata`, `context`,
    `requirements`, `tools`, `acceptance_criteria`, `test_cases`) to their
    corresponding content. Returns a dictionary keyed by story file name.

    Parameters
    ----------
    bmad_dir: str
        Base directory where the `.bmad` folder resides.
    """
    stories: Dict[str, Dict[str, str]] = {}
    stories_path = os.path.join(bmad_dir, "stories")
    if not os.path.isdir(stories_path):
        return stories
    for filename in os.listdir(stories_path):
        if not filename.lower().endswith(".md"):
            continue
        filepath = os.path.join(stories_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read story file {filepath}: {e}")
            continue
        except UnicodeDecodeError as e:
            logger.warning(f"File encoding error in {filepath}: {e}")
            continue
        # Split on headings (lines starting with `#` followed by a space)
        sections: Dict[str, str] = {}
        current_section = None
        for line in content.splitlines():
            if re.match(r"^#+ ", line):
                # New section detected
                current_section = line.lstrip("# ").strip().lower()
                sections[current_section] = ""
            elif current_section:
                sections[current_section] += line + "\n"
        # Trim whitespace
        for key in list(sections.keys()):
            sections[key] = sections[key].strip()
        stories[filename] = sections
    return stories
