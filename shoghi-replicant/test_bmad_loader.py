#!/usr/bin/env python3
"""
Test suite for bmad_loader.py
Tests the BMAD agent and story loading functionality
"""

import pytest
import os
import tempfile
import shutil
from bmad_loader import (
    _extract_yaml_block,
    load_agents,
    load_stories
)


class TestExtractYamlBlock:
    """Tests for _extract_yaml_block function"""

    def test_extract_simple_yaml(self):
        """Test extraction of simple YAML block"""
        markdown = """
# Agent Definition

```yaml
agent:
  name: TestAgent
  role: tester
```

Some other content
"""
        result = _extract_yaml_block(markdown)
        assert "agent:" in result
        assert "name: TestAgent" in result
        assert "role: tester" in result

    def test_extract_no_yaml(self):
        """Test when no YAML block exists"""
        markdown = "# Just a heading\n\nSome content"
        result = _extract_yaml_block(markdown)
        assert result == ""

    def test_extract_first_yaml_only(self):
        """Test that only first YAML block is extracted"""
        markdown = """
```yaml
first: block
```

```yaml
second: block
```
"""
        result = _extract_yaml_block(markdown)
        assert "first: block" in result
        assert "second: block" not in result

    def test_extract_with_whitespace(self):
        """Test YAML extraction with surrounding whitespace"""
        markdown = """
```yaml

  agent:
    name: Spaced

```
"""
        result = _extract_yaml_block(markdown)
        assert "agent:" in result
        assert result.strip() == result  # Should be trimmed


class TestLoadAgents:
    """Tests for load_agents function"""

    def setup_method(self):
        """Create temporary test directory"""
        self.test_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.test_dir, "agents")
        os.makedirs(self.agents_dir)

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_load_valid_agent(self):
        """Test loading a valid agent definition"""
        agent_md = """
# Product Owner Agent

```yaml
agent:
  name: ProductOwner
  role: product_manager
  persona: Strategic product leader

commands:
  analyze:
    description: Analyze product requirements
  prioritize:
    description: Prioritize features
```
"""
        agent_file = os.path.join(self.agents_dir, "product_owner.md")
        with open(agent_file, "w") as f:
            f.write(agent_md)

        agents = load_agents(self.test_dir)

        assert len(agents) == 1
        agent = agents[0]
        assert agent.name == "ProductOwner"
        assert "analyze" in agent.capabilities
        assert "prioritize" in agent.capabilities
        assert agent.specialization == "product_manager"

    def test_load_agent_with_agent_name(self):
        """Test loading agent that uses agent_name instead of name"""
        agent_md = """
```yaml
agent:
  agent_name: Tester
  role: qa_engineer
```
"""
        agent_file = os.path.join(self.agents_dir, "tester.md")
        with open(agent_file, "w") as f:
            f.write(agent_md)

        agents = load_agents(self.test_dir)

        assert len(agents) == 1
        assert agents[0].name == "Tester"

    def test_load_agent_without_name_uses_filename(self):
        """Test that filename is used when no name in YAML"""
        agent_md = """
```yaml
agent:
  role: deployer
  persona: Deployment specialist
```
"""
        agent_file = os.path.join(self.agents_dir, "deployer.md")
        with open(agent_file, "w") as f:
            f.write(agent_md)

        agents = load_agents(self.test_dir)

        assert len(agents) == 1
        assert agents[0].name == "deployer"

    def test_load_multiple_agents(self):
        """Test loading multiple agent files"""
        for i in range(3):
            agent_md = f"""
```yaml
agent:
  name: Agent{i}
  role: role{i}
```
"""
            agent_file = os.path.join(self.agents_dir, f"agent{i}.md")
            with open(agent_file, "w") as f:
                f.write(agent_md)

        agents = load_agents(self.test_dir)

        assert len(agents) == 3
        agent_names = [a.name for a in agents]
        assert "Agent0" in agent_names
        assert "Agent1" in agent_names
        assert "Agent2" in agent_names

    def test_load_agents_skips_non_md_files(self):
        """Test that non-.md files are skipped"""
        # Create .md file
        with open(os.path.join(self.agents_dir, "valid.md"), "w") as f:
            f.write("```yaml\nagent:\n  name: Valid\n  role: tester\n```")

        # Create non-.md files
        with open(os.path.join(self.agents_dir, "invalid.txt"), "w") as f:
            f.write("```yaml\nagent:\n  name: Invalid\n```")

        agents = load_agents(self.test_dir)

        assert len(agents) == 1
        assert agents[0].name == "Valid"

    def test_load_agents_empty_directory(self):
        """Test loading from empty agents directory"""
        agents = load_agents(self.test_dir)
        assert agents == []

    def test_load_agents_no_directory(self):
        """Test loading when agents directory doesn't exist"""
        empty_dir = tempfile.mkdtemp()
        try:
            agents = load_agents(empty_dir)
            assert agents == []
        finally:
            shutil.rmtree(empty_dir)

    def test_load_agent_with_invalid_yaml(self):
        """Test that invalid YAML is gracefully skipped"""
        agent_md = """
```yaml
agent:
  name: BadAgent
  role: [unclosed bracket
```
"""
        agent_file = os.path.join(self.agents_dir, "bad.md")
        with open(agent_file, "w") as f:
            f.write(agent_md)

        agents = load_agents(self.test_dir)
        # Should not raise exception, just skip the file
        assert agents == []

    def test_load_agent_missing_agent_section(self):
        """Test that agents without 'agent' section are skipped"""
        agent_md = """
```yaml
commands:
  test:
    description: Test command
```
"""
        agent_file = os.path.join(self.agents_dir, "no_agent.md")
        with open(agent_file, "w") as f:
            f.write(agent_md)

        agents = load_agents(self.test_dir)
        assert agents == []


class TestLoadStories:
    """Tests for load_stories function"""

    def setup_method(self):
        """Create temporary test directory"""
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        os.makedirs(self.stories_dir)

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_load_valid_story(self):
        """Test loading a valid story file"""
        story_md = """
# Metadata
ID: STORY-001
Title: User Authentication

# Context
Users need to log in securely

# Requirements
- Password authentication
- OAuth support

# Tools
- Authentication library
- Database

# Acceptance Criteria
- Users can log in
- Sessions are secure

# Test Cases
- Test login with valid credentials
- Test login with invalid credentials
"""
        story_file = os.path.join(self.stories_dir, "auth_story.md")
        with open(story_file, "w") as f:
            f.write(story_md)

        stories = load_stories(self.test_dir)

        assert "auth_story.md" in stories
        story = stories["auth_story.md"]

        assert "metadata" in story
        assert "ID: STORY-001" in story["metadata"]
        assert "context" in story
        assert "Users need to log in" in story["context"]
        assert "requirements" in story
        assert "tools" in story
        assert "acceptance criteria" in story
        assert "test cases" in story

    def test_load_multiple_stories(self):
        """Test loading multiple story files"""
        for i in range(2):
            story_md = f"# Story {i}\nContent for story {i}"
            story_file = os.path.join(self.stories_dir, f"story{i}.md")
            with open(story_file, "w") as f:
                f.write(story_md)

        stories = load_stories(self.test_dir)

        assert len(stories) == 2
        assert "story0.md" in stories
        assert "story1.md" in stories

    def test_load_stories_skips_non_md(self):
        """Test that non-.md files are skipped"""
        with open(os.path.join(self.stories_dir, "valid.md"), "w") as f:
            f.write("# Valid\nContent")

        with open(os.path.join(self.stories_dir, "invalid.txt"), "w") as f:
            f.write("# Invalid\nContent")

        stories = load_stories(self.test_dir)

        assert len(stories) == 1
        assert "valid.md" in stories
        assert "invalid.txt" not in stories

    def test_load_stories_empty_directory(self):
        """Test loading from empty stories directory"""
        stories = load_stories(self.test_dir)
        assert stories == {}

    def test_load_stories_no_directory(self):
        """Test loading when stories directory doesn't exist"""
        empty_dir = tempfile.mkdtemp()
        try:
            stories = load_stories(empty_dir)
            assert stories == {}
        finally:
            shutil.rmtree(empty_dir)

    def test_story_section_parsing(self):
        """Test that sections are correctly parsed"""
        story_md = """
# Section One
Content of section one
Multi-line content

# Section Two
Content of section two

## Subsection
Subsection content should still be in Section Two area
"""
        story_file = os.path.join(self.stories_dir, "test.md")
        with open(story_file, "w") as f:
            f.write(story_md)

        stories = load_stories(self.test_dir)
        story = stories["test.md"]

        # Sections should be lowercase
        assert "section one" in story
        assert "section two" in story

        # Content should be captured
        assert "Content of section one" in story["section one"]
        assert "Content of section two" in story["section two"]

        # Note: Subsections (##) create their own section entries in the current implementation
        # This is expected behavior based on the bmad_loader.py implementation
        assert "subsection" in story or "## Subsection" in story["section two"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
