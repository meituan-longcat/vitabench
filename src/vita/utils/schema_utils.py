"""Common utility functions for tool schema definitions

This file contains common functions and utilities used in all tool schema definition files.
"""

from typing import Dict, Any, Optional
from vita.config import DEFAULT_LANGUAGE

# Global tool description registry
TOOL_DESCRIPTIONS_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Global language configuration
_current_language = DEFAULT_LANGUAGE

# Global schema manager registry
_schema_managers: Dict[str, 'ToolSchemaManager'] = {}

def get_global_language() -> str:
    """Get current global language configuration

    Returns:
        Current language setting
    """
    return _current_language

def register_tool_descriptions(domain: str, descriptions: Dict[str, Dict[str, Any]]):
    """Register tool descriptions for a specific domain
    
    Args:
        domain: Domain name (e.g., 'delivery', 'instore', 'ota', 'toolkit')
        descriptions: Mapping dictionary from tool names to descriptions
    """
    TOOL_DESCRIPTIONS_REGISTRY[domain] = descriptions

def get_tool_description(domain: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Get tool description from registry
    
    Args:
        domain: Domain name
        tool_name: Tool name
        
    Returns:
        Tool description dictionary, returns None if not found
    """
    domain_descriptions = TOOL_DESCRIPTIONS_REGISTRY.get(domain, {})
    return domain_descriptions.get(tool_name)

def generate_tool_docstring(domain: str, tool_name: str, language: str = None) -> str:
    """Generate complete docstring for tool by combining all information

    Args:
        domain: Domain name
        tool_name: Tool name
        language: Language setting, if None then use global language setting

    Returns:
        Complete formatted docstring
    """
    if language is None:
        language = get_global_language()

    # If schema manager exists, prioritize using manager descriptions
    if domain in _schema_managers:
        manager = _schema_managers[domain]
        # Temporarily set language
        original_language = manager.language_config
        manager.set_language(language)
        tool_desc = manager.get_tool_description(tool_name)
        # Restore original language
        manager.set_language(original_language)
    else:
        tool_desc = get_tool_description(domain, tool_name)

    if not tool_desc:
        return ""
    
    # Build docstring
    docstring_parts = []
    
    # Description
    docstring_parts.append(tool_desc['description'])
    
    # Preconditions
    docstring_parts.append("Preconditions:")
    docstring_parts.append(f"    - {tool_desc['preconditions']}")
    
    # Postconditions
    docstring_parts.append("Postconditions:")
    docstring_parts.append(f"    - {tool_desc['postconditions']}")
    
    # Arguments
    docstring_parts.append("")
    docstring_parts.append("Args:")
    for arg_name, arg_desc in tool_desc['args'].items():
        docstring_parts.append(f"    {arg_name}: {arg_desc}")
    
    # Return value
    docstring_parts.append("")
    docstring_parts.append("Returns:")
    docstring_parts.append(f"    {tool_desc['returns']}")
    
    return "\n".join(docstring_parts)

def get_domain_from_class(cls) -> Optional[str]:
    """Extract domain name from class name or module path

    Args:
        cls: Class object

    Returns:
        Domain name, returns None if cannot determine
    """
    # Try to extract domain from class name
    class_name = cls.__name__.lower()

    # Common domain patterns
    if 'delivery' in class_name:
        return 'delivery'
    elif 'instore' in class_name:
        return 'instore'
    elif 'ota' in class_name:
        return 'ota'
    elif 'toolkitbase' in class_name or 'generictoolkit' in class_name:
        return 'toolkit'

    # Try to extract from module path
    module_name = cls.__module__.lower()
    if 'delivery' in module_name:
        return 'delivery'
    elif 'instore' in module_name:
        return 'instore'
    elif 'ota' in module_name:
        return 'ota'
    elif 'toolkit' in module_name:
        return 'toolkit'

    return None


def set_global_language(language: str):
    """Set global language configuration

    Args:
        language: Language setting ('chinese' or 'english')
    """
    global _current_language
    _current_language = language

    # Update language configuration for all registered schema managers
    for manager in _schema_managers.values():
        manager.set_language(language)

    # Re-register all tool descriptions
    for domain, manager in _schema_managers.items():
        TOOL_DESCRIPTIONS_REGISTRY[domain] = manager.get_tool_descriptions()


# Common tool description management class
class ToolSchemaManager:
    """Tool schema manager, provides common tool description management functionality"""
    
    def __init__(self, domain: str, descriptions_zh: Dict[str, Dict[str, Any]], 
                 descriptions_en: Dict[str, Dict[str, Any]]):
        """Initialize tool schema manager
        
        Args:
            domain: Domain name
            descriptions_zh: Chinese tool descriptions
            descriptions_en: English tool descriptions
        """
        self.domain = domain
        self.descriptions_zh = descriptions_zh
        self.descriptions_en = descriptions_en
        self.language_config = get_global_language()
        
        # Tool type mapping
        self._update_tool_type_mapping()

        # Register to global manager registry
        _schema_managers[domain] = self

        # Automatically register to global registry
        self._register_with_global_registry()

    def set_language(self, language: str):
        """Set language configuration

        Args:
            language: Language setting ('chinese' or 'english')
        """
        self.language_config = language
        self._update_tool_type_mapping()

    def _update_tool_type_mapping(self):
        """Update tool type mapping"""
        self.tool_type_mapping = {
            "GENERIC": "通用工具" if self.language_config == 'chinese' else "Generic Tool",
            "READ": "读取工具" if self.language_config == 'chinese' else "Read Tool",
            "WRITE": "写入工具" if self.language_config == 'chinese' else "Write Tool"
        }
    
    def get_tool_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool descriptions based on language configuration"""
        if self.language_config == 'english':
            return self.descriptions_en
        else:
            return self.descriptions_zh
    
    def get_tool_description(self, tool_name: str) -> Dict[str, Any]:
        """Get description of specific tool by name
        
        Args:
            tool_name: Tool name
            
        Returns:
            Dictionary containing tool description, preconditions, postconditions, arguments, return value and tool type
        """
        return self.get_tool_descriptions().get(tool_name, {})
    
    def get_all_tool_names(self) -> list:
        """Get list of all available tool names

        Returns:
            List of tool names
        """
        return list(self.get_tool_descriptions().keys())

    def get_tools_by_type(self, tool_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all tools of specific type

        Args:
            tool_type: Tool type (GENERIC, READ, or WRITE)

        Returns:
            Mapping dictionary from tool names to descriptions
        """
        return {
            name: desc for name, desc in self.get_tool_descriptions().items()
            if desc["tool_type"] == tool_type
        }

    def get_tool_count_by_type(self) -> Dict[str, int]:
        """Get tool count by type

        Returns:
            Mapping dictionary from tool type to count
        """
        counts = {}
        for desc in self.get_tool_descriptions().values():
            tool_type = desc["tool_type"]
            counts[tool_type] = counts.get(tool_type, 0) + 1
        return counts

    def get_tool_args(self, tool_name: str) -> Dict[str, str]:
        """Get arguments of specific tool by name

        Args:
            tool_name: Tool name

        Returns:
            Mapping dictionary from argument names to descriptions
        """
        tool_desc = self.get_tool_descriptions().get(tool_name, {})
        return tool_desc.get("args", {})

    def get_tool_returns(self, tool_name: str) -> str:
        """Get return value description of specific tool by name

        Args:
            tool_name: Tool name

        Returns:
            String describing tool return content
        """
        tool_desc = self.get_tool_descriptions().get(tool_name, {})
        return tool_desc.get("returns", "")

    def _register_with_global_registry(self):
        """Register tool descriptions to global toolkit registry"""
        try:
            register_tool_descriptions(self.domain, self.get_tool_descriptions())
        except ImportError:
            # If toolkit_schema is not available, skip registration
            pass

# Convenience function for creating and managing tool schemas
def create_tool_schema_manager(domain: str, descriptions_zh: Dict[str, Dict[str, Any]], 
                              descriptions_en: Dict[str, Dict[str, Any]]) -> ToolSchemaManager:
    """Convenience function to create tool schema manager
    
    Args:
        domain: Domain name
        descriptions_zh: Chinese tool descriptions
        descriptions_en: English tool descriptions
        
    Returns:
        Tool schema manager instance
    """
    return ToolSchemaManager(domain, descriptions_zh, descriptions_en)

# Common tool type mapping
def get_tool_type_mapping(language: str = None) -> Dict[str, str]:
    """Get tool type mapping
    
    Args:
        language: Language setting, if None then use global language setting

    Returns:
        Mapping from tool type to localized name
    """
    if language is None:
        language = get_global_language()

    return {
        "GENERIC": "通用工具" if language == 'chinese' else "Generic Tool",
        "READ": "读取工具" if language == 'chinese' else "Read Tool",
        "WRITE": "写入工具" if language == 'chinese' else "Write Tool"
    }