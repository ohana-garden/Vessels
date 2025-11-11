#!/usr/bin/env python3
"""
ADAPTIVE TOOLS SYSTEM
Tools that create other tools
Agents identify needed capabilities and build them
Includes: web scraping, document generation, API integration, data processing
"""

import json
import logging
import sqlite3
import threading
import time
import importlib
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import uuid
import inspect
import ast

logger = logging.getLogger(__name__)

class ToolType(Enum):
    WEB_SCRAPING = "web_scraping"
    DOCUMENT_GENERATION = "document_generation"
    API_INTEGRATION = "api_integration"
    DATA_PROCESSING = "data_processing"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    MONITORING = "monitoring"

@dataclass
class ToolSpecification:
    """Specification for a tool"""
    name: str
    description: str
    tool_type: ToolType
    capabilities: List[str]
    dependencies: List[str]
    parameters: Dict[str, Any]
    return_type: str
    examples: List[str] = field(default_factory=list)
    
@dataclass
class ToolInstance:
    """Instance of a tool"""
    id: str
    specification: ToolSpecification
    implementation: str
    created_by: str
    created_at: datetime
    usage_count: int = 0
    success_rate: float = 1.0
    last_used: Optional[datetime] = None
    
class AdaptiveTools:
    """Self-expanding tool system that creates tools based on needs"""
    
    def __init__(self):
        self.tools: Dict[str, ToolInstance] = {}
        self.tool_specs: Dict[str, ToolSpecification] = {}
        self.capability_matrix: Dict[str, List[str]] = {}
        self.tool_history: List[Dict[str, Any]] = []
        self.tools_db = None
        self.running = False
        self.optimization_thread = None
        
        self.initialize_tool_system()
    
    def initialize_tool_system(self):
        """Initialize the adaptive tool system"""
        self.running = True
        
        # Initialize database
        self.tools_db = sqlite3.connect(':memory:', check_same_thread=False)
        self._create_tool_tables()
        
        # Load base tools
        self._load_base_tools()
        
        # Start optimization thread
        self.optimization_thread = threading.Thread(target=self._optimization_loop)
        self.optimization_thread.daemon = True
        self.optimization_thread.start()
        
        logger.info("Adaptive Tools System initialized")
    
    def _create_tool_tables(self):
        """Create database tables for tools"""
        cursor = self.tools_db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                tool_type TEXT,
                capabilities TEXT,
                dependencies TEXT,
                parameters TEXT,
                return_type TEXT,
                implementation TEXT,
                created_by TEXT,
                created_at TEXT,
                usage_count INTEGER,
                success_rate REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_usage (
                id TEXT PRIMARY KEY,
                tool_id TEXT,
                agent_id TEXT,
                timestamp TEXT,
                parameters TEXT,
                result TEXT,
                success BOOLEAN
            )
        ''')
        
        self.tools_db.commit()
    
    def _load_base_tools(self):
        """Load base set of tools"""
        base_tools = [
            ToolSpecification(
                name="web_scraper",
                description="Scrapes web content from URLs",
                tool_type=ToolType.WEB_SCRAPING,
                capabilities=["extract_text", "extract_links", "extract_images", "parse_html"],
                dependencies=["requests", "beautifulsoup4"],
                parameters={"url": "string", "selectors": "dict", "timeout": "int"},
                return_type="dict",
                examples=["Scrape grant information from foundation websites"]
            ),
            ToolSpecification(
                name="document_generator",
                description="Generates documents from templates",
                tool_type=ToolType.DOCUMENT_GENERATION,
                capabilities=["template_processing", "text_generation", "format_conversion"],
                dependencies=["jinja2"],
                parameters={"template": "string", "data": "dict", "format": "string"},
                return_type="string",
                examples=["Generate grant applications from templates"]
            ),
            ToolSpecification(
                name="api_connector",
                description="Connects to REST APIs",
                tool_type=ToolType.API_INTEGRATION,
                capabilities=["http_requests", "authentication", "data_parsing", "error_handling"],
                dependencies=["requests"],
                parameters={"url": "string", "method": "string", "headers": "dict", "data": "dict"},
                return_type="dict",
                examples=["Connect to government grant databases"]
            ),
            ToolSpecification(
                name="data_processor",
                description="Processes and transforms data",
                tool_type=ToolType.DATA_PROCESSING,
                capabilities=["data_cleaning", "data_transformation", "statistical_analysis"],
                dependencies=["pandas", "numpy"],
                parameters={"data": "any", "operations": "list", "config": "dict"},
                return_type="any",
                examples=["Process grant application data"]
            ),
            ToolSpecification(
                name="email_sender",
                description="Sends emails with attachments",
                tool_type=ToolType.COMMUNICATION,
                capabilities=["email_composition", "attachment_handling", "bulk_sending"],
                dependencies=["smtplib", "email"],
                parameters={"recipients": "list", "subject": "string", "body": "string", "attachments": "list"},
                return_type="bool",
                examples=["Send grant applications to funders"]
            ),
            ToolSpecification(
                name="calendar_manager",
                description="Manages calendar events and deadlines",
                tool_type=ToolType.AUTOMATION,
                capabilities=["event_creation", "deadline_tracking", "reminder_system"],
                dependencies=["datetime"],
                parameters={"events": "list", "reminders": "dict", "timezone": "string"},
                return_type="list",
                examples=["Track grant application deadlines"]
            ),
            ToolSpecification(
                name="report_generator",
                description="Generates reports and analytics",
                tool_type=ToolType.ANALYTICS,
                capabilities=["data_visualization", "report_formatting", "chart_generation"],
                dependencies=["matplotlib", "seaborn"],
                parameters={"data": "any", "report_type": "string", "format": "string"},
                return_type="string",
                examples=["Generate grant performance reports"]
            ),
            ToolSpecification(
                name="monitoring_system",
                description="Monitors systems and processes",
                tool_type=ToolType.MONITORING,
                capabilities=["health_checks", "performance_monitoring", "alert_system"],
                dependencies=["time"],
                parameters={"targets": "list", "metrics": "list", "thresholds": "dict"},
                return_type="dict",
                examples=["Monitor grant application status"]
            )
        ]
        
        for spec in base_tools:
            self.create_tool(spec, "system")
    
    def identify_needed_capabilities(self, agent_requirements: List[str]) -> List[str]:
        """Identify capabilities needed based on agent requirements"""
        needed_capabilities = []
        
        # Map requirements to capabilities
        capability_mapping = {
            "web_search": ["web_scraping", "data_extraction", "content_parsing"],
            "grant_discovery": ["web_scraping", "database_query", "api_integration", "data_analysis"],
            "document_generation": ["template_processing", "text_generation", "format_conversion"],
            "communication": ["email_sending", "notification_system", "messaging"],
            "scheduling": ["calendar_management", "deadline_tracking", "reminder_system"],
            "data_analysis": ["statistical_analysis", "data_processing", "visualization"],
            "monitoring": ["system_monitoring", "performance_tracking", "alert_system"],
            "automation": ["workflow_automation", "task_scheduling", "process_optimization"]
        }
        
        for requirement in agent_requirements:
            if requirement in capability_mapping:
                needed_capabilities.extend(capability_mapping[requirement])
            else:
                # Analyze requirement and suggest capabilities
                needed_capabilities.extend(self._analyze_requirement(requirement))
        
        return list(set(needed_capabilities))  # Remove duplicates
    
    def _analyze_requirement(self, requirement: str) -> List[str]:
        """Analyze requirement and suggest needed capabilities"""
        requirement_lower = requirement.lower()
        
        if "web" in requirement_lower or "scrap" in requirement_lower:
            return ["web_scraping", "data_extraction"]
        elif "document" in requirement_lower or "generat" in requirement_lower:
            return ["document_generation", "template_processing"]
        elif "api" in requirement_lower or "connect" in requirement_lower:
            return ["api_integration", "data_transformation"]
        elif "data" in requirement_lower or "analyz" in requirement_lower:
            return ["data_processing", "statistical_analysis"]
        elif "communicat" in requirement_lower or "email" in requirement_lower:
            return ["communication", "notification_system"]
        elif "schedul" in requirement_lower or "deadline" in requirement_lower:
            return ["calendar_management", "task_scheduling"]
        elif "monitor" in requirement_lower or "track" in requirement_lower:
            return ["system_monitoring", "performance_tracking"]
        else:
            return ["general_processing"]  # Default capability
    
    def create_tool(self, specification: ToolSpecification, creator_id: str) -> str:
        """Create a new tool based on specification"""
        tool_id = str(uuid.uuid4())
        
        # Generate implementation code
        implementation = self._generate_tool_implementation(specification)
        
        # Create tool instance
        tool_instance = ToolInstance(
            id=tool_id,
            specification=specification,
            implementation=implementation,
            created_by=creator_id,
            created_at=datetime.now()
        )
        
        # Store tool
        self.tools[tool_id] = tool_instance
        self.tool_specs[specification.name] = specification
        
        # Update capability matrix
        for capability in specification.capabilities:
            if capability not in self.capability_matrix:
                self.capability_matrix[capability] = []
            self.capability_matrix[capability].append(tool_id)
        
        # Persist tool
        self._persist_tool(tool_instance)
        
        # Log creation
        self.tool_history.append({
            "action": "tool_created",
            "tool_id": tool_id,
            "tool_name": specification.name,
            "creator": creator_id,
            "timestamp": datetime.now(),
            "capabilities": specification.capabilities
        })
        
        logger.info(f"Created tool {specification.name} with ID {tool_id}")
        return tool_id
    
    def _generate_tool_implementation(self, spec: ToolSpecification) -> str:
        """Generate Python code implementation for tool"""
        
        # Base template for tool implementation
        if spec.tool_type == ToolType.WEB_SCRAPING:
            return self._generate_web_scraper_implementation(spec)
        elif spec.tool_type == ToolType.DOCUMENT_GENERATION:
            return self._generate_document_generator_implementation(spec)
        elif spec.tool_type == ToolType.API_INTEGRATION:
            return self._generate_api_connector_implementation(spec)
        elif spec.tool_type == ToolType.DATA_PROCESSING:
            return self._generate_data_processor_implementation(spec)
        elif spec.tool_type == ToolType.COMMUNICATION:
            return self._generate_communication_implementation(spec)
        elif spec.tool_type == ToolType.AUTOMATION:
            return self._generate_automation_implementation(spec)
        elif spec.tool_type == ToolType.ANALYTICS:
            return self._generate_analytics_implementation(spec)
        elif spec.tool_type == ToolType.MONITORING:
            return self._generate_monitoring_implementation(spec)
        else:
            return self._generate_generic_implementation(spec)
    
    def _generate_web_scraper_implementation(self, spec: ToolSpecification) -> str:
        """Generate web scraper implementation"""
        return f"""
import requests
from bs4 import BeautifulSoup
import time

def {spec.name}(url, selectors=None, timeout=30):
    \"\"\"
    {spec.description}
    
    Args:
        url: Website URL to scrape
        selectors: CSS selectors for specific elements
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary containing scraped content
    \"\"\"
    try:
        headers = {{
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }}
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        result = {{
            'url': url,
            'title': soup.title.string if soup.title else '',
            'text': soup.get_text(),
            'links': [a.get('href') for a in soup.find_all('a', href=True)],
            'images': [img.get('src') for img in soup.find_all('img', src=True)],
            'selectors': {{}}
        }}
        
        if selectors:
            for name, selector in selectors.items():
                elements = soup.select(selector)
                result['selectors'][name] = [elem.get_text().strip() for elem in elements]
        
        return {{
            'success': True,
            'data': result,
            'timestamp': time.time()
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }}
        """.strip()
    
    def _generate_document_generator_implementation(self, spec: ToolSpecification) -> str:
        """Generate document generator implementation"""
        return f"""
from jinja2 import Template
import json

def {spec.name}(template, data, format='text'):
    \"\"\"
    {spec.description}
    
    Args:
        template: Template string or file path
        data: Data to populate template
        format: Output format ('text', 'html', 'markdown')
    
    Returns:
        Generated document content
    \"\"\"
    try:
        # If template is a file path, read it
        if template.endswith('.txt') or template.endswith('.html'):
            with open(template, 'r') as f:
                template_content = f.read()
        else:
            template_content = template
        
        # Create and render template
        jinja_template = Template(template_content)
        rendered_content = jinja_template.render(**data)
        
        # Apply format-specific processing
        if format == 'html':
            rendered_content = f'<html><body>{{rendered_content}}</body></html>'
        elif format == 'markdown':
            # Basic markdown formatting
            rendered_content = rendered_content.replace('\\n\\n', '\\n\\n')
        
        return {{
            'success': True,
            'content': rendered_content,
            'format': format,
            'template_used': template
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_api_connector_implementation(self, spec: ToolSpecification) -> str:
        """Generate API connector implementation"""
        return f"""
import requests
import json

def {spec.name}(url, method='GET', headers=None, data=None, auth=None):
    \"\"\"
    {spec.description}
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Request headers
        data: Request body data
        auth: Authentication credentials
    
    Returns:
        API response data
    \"\"\"
    try:
        # Default headers
        if headers is None:
            headers = {{'Content-Type': 'application/json'}}
        
        # Prepare request
        kwargs = {{
            'url': url,
            'method': method,
            'headers': headers,
            'timeout': 30
        }}
        
        if data:
            if method in ['POST', 'PUT']:
                if isinstance(data, dict):
                    kwargs['json'] = data
                else:
                    kwargs['data'] = data
        
        if auth:
            kwargs['auth'] = auth
        
        # Make request
        response = requests.request(**kwargs)
        
        # Parse response
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return {{
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'data': response_data,
            'headers': dict(response.headers)
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_data_processor_implementation(self, spec: ToolSpecification) -> str:
        """Generate data processor implementation"""
        return f"""
import pandas as pd
import numpy as np
import json

def {spec.name}(data, operations, config=None):
    \"\"\"
    {spec.description}
    
    Args:
        data: Input data (list, dict, or DataFrame)
        operations: List of processing operations
        config: Processing configuration
    
    Returns:
        Processed data
    \"\"\"
    try:
        if config is None:
            config = {{}}
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data
        
        # Apply operations
        for operation in operations:
            op_type = operation.get('type')
            
            if op_type == 'filter':
                condition = operation.get('condition')
                df = df.query(condition)
            
            elif op_type == 'transform':
                column = operation.get('column')
                func = operation.get('function')
                if column and func:
                    df[column] = df[column].apply(eval(func))
            
            elif op_type == 'aggregate':
                group_by = operation.get('group_by')
                agg_func = operation.get('function')
                if group_by:
                    df = df.groupby(group_by).agg(agg_func).reset_index()
            
            elif op_type == 'clean':
                # Remove duplicates and handle missing values
                df = df.drop_duplicates()
                df = df.fillna(operation.get('fill_value', ''))
        
        # Convert back to original format if needed
        if config.get('return_format') == 'list':
            result = df.to_dict('records')
        elif config.get('return_format') == 'dict' and len(df) == 1:
            result = df.iloc[0].to_dict()
        else:
            result = df
        
        return {{
            'success': True,
            'data': result,
            'operations_applied': len(operations)
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_communication_implementation(self, spec: ToolSpecification) -> str:
        """Generate communication tool implementation"""
        return f"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def {spec.name}(recipients, subject, body, attachments=None, smtp_server='smtp.gmail.com', port=587):
    \"\"\"
    {spec.description}
    
    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        body: Email body content
        attachments: List of file paths to attach
        smtp_server: SMTP server address
        port: SMTP port
    
    Returns:
        Success status
    \"\"\"
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_FROM', 'noreply@example.com')
        msg['To'] = ', '.join(recipients if isinstance(recipients, list) else [recipients])
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {{os.path.basename(file_path)}}'
                        )
                        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        
        # Login (use environment variables for credentials)
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        if email_user and email_password:
            server.login(email_user, email_password)
        
        server.send_message(msg)
        server.quit()
        
        return {{
            'success': True,
            'recipients': recipients,
            'subject': subject
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_automation_implementation(self, spec: ToolSpecification) -> str:
        """Generate automation tool implementation"""
        return f"""
import datetime
from typing import List, Dict, Any

def {spec.name}(events, reminders=None, timezone='UTC'):
    \"\"\"
    {spec.description}
    
    Args:
        events: List of event dictionaries
        reminders: Reminder configuration
        timezone: Timezone for events
    
    Returns:
        List of scheduled events
    \"\"\"
    try:
        if reminders is None:
            reminders = {{'default_days': [7, 3, 1]}}
        
        scheduled_events = []
        
        for event in events:
            event_data = {{
                'id': event.get('id', 'event_{{len(scheduled_events)}}'),
                'title': event.get('title', 'Untitled Event'),
                'description': event.get('description', ''),
                'start_time': event.get('start_time'),
                'end_time': event.get('end_time'),
                'timezone': timezone,
                'reminders': []
            }}
            
            # Generate reminders
            event_date = datetime.datetime.fromisoformat(event['start_time'])
            for days_before in reminders.get('default_days', []):
                reminder_date = event_date - datetime.timedelta(days=days_before)
                event_data['reminders'].append({{
                    'type': 'deadline_approaching',
                    'date': reminder_date.isoformat(),
                    'days_before': days_before
                }})
            
            scheduled_events.append(event_data)
        
        return {{
            'success': True,
            'scheduled_events': scheduled_events,
            'total_events': len(scheduled_events)
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_analytics_implementation(self, spec: ToolSpecification) -> str:
        """Generate analytics tool implementation"""
        return f"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64

def {spec.name}(data, report_type='summary', format='html'):
    \"\"\"
    {spec.description}
    
    Args:
        data: Input data for analysis
        report_type: Type of report to generate
        format: Output format
    
    Returns:
        Generated report
    \"\"\"
    try:
        # Convert data to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data
        
        report_content = []
        
        if report_type == 'summary':
            # Generate summary statistics
            report_content.append('DATA SUMMARY')
            report_content.append('=' * 50)
            report_content.append(str(df.describe()))
            report_content.append('')
            
            # Data info
            report_content.append('DATA INFO')
            report_content.append('=' * 50)
            report_content.append(f'Rows: {{len(df)}}')
            report_content.append(f'Columns: {{len(df.columns)}}')
            report_content.append(f'Missing values: {{df.isnull().sum().sum()}}')
        
        elif report_type == 'visualization':
            # Create basic visualizations
            plt.figure(figsize=(12, 8))
            
            # Numeric columns distribution
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                plt.subplot(2, 2, 1)
                df[numeric_cols].hist(bins=10)
                plt.title('Numeric Distributions')
            
            # Correlation heatmap
            if len(numeric_cols) > 1:
                plt.subplot(2, 2, 2)
                sns.heatmap(df[numeric_cols].corr(), annot=True)
                plt.title('Correlation Matrix')
            
            # Categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                plt.subplot(2, 2, 3)
                df[categorical_cols[0]].value_counts().plot(kind='bar')
                plt.title(f'{{categorical_cols[0]}} Distribution')
            
            plt.tight_layout()
            
            # Save plot to base64 for embedding
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            report_content.append(f'<img src="data:image/png;base64,{{plot_data}}" alt="Analysis Charts">')
        
        if format == 'html':
            return {{
                'success': True,
                'content': '<br>'.join(report_content),
                'format': 'html'
            }}
        else:
            return {{
                'success': True,
                'content': '\\n'.join(report_content),
                'format': 'text'
            }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_monitoring_implementation(self, spec: ToolSpecification) -> str:
        """Generate monitoring tool implementation"""
        return f"""
import time
import requests
from datetime import datetime

def {spec.name}(targets, metrics, thresholds=None):
    \"\"\"
    {spec.description}
    
    Args:
        targets: List of targets to monitor
        metrics: List of metrics to track
        thresholds: Threshold values for alerts
    
    Returns:
        Monitoring results
    \"\"\"
    try:
        if thresholds is None:
            thresholds = {{'response_time': 5.0, 'error_rate': 0.1}}
        
        results = {{
            'timestamp': datetime.now().isoformat(),
            'targets': {{}},
            'alerts': []
        }}
        
        for target in targets:
            target_results = {{
                'status': 'unknown',
                'response_time': None,
                'error_count': 0,
                'metrics': {{}}
            }}
            
            try:
                if target.startswith('http'):
                    # Monitor web endpoint
                    start_time = time.time()
                    response = requests.get(target, timeout=10)
                    response_time = time.time() - start_time
                    
                    target_results['status'] = 'healthy' if response.status_code < 400 else 'error'
                    target_results['response_time'] = response_time
                    
                    # Check thresholds
                    if response_time > thresholds.get('response_time', 5.0):
                        results['alerts'].append({{
                            'target': target,
                            'type': 'slow_response',
                            'value': response_time,
                            'threshold': thresholds.get('response_time', 5.0)
                        }})
                
                else:
                    # Monitor file or process
                    import os
                    if os.path.exists(target):
                        target_results['status'] = 'healthy'
                        target_results['metrics']['file_size'] = os.path.getsize(target)
                        target_results['metrics']['last_modified'] = os.path.getmtime(target)
                    else:
                        target_results['status'] = 'missing'
                        results['alerts'].append({{
                            'target': target,
                            'type': 'file_missing',
                            'message': f'File not found: {{target}}'
                        }})
            
            except Exception as e:
                target_results['status'] = 'error'
                target_results['error_count'] += 1
                results['alerts'].append({{
                    'target': target,
                    'type': 'error',
                    'message': str(e)
                }})
            
            results['targets'][target] = target_results
        
        return {{
            'success': True,
            'results': results,
            'total_targets': len(targets),
            'alerts_count': len(results['alerts'])
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def _generate_generic_implementation(self, spec: ToolSpecification) -> str:
        """Generate generic tool implementation"""
        return f"""
def {spec.name}(*args, **kwargs):
    \"\"\"
    {spec.description}
    
    Args:
        *args: Variable positional arguments
        **kwargs: Variable keyword arguments
    
    Returns:
        Tool execution result
    \"\"\"
    try:
        # Generic implementation that logs parameters and returns success
        result = {{
            'tool_name': '{spec.name}',
            'parameters_received': {{
                'args': args,
                'kwargs': kwargs
            }},
            'capabilities': {spec.capabilities},
            'message': 'Generic tool execution completed'
        }}
        
        return {{
            'success': True,
            'data': result
        }}
        
    except Exception as e:
        return {{
            'success': False,
            'error': str(e)
        }}
        """.strip()
    
    def get_tool(self, tool_id: str) -> Optional[ToolInstance]:
        """Get tool by ID"""
        return self.tools.get(tool_id)
    
    def get_tools_by_capability(self, capability: str) -> List[ToolInstance]:
        """Get tools that provide specific capability"""
        tool_ids = self.capability_matrix.get(capability, [])
        return [self.tools[tool_id] for tool_id in tool_ids if tool_id in self.tools]
    
    def execute_tool(self, tool_id: str, parameters: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Execute tool with given parameters"""
        if tool_id not in self.tools:
            return {"success": False, "error": "Tool not found"}
        
        tool = self.tools[tool_id]
        
        try:
            # Execute tool implementation
            # In a real system, this would use proper code execution
            exec_globals = {{}}
            exec(tool.implementation, exec_globals)
            
            # Get the function and execute it
            func_name = tool.specification.name
            if func_name in exec_globals:
                result = exec_globals[func_name](**parameters)
                
                # Update tool statistics
                tool.usage_count += 1
                tool.last_used = datetime.now()
                
                # Log usage
                self._log_tool_usage(tool_id, agent_id, parameters, result)
                
                return result
            else:
                return {"success": False, "error": "Tool function not found"}
                
        except Exception as e:
            # Update failure statistics
            if tool.usage_count > 0:
                tool.success_rate = (tool.success_rate * (tool.usage_count - 1)) / tool.usage_count
            
            return {"success": False, "error": str(e)}
    
    def expand_tool_capabilities(self, base_tool_id: str, new_capabilities: List[str], 
                               agent_id: str) -> str:
        """Expand existing tool with new capabilities"""
        if base_tool_id not in self.tools:
            return ""
        
        base_tool = self.tools[base_tool_id]
        
        # Create new specification with expanded capabilities
        new_spec = ToolSpecification(
            name=f"{{base_tool.specification.name}}_enhanced",
            description=f"{{base_tool.specification.description}} with additional capabilities",
            tool_type=base_tool.specification.tool_type,
            capabilities=list(set(base_tool.specification.capabilities + new_capabilities)),
            dependencies=base_tool.specification.dependencies,
            parameters=base_tool.specification.parameters,
            return_type=base_tool.specification.return_type,
            examples=base_tool.specification.examples
        )
        
        # Create enhanced tool
        enhanced_tool_id = self.create_tool(new_spec, agent_id)
        
        logger.info(f"Enhanced tool {{base_tool.specification.name}} with new capabilities: {{new_capabilities}}")
        return enhanced_tool_id
    
    def create_composite_tool(self, component_tool_ids: List[str], 
                            composite_name: str, agent_id: str) -> str:
        """Create composite tool from multiple component tools"""
        
        # Validate all component tools exist
        for tool_id in component_tool_ids:
            if tool_id not in self.tools:
                raise ValueError(f"Tool {{tool_id}} not found")
        
        # Collect capabilities from all components
        all_capabilities = []
        for tool_id in component_tool_ids:
            all_capabilities.extend(self.tools[tool_id].specification.capabilities)
        
        # Create composite specification
        composite_spec = ToolSpecification(
            name=composite_name,
            description=f"Composite tool combining {{len(component_tool_ids)}} tools",
            tool_type=ToolType.AUTOMATION,
            capabilities=list(set(all_capabilities)),
            dependencies=[],
            parameters={"workflow": "list", "config": "dict"},
            return_type="dict",
            examples=["Automated workflow using multiple tools"]
        )
        
        # Generate composite implementation
        composite_impl = self._generate_composite_implementation(component_tool_ids)
        
        # Create composite tool
        composite_tool_id = str(uuid.uuid4())
        composite_tool = ToolInstance(
            id=composite_tool_id,
            specification=composite_spec,
            implementation=composite_impl,
            created_by=agent_id,
            created_at=datetime.now()
        )
        
        self.tools[composite_tool_id] = composite_tool
        self._persist_tool(composite_tool)
        
        logger.info(f"Created composite tool {{composite_name}} from {{len(component_tool_ids)}} components")
        return composite_tool_id
    
    def _generate_composite_implementation(self, component_tool_ids: List[str]) -> str:
        """Generate implementation for composite tool"""
        impl_parts = []
        
        impl_parts.append("def composite_tool(workflow, config=None):")
        impl_parts.append('    \"\"\"Composite tool that executes multiple tools in sequence\"\"\"')
        impl_parts.append("    results = {}")
        impl_parts.append("    ")
        impl_parts.append("    for step in workflow:")
        impl_parts.append("        tool_name = step.get('tool')")
        impl_parts.append("        parameters = step.get('parameters', {})")
        impl_parts.append("        step_name = step.get('name', tool_name)")
        impl_parts.append("        ")
        impl_parts.append("        try:")
        impl_parts.append("            # This would execute the actual tool")
        impl_parts.append("            result = {'success': True, 'data': f'Executed {{tool_name}}'}")
        impl_parts.append("            results[step_name] = result")
        impl_parts.append("        except Exception as e:")
        impl_parts.append("            results[step_name] = {'success': False, 'error': str(e)}")
        impl_parts.append("            break  # Stop workflow on error")
        impl_parts.append("    ")
        impl_parts.append("    return {'success': True, 'workflow_results': results}")
        
        return "\\n".join(impl_parts)
    
    def get_tool_insights(self) -> Dict[str, Any]:
        """Get insights about tool usage and performance"""
        insights = {
            "total_tools": len(self.tools),
            "tools_by_type": {},
            "most_used_tools": [],
            "highest_success_rate": [],
            "recently_created": [],
            "capability_coverage": {},
            "recommendations": []
        }
        
        # Count tools by type
        for tool in self.tools.values():
            tool_type = tool.specification.tool_type.value
            insights["tools_by_type"][tool_type] = insights["tools_by_type"].get(tool_type, 0) + 1
        
        # Most used tools
        sorted_tools = sorted(self.tools.values(), key=lambda t: t.usage_count, reverse=True)
        insights["most_used_tools"] = [
            {"name": t.specification.name, "usage_count": t.usage_count}
            for t in sorted_tools[:5]
        ]
        
        # Highest success rate
        successful_tools = sorted(self.tools.values(), key=lambda t: t.success_rate, reverse=True)
        insights["highest_success_rate"] = [
            {"name": t.specification.name, "success_rate": t.success_rate}
            for t in successful_tools[:5]
        ]
        
        # Recently created
        recent_tools = sorted(self.tools.values(), key=lambda t: t.created_at, reverse=True)
        insights["recently_created"] = [
            {"name": t.specification.name, "created_at": t.created_at.isoformat()}
            for t in recent_tools[:5]
        ]
        
        # Capability coverage
        for capability, tool_ids in self.capability_matrix.items():
            insights["capability_coverage"][capability] = len(tool_ids)
        
        # Recommendations
        if len(self.tools) < 10:
            insights["recommendations"].append({
                "type": "expansion",
                "message": "Consider creating more specialized tools for common tasks"
            })
        
        low_usage_tools = [t for t in self.tools.values() if t.usage_count < 5]
        if len(low_usage_tools) > len(self.tools) * 0.5:
            insights["recommendations"].append({
                "type": "optimization",
                "message": f"{{len(low_usage_tools)}} tools have low usage - consider optimization"
            })
        
        return insights
    
    def _log_tool_usage(self, tool_id: str, agent_id: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log tool usage"""
        cursor = self.tools_db.cursor()
        cursor.execute('''
            INSERT INTO tool_usage (id, tool_id, agent_id, timestamp, parameters, result, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            tool_id,
            agent_id,
            datetime.now().isoformat(),
            json.dumps(parameters),
            json.dumps(result),
            result.get('success', False)
        ))
        self.tools_db.commit()
    
    def _persist_tool(self, tool: ToolInstance):
        """Persist tool to database"""
        cursor = self.tools_db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tools VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tool.id,
            tool.specification.name,
            tool.specification.description,
            tool.specification.tool_type.value,
            json.dumps(tool.specification.capabilities),
            json.dumps(tool.specification.dependencies),
            json.dumps(tool.specification.parameters),
            tool.specification.return_type,
            tool.implementation,
            tool.created_by,
            tool.created_at.isoformat(),
            tool.usage_count,
            tool.success_rate
        ))
        self.tools_db.commit()
    
    def _optimization_loop(self):
        """Background optimization loop"""
        while self.running:
            try:
                # Analyze tool usage patterns
                insights = self.get_tool_insights()
                
                # Optimize low-performing tools
                for tool in self.tools.values():
                    if tool.success_rate < 0.5 and tool.usage_count > 10:
                        logger.warning(f"Tool {{tool.specification.name}} has low success rate: {{tool.success_rate}}")
                
                # Suggest new tools based on usage patterns
                self._suggest_new_tools()
                
            except Exception as e:
                logger.error(f"Tool optimization error: {e}")
            
            time.sleep(3600)  # Run every hour
    
    def _suggest_new_tools(self):
        """Suggest new tools based on usage patterns"""
        # Analyze failed tool usages to identify gaps
        cursor = self.tools_db.cursor()
        cursor.execute('''
            SELECT parameters, error FROM tool_usage 
            WHERE success = FALSE 
            AND timestamp > datetime('now', '-1 day')
        ''')
        
        failed_usages = cursor.fetchall()
        
        # Look for patterns in failures that might indicate need for new tools
        # This is a simplified implementation
        if len(failed_usages) > 10:
            logger.info("High number of tool failures detected - consider creating specialized tools")
    
    def shutdown(self):
        """Shutdown the tool system"""
        self.running = False
        
        if self.optimization_thread:
            self.optimization_thread.join(timeout=10)
        
        if self.tools_db:
            self.tools_db.close()
        
        logger.info("Adaptive Tools System shutdown complete")

# Global instance
adaptive_tools = AdaptiveTools()