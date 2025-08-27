#! /usr/bin/env python3
#
# POE client written with the help of POE - Updated for OpenAI-compatible API
#
# Example usage:
#   client = POEClient(base_url="https://api.poe.com/v1", api_key="your_api_key")
#   response = client.ask(model="gpt-3.5-turbo", question="What is the capital of France?")
#   print(response)
#

"""
A Python client for interacting with POE (Platform for Open Exploration) LLMs via OpenAI-compatible API.
This module provides a class for basic Q&A functionality and extensibility for advanced features.

Sample usage:
    POE_API="..." {script} --command "What is the color of MAGA?"
"""

# Standard modules
from typing import Any, Dict, Optional, List

# Installed modules
import requests

# Local modules
# TODO: def mezcla_import(name): ... components = eval(name).split(); ... import nameN-1.nameN as nameN
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system


# Environment options
POE_API = system.getenv_value(
    "POE_API", None,
    desc="API key for POE")
POE_MODEL = system.getenv_value(
    ## OLD: "POE_MODEL", "GPT-4.1-nano",
    "POE_MODEL", None,
    desc="Default model for POE")
POE_URL = system.getenv_text(
    "POE_URL", "https://api.poe.com/v1",
    desc="Base URL for POE API")
POE_TIMEOUT = system.getenv_float(
    "POE_TIMEOUT", 30,
    desc="Timeout for POE API call")


class POEClient:
    """
    A Python client for interacting with POE LLMs via OpenAI-compatible API.
    Supports basic Q&A functionality and is designed to be extensible.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: Optional[float] = None, model: Optional[str] = None):
        """
        Initialize the client with the base URL of the POE API and an API key.

        Args:
            base_url (str): The base URL of the POE API.
            api_key (str): The API key for authentication.
            timeout (float): Timeout for HTTP requests in seconds (e.g., 30).
            model (str): Default model to use.
        """
        debug.trace_expr(6, base_url, api_key, timeout, model,
                         prefix="in __init__: ")
        if base_url is None:
            base_url = POE_URL
        self.base_url = base_url.rstrip("/")
        if api_key is None:
            api_key = POE_API
        self.api_key = api_key
        if timeout is None:
            timeout = POE_TIMEOUT
        self.timeout = timeout
        if model is None:
            debug.assertion(POE_MODEL)
            model = POE_MODEL
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def _send_request(
        self, endpoint: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Internal method to send a request to the POE API.

        Args:
            endpoint (str): The API endpoint (relative to the base URL).
            payload (Optional[Dict[str, Any]]): The request payload (optional).
            method (str): The HTTP method ("POST" or "GET").

        Returns:
            Dict[str, Any]: The API response as a dictionary.

        Raises:
            RuntimeError: If the request fails due to an HTTP or connection error.
        """
        debug.trace_expr(5, endpoint, payload, method,
                         prefix="in _send_request: ")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(
                    url, headers=self.headers, json=payload, timeout=self.timeout
                )
            elif method.upper() == "GET":
                response = requests.get(
                    url, headers=self.headers, params=payload, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            debug.trace_object(6, response)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            
            result = response.json()
            debug.trace(5, f"_send_request() => {result}")
            return result
            
        except requests.exceptions.HTTPError as http_err:
            debug.raise_exception(6)
            error_details = ""
            try:
                error_response = http_err.response.json()
                error_details = f" - {error_response}"
            except:
                pass
            raise RuntimeError(
                f"HTTP error occurred: {http_err.response.status_code} {http_err.response.reason}{error_details}"
            ) from http_err
        except requests.exceptions.RequestException as req_err:
            debug.raise_exception(6)
            raise RuntimeError(f"Error in API request: {req_err}") from req_err

    def ask(self, question: str, model: Optional[str] = None, context: Optional[str] = None, 
            temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        Send a question to the specified model with optional context using OpenAI chat completions format.

        Args:
            question (str): The question to ask the model.
            model (Optional[str]): The name of the model to use (uses default if None).
            context (Optional[str]): Additional context for the model (optional).
            temperature (float): Controls randomness in the response (0.0 to 2.0).
            max_tokens (Optional[int]): Maximum number of tokens in the response.

        Returns:
            str: The model's response.
        """
        debug.trace_expr(6, model, question, context, temperature, max_tokens,
                         prefix="in ask: ")
        
        if model is None:
            model = self.model
            
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": question})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = self._send_request("chat/completions", payload)
        
        # Extract the response content from OpenAI format
        try:
            result = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            debug.trace(4, f"Unexpected response format:\n\t{response}\n\t{e}")
            result = response.get("output", str(response))
        debug.trace(5, f"ask() => {result}")
        return result

    def create_chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                              temperature: float = 0.7, max_tokens: Optional[int] = None,
                              stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Create a chat completion using the OpenAI chat completions format.

        Args:
            messages (List[Dict[str, str]]): List of messages in OpenAI format.
            model (Optional[str]): The name of the model to use.
            temperature (float): Controls randomness in the response.
            max_tokens (Optional[int]): Maximum number of tokens in the response.
            stream (bool): Whether to stream the response (not yet implemented).
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dict[str, Any]: The complete API response.
        """
        debug.trace_expr(6, messages, model, temperature, max_tokens, stream,
                         prefix="in create_chat_completion: ")
        
        if model is None:
            model = self.model
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
            
        if stream:
            payload["stream"] = stream
            # TODO: Implement streaming support
            debug.trace(3, "Warning: Streaming not yet implemented")

        result = self._send_request("chat/completions", payload)
        debug.trace(5, f"create_chat_completion() => {result}")
        return result

    def list_models(self) -> Dict[str, Any]:
        """
        List available models.

        Returns:
            Dict[str, Any]: The list of available models.
        """
        debug.trace(5, "in list_models")
        return self._send_request("models", method="GET")

    def call_function(self, function_name: str, arguments: Dict[str, Any], 
                     model: Optional[str] = None, context: Optional[str] = None) -> Any:
        """
        Call a specific function using function calling in chat completions.

        Args:
            function_name (str): The name of the function to call.
            arguments (Dict[str, Any]): The arguments for the function.
            model (Optional[str]): The name of the model to use.
            context (Optional[str]): Additional context for the function call.

        Returns:
            Any: The function's output.
        """
        debug.trace_expr(6, model, function_name, arguments, context,
                         prefix="in call_function: ")
        
        if model is None:
            model = self.model

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({
            "role": "user", 
            "content": f"Please call the function {function_name} with these arguments: {arguments}"
        })

        # Define the function for function calling
        functions = [{
            "name": function_name,
            "description": f"Call the {function_name} function",
            "parameters": {
                "type": "object",
                "properties": {key: {"type": "string"} for key in arguments.keys()},
                "required": list(arguments.keys())
            }
        }]

        payload = {
            "model": model,
            "messages": messages,
            "functions": functions,
            "function_call": {"name": function_name}
        }

        response = self._send_request("chat/completions", payload)
        
        try:
            function_call = response["choices"][0]["message"].get("function_call")
            if function_call:
                response = function_call.get("arguments", {})
            else:
                response = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            response = response.get("output")
        
        debug.trace(5, f"call_function() => {response}")
        return response

    def extend(self, extension_name: str, params: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """
        Extend the model's capabilities using chat completions with custom instructions.

        Args:
            extension_name (str): The name of the extension to apply.
            params (Dict[str, Any]): Parameters for the extension.
            model (Optional[str]): The name of the model to use.

        Returns:
            Dict[str, Any]: The extension's result.
        """
        debug.trace_expr(5, model, extension_name, params,
                         prefix="in extend: ")
        
        if model is None:
            model = self.model

        # Convert extension call to a chat completion
        system_message = f"You are operating in {extension_name} mode with the following parameters: {params}"
        user_message = f"Please process this request using the {extension_name} extension."

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        response = self.create_chat_completion(messages, model=model)
        debug.trace(5, f"extend() => {response}")
        return response


def main():
    """Entry point for testing"""
    debug.trace(4, "POE Client - OpenAI Compatible API")
    
    # Parse command line options, show usage if --help given
    LIST_MODELS_ARG = "list-models"
    COMMAND_ARG = "command"
    STDIO_ARG = "stdio"
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        boolean_options=[(LIST_MODELS_ARG, "List available LLM models"),
                         (STDIO_ARG, "Use stdin for command (and plain stdout for output)")],
        text_options=[(COMMAND_ARG, "Command or question for LLM")],
    )
    debug.assertion(main_app.parsed_args)
    list_models = main_app.get_parsed_option(LIST_MODELS_ARG)
    llm_command = main_app.get_parsed_option(COMMAND_ARG)
    use_stdio = main_app.get_parsed_option(STDIO_ARG)
    if use_stdio:
        debug.assertion(not llm_command)
        llm_command = main_app.read_entire_input()
    
    # Example usage
    if not POE_API:
        system.exit("Error: POE_API environment variable not set. Cannot run client.")
    try:
        client = POEClient()
        
        # Test model listing
        if list_models:
            models = client.list_models()
            print(f"Available models:\n\t{models}")
            
        # Test basic ask functionality
        if llm_command:
            response = client.ask(llm_command)
            print(f"Response:\n\t{response}" if not use_stdio else response)
        
    except:
        system.print_exception_info("Error testing client")

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(6)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
