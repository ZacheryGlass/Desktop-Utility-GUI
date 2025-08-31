import subprocess
import sys
import importlib.util
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .script_analyzer import ScriptInfo, ExecutionStrategy, ArgumentInfo

logger = logging.getLogger('Core.ScriptExecutor')

@dataclass
class ExecutionResult:
    success: bool
    message: str = ""
    output: str = ""
    error: str = ""
    return_code: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

class ScriptExecutor:
    def __init__(self, settings=None):
        self.loaded_modules = {}
        self.settings = settings
    
    def execute_script(self, script_info: ScriptInfo, arguments: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Execute a script using the appropriate strategy."""
        if not script_info.is_executable:
            return ExecutionResult(
                success=False,
                error=f"Script is not executable: {script_info.error}"
            )
        
        if arguments is None:
            arguments = {}
        
        logger.debug(f"Executing script {script_info.display_name} with strategy {script_info.execution_strategy}")
        
        try:
            if script_info.execution_strategy == ExecutionStrategy.SUBPROCESS:
                return self._execute_subprocess(script_info, arguments)
            elif script_info.execution_strategy == ExecutionStrategy.FUNCTION_CALL:
                return self._execute_function_call(script_info, arguments)
            elif script_info.execution_strategy == ExecutionStrategy.MODULE_EXEC:
                return self._execute_module(script_info, arguments)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unknown execution strategy: {script_info.execution_strategy}"
                )
                
        except Exception as e:
            logger.error(f"Error executing script {script_info.display_name}: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    def _execute_subprocess(self, script_info: ScriptInfo, arguments: Dict[str, Any]) -> ExecutionResult:
        """Execute script as subprocess with command line arguments."""
        cmd = [sys.executable, str(script_info.file_path)]
        
        # Add arguments
        for arg_info in script_info.arguments:
            if arg_info.name in arguments:
                value = arguments[arg_info.name]
                if value is not None and value != "":
                    cmd.extend([f"--{arg_info.name}", str(value)])
            elif arg_info.required:
                return ExecutionResult(
                    success=False,
                    error=f"Required argument '{arg_info.name}' not provided"
                )
        
        logger.debug(f"Executing command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.get_script_timeout_seconds() if self.settings else 30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            success = result.returncode == 0
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            # Try to parse output as JSON for structured data
            data = None
            message = output
            if output:
                try:
                    data = json.loads(output)
                    if isinstance(data, dict):
                        message = data.get('message', output)
                        success = data.get('success', success)
                except json.JSONDecodeError:
                    pass
            
            return ExecutionResult(
                success=success,
                message=message,
                output=output,
                error=error,
                return_code=result.returncode,
                data=data
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error="Script execution timed out (30 seconds)"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Subprocess execution failed: {str(e)}"
            )
    
    def _execute_function_call(self, script_info: ScriptInfo, arguments: Dict[str, Any]) -> ExecutionResult:
        """Execute script by importing and calling main function."""
        try:
            # Load or reload the module
            module_name = script_info.file_path.stem
            
            if module_name in self.loaded_modules:
                # Reload module for changes; ensure present in sys.modules for reload()
                module = self.loaded_modules[module_name]
                try:
                    if module_name not in sys.modules:
                        sys.modules[module_name] = module
                    importlib.reload(module)
                except Exception:
                    # If reload fails (e.g., not in sys.modules), fall back to fresh load
                    spec = importlib.util.spec_from_file_location(module_name, script_info.file_path)
                    if spec is None or spec.loader is None:
                        return ExecutionResult(
                            success=False,
                            error=f"Could not load module spec for {script_info.file_path}"
                        )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self.loaded_modules[module_name] = module
            else:
                # Load module for first time
                spec = importlib.util.spec_from_file_location(module_name, script_info.file_path)
                if spec is None or spec.loader is None:
                    return ExecutionResult(
                        success=False,
                        error=f"Could not load module spec for {script_info.file_path}"
                    )
                
                module = importlib.util.module_from_spec(spec)
                # Insert into sys.modules before execution to support reloads/circular imports
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                self.loaded_modules[module_name] = module
            
            # Get the main function
            if not hasattr(module, script_info.main_function or 'main'):
                return ExecutionResult(
                    success=False,
                    error=f"Function '{script_info.main_function or 'main'}' not found in script"
                )
            
            main_func = getattr(module, script_info.main_function or 'main')
            
            # Prepare function arguments
            func_args = []
            func_kwargs = {}
            
            # Check function signature to determine how to pass arguments
            import inspect
            sig = inspect.signature(main_func)
            
            for param_name, param in sig.parameters.items():
                if param_name in arguments:
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        func_kwargs[param_name] = arguments[param_name]
                    elif param.kind == inspect.Parameter.POSITIONAL_ONLY:
                        func_args.append(arguments[param_name])
            
            # Call the function
            result = main_func(*func_args, **func_kwargs)
            
            # Process the result
            success = True
            message = ""
            data = None
            
            if result is None:
                message = "Script executed successfully"
            elif isinstance(result, dict):
                data = result
                success = result.get('success', True)
                message = result.get('message', 'Script executed successfully')
            elif isinstance(result, str):
                message = result
            elif isinstance(result, bool):
                success = result
                message = "Script executed successfully" if result else "Script execution failed"
            else:
                message = str(result)
            
            return ExecutionResult(
                success=success,
                message=message,
                data=data
            )
            
        except Exception as e:
            logger.error(f"Function call execution failed: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Function execution failed: {str(e)}"
            )
    
    def _execute_module(self, script_info: ScriptInfo, arguments: Dict[str, Any]) -> ExecutionResult:
        """Execute script by importing the entire module."""
        try:
            module_name = script_info.file_path.stem
            
            # Set up arguments in sys.argv if the script expects them
            original_argv = sys.argv.copy()
            
            try:
                # Build argv list
                sys.argv = [str(script_info.file_path)]
                for arg_info in script_info.arguments:
                    if arg_info.name in arguments:
                        value = arguments[arg_info.name]
                        if value is not None and value != "":
                            sys.argv.extend([f"--{arg_info.name}", str(value)])
                
                # Import and execute the module
                spec = importlib.util.spec_from_file_location(module_name, script_info.file_path)
                if spec is None or spec.loader is None:
                    return ExecutionResult(
                        success=False,
                        error=f"Could not load module spec for {script_info.file_path}"
                    )
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                return ExecutionResult(
                    success=True,
                    message="Script executed successfully"
                )
                
            finally:
                # Restore original argv
                sys.argv = original_argv
                
        except Exception as e:
            logger.error(f"Module execution failed: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Module execution failed: {str(e)}"
            )
    
    def get_script_status(self, script_info: ScriptInfo) -> str:
        """Get current status of a script (if applicable)."""
        # For now, return a simple status
        if not script_info.is_executable:
            return "Error"
        
        # Could be enhanced to check actual status for toggle/cycle scripts
        return "Ready"
    
    def validate_arguments(self, script_info: ScriptInfo, arguments: Dict[str, Any]) -> List[str]:
        """Validate provided arguments against script requirements."""
        errors = []
        
        for arg_info in script_info.arguments:
            if arg_info.required and arg_info.name not in arguments:
                errors.append(f"Required argument '{arg_info.name}' is missing")
            
            if arg_info.name in arguments:
                value = arguments[arg_info.name]
                
                # Check choices
                if arg_info.choices and value not in arg_info.choices:
                    errors.append(f"Argument '{arg_info.name}' must be one of: {', '.join(arg_info.choices)}")
                
                # Basic type checking
                if arg_info.type == 'int':
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Argument '{arg_info.name}' must be an integer")
                elif arg_info.type == 'float':
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Argument '{arg_info.name}' must be a number")
        
        return errors
