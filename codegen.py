#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path
import anthropic

def read_api_key():
    """Read Anthropic API key from ~/.mingdaoai/anthropic.key"""
    key_path = os.path.expanduser("~/.mingdaoai/anthropic.key")
    try:
        with open(key_path) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: API key file not found at {key_path}")
        sys.exit(1)

def read_prompt_from_text(text):
    """Read prompt directly from text input"""
    return text

def read_input_files(input_paths):
    """Read content of input files and directories"""
    file_contents = []
    for path in input_paths:
        if os.path.isfile(path):
            with open(path) as f:
                file_contents.append({
                    'path': path,
                    'content': f.read()
                })
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path) as f:
                        file_contents.append({
                            'path': file_path,
                            'content': f.read()
                        })
    return file_contents

def generate_code(prompt, output_dir, input_paths=None, model="claude-3-5-sonnet-20241022"):
    """Generate code snippets using Claude API and save directly to files"""
    api_key = read_api_key()
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input files if provided
    input_context = ""
    if input_paths:
        file_contents = read_input_files(input_paths)
        for file in file_contents:
            input_context += f"\n=== {file['path']} ===\n"
            input_context += file['content'] + "\n"
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # First ask for list of files with descriptions
        file_list_prompt = prompt
        if input_context:
            file_list_prompt = f"Reference files:\n{input_context}\n\nBased on these files and the request:\n{prompt}"
            
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "assistant", "content": "You are a helpful programming assistant. Based on the user's request, return a JSON array where each element has 'filepath' and 'description' fields, describing what each file will contain. Output the answer only with json array format. Do not include any other text in front of or behind the json array.\n"},
                {"role": "user", "content": file_list_prompt}
            ]
        )
        file_specs = json.loads(response.content[0].text)
        
        # Generate and save code for each file
        generated_files = {}
        
        for file_spec in file_specs:
            filepath = file_spec['filepath']
            description = file_spec['description']
            
            # Include previously generated files and input files in context
            generation_prompt = json.dumps({
                "file_info": {
                    "filepath": filepath,
                    "purpose": description
                },
                "context": {
                    "reference_files": input_context,
                    "generated_files": generated_files
                },
                "instructions": "Generate the code for this file. Output only the code content, without any formatting or JSON."
            }, indent=2)
            
            file_response = client.messages.create(
                model=model,
                max_tokens=4096*2,
                messages=[
                    {"role": "assistant", "content": "You are a helpful programming assistant."},
                    {"role": "user", "content": prompt + "\n\n" + generation_prompt}
                ]
            )
            
            code = file_response.content[0].text
            print(f"Generated code for {filepath} ({description}):")
            print(code)
            print("\n========")
            
            # Save the code to file
            full_path = os.path.join(output_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            try:
                with open(full_path, 'w') as f:
                    f.write(code)
                print(f"Created: {full_path}")
            except Exception as e:
                print(f"Error creating {full_path}: {str(e)}")
                continue
            
            # Add to generated files context as JSON
            generated_files[filepath] = {
                "description": description,
                "content": code
            }
            
    except Exception as e:
        print(f"Error generating code: {str(e)}")
        sys.exit(1)

def main():
    # Example usage:
    # python generator.py --text-prompt "Create a Python script to sort a list" --input src/ output_dir
    # python generator.py --text-prompt "Write a logging utility" --input lib.py,utils/ output_dir

    parser = argparse.ArgumentParser(description="Generate code snippets using Claude")
    parser.add_argument("--text-prompt", required=True, help="Direct text prompt for code generation")
    parser.add_argument("--input", required=True, help="Input files/directories (comma-separated) to use as reference")
    parser.add_argument("--output", required=True, help="Output directory for generated code")
    
    args = parser.parse_args()
    
    input_paths = None
    if args.input:
        input_paths = [p.strip() for p in args.input.split(',')]
    
    prompt = read_prompt_from_text(args.text_prompt)
    generate_code(prompt, args.output, input_paths)

if __name__ == "__main__":
    main()
