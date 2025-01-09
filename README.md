# Command Bootstrap

## Overview

Command Bootstrap is a powerful command-line tool that supercharges your development workflow by harnessing the intelligence of OpenAI's ChatGPT! With just a simple prompt, it instantly generates high-quality code snippets, eliminating the tedium of writing boilerplate code and common patterns. Say goodbye to repetitive coding tasks and hello to lightning-fast development!

## Features

- Generate complete code snippets from natural language descriptions
- Support for both inline prompts and prompt files
- Automatic directory creation and file management
- JSON-formatted output for easy parsing and organization

## Usage

The tool `generator.py` accepts command line arguments for:
1. The user's prompt (either as a string or file path)
2. The target directory for generated code
3. The model to use for code generation (optional, defaults to `gpt-4o-mini`)

If any required arguments are missing, the tool will display usage instructions.

### Example Commands

- Generate code from a direct text prompt:
  ```bash
  python generator.py --text-prompt "Create a Python script to sort a list" output_dir
  ```

- Generate code from a prompt file:
  ```bash
  python generator.py --file-prompt prompt.txt output_dir
  ```

- Generate code with a specific model:
  ```bash
  python generator.py --text-prompt "Write a logging utility" --model gpt-4o output_dir
  ```

## How It Works

1. The tool processes the user's prompt and desired output location
2. It sends the prompt to ChatGPT to generate relevant code snippets
   - The API key is saved as a single line in file "~/.mingdaoai/openai.key"
   - The model can be chosen from: gpt-4o, gpt-4o-mini, o1, and o1-mini.  The default is gpt-4o-mini.
3. The response is formatted as a JSON array, where each element contains:
   - A descriptive name for the code snippet
   - The actual code content
4. The tool then creates individual files for each snippet in the specified directory

## Implementation

The core functionality is implemented in `generator.py`, which handles:
- Command line argument parsing
- Directory management
- API communication with ChatGPT
- JSON parsing and file creation

## License

This project is open-sourced under the MIT License - see the LICENSE file for details.
