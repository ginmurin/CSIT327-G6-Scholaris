import os

def load_prompt(prompt_name):
    """Load a prompt template from the prompts directory."""
    prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
    prompt_path = os.path.join(prompts_dir, f'{prompt_name}.txt')
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}.txt")
