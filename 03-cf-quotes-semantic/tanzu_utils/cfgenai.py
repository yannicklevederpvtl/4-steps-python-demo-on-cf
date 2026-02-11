"""
CFGenAIService - Utility to load GenAI service credentials from Cloud Foundry environment.

This module provides a utility class to discover and interact with GenAI services
bound to Cloud Foundry applications via VCAP_SERVICES environment variable.

Cloud Foundry Service Binding:
-----------------------------
When a service is bound to a Cloud Foundry application, Cloud Foundry automatically
injects service credentials into the VCAP_SERVICES environment variable as JSON.

Example VCAP_SERVICES structure:
{
  "user-provided": [
    {
      "name": "tanzu-nomic-embed-text",
      "credentials": {
        "endpoint": {
          "api_base": "https://genai-proxy.sys.tas.labs.com/...",
          "api_key": "bearer-token-here",
          "config_url": "https://genai-proxy.sys.tas.labs.com/.../config/v1/endpoint"
        }
      }
    }
  ]
}

The cfenv library (AppEnv) parses VCAP_SERVICES and provides easy access to
service credentials by name.
"""
import requests
from cfenv import AppEnv


class CFGenAIService:
    """
    Utility to load GenAI service credentials from Cloud Foundry environment (VCAP_SERVICES)
    and interact with the model config endpoint.
    
    This class discovers GenAI services (like tanzu-nomic-embed-text) that are bound
    to the Cloud Foundry application and provides access to their API credentials.
    
    Usage:
        # Initialize with service name (as it appears in VCAP_SERVICES)
        genai = CFGenAIService("tanzu-nomic-embed-text")
        
        # Access API credentials
        api_base = genai.api_base
        api_key = genai.api_key
        
        # List available models
        models = genai.list_models()
    """

    def __init__(self, service_name: str):
        """
        Initialize the service by discovering it from VCAP_SERVICES.
        
        Args:
            service_name: The name of the service as it appears in VCAP_SERVICES
                         (e.g., "tanzu-nomic-embed-text")
        
        Raises:
            ValueError: If the service is not found in VCAP_SERVICES
        """
        # Cloud Foundry automatically injects VCAP_SERVICES environment variable
        # when services are bound to the application
        env = AppEnv()
        
        # Discover the service by name from VCAP_SERVICES
        self.service = env.get_service(name=service_name)
        if not self.service:
            raise ValueError(
                f"Service '{service_name}' not found in VCAP_SERVICES. "
                f"Make sure the service is bound to the application."
            )

        # Extract credentials from the service binding
        # Cloud Foundry service credentials are nested in the service object
        creds = self.service.credentials
        
        # GenAI services provide endpoint configuration with:
        # - api_base: Base URL for API calls
        # - api_key: Bearer token for authentication
        # - config_url: URL to query available models
        endpoint = creds.get("endpoint", {})
        self.config_url = endpoint.get("config_url")
        self.api_base = endpoint.get("api_base")
        self.api_key = endpoint.get("api_key")

    def get_headers(self):
        """
        Get HTTP headers for API requests with authentication.
        
        Returns:
            dict: Headers dictionary with Authorization and Content-Type
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def list_models(self, insecure: bool = True):
        """
        Call the config endpoint and return advertised models.
        
        This method queries the service's config endpoint to discover
        available models and their capabilities.
        
        Args:
            insecure: If True, disable SSL certificate verification (default True).
                     Set to False to validate SSL certs. In demo environments with
                     self-signed certificates, this should be True.
        
        Returns:
            list: List of dictionaries with model details, each containing:
                  - name: Model name
                  - capabilities: List of model capabilities (e.g., ["EMBEDDING"])
        
        Raises:
            ValueError: If config_url is not found in service credentials
            requests.RequestException: If the API request fails
        """
        if not self.config_url:
            raise ValueError("No config_url found in service credentials")

        # Make API call to config endpoint
        # verify=not insecure handles self-signed certificates in demo environments
        response = requests.get(
            self.config_url,
            headers=self.get_headers(),
            verify=not insecure  # False = skip SSL verification (for self-signed certs)
        )
        response.raise_for_status()
        data = response.json()
        return data.get("advertisedModels", [])

    def __repr__(self):
        """String representation of the service for debugging."""
        return f"<CFGenAIService api_base={self.api_base} config_url={self.config_url}>"


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Example: Initialize with tanzu-nomic-embed-text service
    service_name = "tanzu-nomic-embed-text"
    try:
        genai = CFGenAIService(service_name)
        
        print("Service loaded:", genai)
        
        # List available models
        models = genai.list_models()
        print("Available models:")
        for m in models:
            print(f"- {m['name']} (capabilities: {', '.join(m['capabilities'])})")
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure the service is bound to the application in Cloud Foundry.")
