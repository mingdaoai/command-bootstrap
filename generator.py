#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path
import openai

def read_api_key():
    """Read OpenAI API key from ~/.mingdaoai/openai.key"""
    key_path = os.path.expanduser("~/.mingdaoai/openai.key")
    try:
        with open(key_path) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: API key file not found at {key_path}")
        sys.exit(1)

def read_prompt_from_file(file_path):
    """Read prompt from a file"""
    try:
        with open(file_path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {file_path}")
        sys.exit(1)

def read_prompt_from_text(text):
    """Read prompt directly from text input"""
    return text

def generate_code(prompt, model="gpt-4o-mini"):
    """Generate code snippets using ChatGPT API"""
    openai.api_key = read_api_key()
    
    valid_models = ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"]
    if model not in valid_models:
        print(f"Error: Invalid model. Choose from: {', '.join(valid_models)}")
        sys.exit(1)

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful programming assistant. Generate code based on the prompt and return a JSON array where each element has 'name' and 'code' fields. Output the answer only with json array format. Do not use triple quote to enclose the answer."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        print("Generated code:")
        print(content)
        print("\n========")
        return json.loads(content)
    except Exception as e:
        print(f"Error generating code: {str(e)}")
        sys.exit(1)

def create_files(snippets, output_dir):
    """Create files for each code snippet"""
    os.makedirs(output_dir, exist_ok=True)
    
    for snippet in snippets:
        if not all(key in snippet for key in ['name', 'code']):
            print("Error: Invalid snippet format")
            continue
            
        filename = os.path.join(output_dir, snippet['name'])
        try:
            with open(filename, 'w') as f:
                f.write(snippet['code'])
            print(f"Created: {filename}")
        except Exception as e:
            print(f"Error creating {filename}: {str(e)}")

def main():
    # Example usage:
    # python generator.py --text-prompt "Create a Python script to sort a list" output_dir
    # python generator.py --file-prompt prompt.txt output_dir
    # python generator.py --text-prompt "Write a logging utility" --model gpt-4o output_dir

    parser = argparse.ArgumentParser(description="Generate code snippets using ChatGPT")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text-prompt", help="Direct text prompt for code generation")
    group.add_argument("--file-prompt", help="Path to file containing the prompt")
    parser.add_argument("output_dir", help="Output directory for generated code")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model to use (gpt-4o, gpt-4o-mini, o1, o1-mini)")
    
    args = parser.parse_args()
    
    if args.text_prompt:
        prompt = read_prompt_from_text(args.text_prompt)
    else:
        prompt = read_prompt_from_file(args.file_prompt)
        
    snippets = generate_code(prompt, args.model)
    create_files(snippets, args.output_dir)

if __name__ == "__main__":
    main()
