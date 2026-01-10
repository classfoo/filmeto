"""
Example Web Client for Filmeto API

Demonstrates how to use the Filmeto API via HTTP/REST endpoints.
"""

import requests
import json
import time
from typing import Iterator


class FilmetoWebClient:
    """Simple web client for Filmeto API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize web client.
        
        Args:
            base_url: Base URL of the Filmeto API server
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    def list_tools(self) -> list:
        """List available tools"""
        response = self.session.get(f"{self.base_url}/api/v1/tools")
        response.raise_for_status()
        return response.json()
    
    def list_plugins(self) -> list:
        """List available plugins"""
        response = self.session.get(f"{self.base_url}/api/v1/plugins")
        response.raise_for_status()
        return response.json()
    
    def get_plugins_by_tool(self, tool_name: str) -> list:
        """Get plugins for a specific tool"""
        response = self.session.get(
            f"{self.base_url}/api/v1/plugins/by-tool/{tool_name}"
        )
        response.raise_for_status()
        return response.json()
    
    def execute_task_stream(self, task_request: dict) -> Iterator[dict]:
        """
        Execute a task and stream results.
        
        Args:
            task_request: Task request dictionary
        
        Yields:
            Progress updates and final result
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/tasks/execute",
            json=task_request,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        
        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        pass


def example_basic_usage():
    """Basic usage example"""
    print("\n=== Basic Web Client Usage ===")
    
    client = FilmetoWebClient()
    
    # Check health
    print("Checking API health...")
    health = client.health_check()
    print(f"  Status: {health['status']}")
    
    # List tools
    print("\nAvailable tools:")
    tools = client.list_tools()
    for tool in tools:
        print(f"  • {tool['name']}")
    
    # List plugins
    print("\nAvailable plugins:")
    plugins = client.list_plugins()
    for plugin in plugins:
        print(f"  • {plugin['name']} - {plugin['description']}")


def example_text2image():
    """Text-to-image generation example"""
    print("\n=== Text to Image Generation ===")
    
    client = FilmetoWebClient()
    
    # Create task request
    task_request = {
        "tool_name": "text2image",
        "plugin_name": "text2image_demo",
        "parameters": {
            "prompt": "A beautiful landscape with mountains",
            "width": 512,
            "height": 512,
            "steps": 20
        },
        "resources": [],
        "timeout": 300
    }
    
    print(f"Executing task: {task_request['parameters']['prompt']}")
    
    # Execute and stream results
    for update in client.execute_task_stream(task_request):
        update_type = update.get('_type')
        
        if update_type == 'progress':
            percent = update.get('percent', 0)
            message = update.get('message', '')
            print(f"  Progress: {percent:.1f}% - {message}")
        
        elif update_type == 'result':
            status = update.get('status')
            print(f"\n✅ Result: {status}")
            
            if status == 'success':
                output_files = update.get('output_files', [])
                execution_time = update.get('execution_time', 0)
                print(f"   Execution time: {execution_time:.2f}s")
                print(f"   Output files: {output_files}")
        
        elif update_type == 'error':
            code = update.get('code')
            message = update.get('message')
            print(f"\n❌ Error: {code} - {message}")


def example_with_resource():
    """Example with resource input"""
    print("\n=== Image Processing with Resource ===")
    
    client = FilmetoWebClient()
    
    # First, generate a source image
    print("Generating source image...")
    source_task = {
        "tool_name": "text2image",
        "plugin_name": "text2image_demo",
        "parameters": {
            "prompt": "Source image",
            "width": 256,
            "height": 256,
            "steps": 5
        }
    }
    
    source_file = None
    for update in client.execute_task_stream(source_task):
        if update.get('_type') == 'result' and update.get('status') == 'success':
            source_file = update.get('output_files', [None])[0]
            print(f"✓ Source image: {source_file}")
            break
    
    if source_file:
        # Process the source image
        print("\nProcessing image...")
        process_task = {
            "tool_name": "image2image",
            "plugin_name": "text2image_demo",
            "parameters": {
                "prompt": "Enhanced version"
            },
            "resources": [
                {
                    "type": "local_path",
                    "data": source_file,
                    "mime_type": "image/png"
                }
            ]
        }
        
        for update in client.execute_task_stream(process_task):
            if update.get('_type') == 'result':
                print(f"✅ Processed: {update.get('status')}")


def main():
    """Run examples"""
    print("=" * 60)
    print("Filmeto Web Client Examples")
    print("=" * 60)
    print("\nNOTE: Make sure the Filmeto API server is running:")
    print("  python server/api/web_api.py")
    print()
    
    try:
        example_basic_usage()
        example_text2image()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()



