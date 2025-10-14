import os
import yaml
from vita.config import DEFAULT_LANGUAGE

class Prompts:
    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self.language = language
        self._load_prompts()

    def _load_prompts(self):
        """Load prompts for the current language"""
        prompt_yamls = self.get_prompt_yamls()
        for prompt_yaml in prompt_yamls:
            prompt_name = prompt_yaml.split('.')[0]
            with open(os.path.join(os.path.dirname(__file__), prompt_yaml), 'r') as f:
                prompt_data = yaml.load(f, Loader=yaml.FullLoader)
                if self.language not in prompt_data:
                    raise ValueError(f"Language {self.language} not found in prompt {prompt_yaml}")
                setattr(self, prompt_name, prompt_data[self.language])

    def set_language(self, language: str):
        """Change the language and reload prompts"""
        self.language = language
        self._load_prompts()

    def get_prompt_yamls(self):
        prompt_yamls = []
        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith('.yaml'):
                prompt_yamls.append(file)
        return prompt_yamls

# Global prompts instance
prompts = Prompts()

def get_prompts(language: str = None) -> Prompts:
    """Get prompts instance with specified language"""
    if language is None:
        return prompts
    else:
        return Prompts(language)