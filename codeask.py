#!/usr/bin/env python3

import argparse
import os
import sys
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

def read_prompt_from_files(file_paths=None):
    """Read prompts from multiple files and combine them"""
    if file_paths is None:
        # Default to current directory if no paths provided
        file_paths = [os.getcwd()]
        print("\nNo files specified. Scanning current directory:")
        print(f"  Directory: {os.getcwd()}")
        
    combined_prompt = ""
    files = []
    
    # File extensions that typically contain source code
    code_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', 
                      '.swift', '.kt', '.rb', '.php', '.ts', '.scala', '.m', '.hpp'}
    
    # Silently discover files
    for path in file_paths:
        if os.path.isdir(path):
            # Add all code files from directory
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in code_extensions:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
        elif os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in code_extensions:
                files.append(path)
            
    if not files:
        print("\nError: No valid source code files found")
        sys.exit(1)

    assert len(files) <= 50, f"Too many files ({len(files)}). Maximum allowed is 50."
    
    # Sort files for consistent display
    files.sort()
    
    # Only show the summary
    print(f"\nSummary: Found {len(files)} files to analyze:")
    for file_path in files:
        relative_path = os.path.relpath(file_path, os.getcwd())
        print(f"  - {relative_path}")
    print()
        
    # Silently read file contents
    for file_path in files:
        try:
            with open(file_path) as f:
                content = f.read()
                combined_prompt += f"\n=== From {file_path} ===\n{content}\n"
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            sys.exit(1)
    
    return combined_prompt

class ChatSession:
    def __init__(self, files=None, model="claude-3-5-sonnet-20241022", context_window=5):
        self.model = model
        self.client = anthropic.Anthropic(api_key=read_api_key())
        # Always read files, using None to trigger current directory scan
        self.context = read_prompt_from_files(files)
        self.context_window = context_window
        self.conversation_history = []
        
        self.messages = [
            {"role": "assistant", "content": "You are a helpful programming assistant."}
        ]
        
        if self.context:
            self.messages.append({
                "role": "user", 
                "content": f"Here is the code context I'll be asking about:\n{self.context}"
            })
            self.messages.append({
                "role": "assistant", 
                "content": "I understand. I'll help answer questions about this code. What would you like to know?"
            })

    def _format_conversation_context(self):
        """Format recent conversation history for context"""
        if not self.conversation_history:
            return ""
            
        context = "\nRecent conversation history:\n"
        # Take the last n conversations from history
        recent = self.conversation_history[-self.context_window:]
        for i, (q, a) in enumerate(recent, 1):
            context += f"\nQ{i}: {q}\nA{i}: {a}\n"
        return context

    def chat(self, user_input):
        """Process a single chat message and stream the response"""
        try:
            # Add conversation context to the user's question
            conversation_context = self._format_conversation_context()
            enhanced_input = user_input
            if conversation_context:
                enhanced_input = f"{conversation_context}\nCurrent question: {user_input}"
            
            self.messages.append({"role": "user", "content": enhanced_input})
            
            # Stream the response
            print("\nClaude:", end=" ", flush=True)
            full_response = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                messages=self.messages
            ) as stream:
                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        print(chunk.delta.text, end="", flush=True)
                        full_response += chunk.delta.text
            
            print("\n")  # Add newline after streaming completes
            
            self.messages.append({"role": "assistant", "content": full_response})
            self.conversation_history.append((user_input, full_response))
            
            return full_response
            
        except Exception as e:
            return f"Error: {str(e)}"

def start_chat_interface():
    """Start an interactive chat interface"""
    parser = argparse.ArgumentParser(description="Interactive chat interface with Claude")
    parser.add_argument("--files", nargs="+", required=False, 
                       help="Paths to files or directories containing the code to analyze")
    parser.add_argument("--context-window", type=int, default=5,
                       help="Number of previous Q&A pairs to include in context (default: 5)")
    
    args = parser.parse_args()
    
    print("\nStarting code analysis with Claude...")
    chat_session = ChatSession(files=args.files, context_window=args.context_window)
    
    print("\nChat interface ready!")
    print("Type 'exit', 'quit', or press Ctrl+C to end the chat.")
    print("Type your message and press Enter. For multiple lines, keep typing and press Enter twice when done.")
    
    while True:
        # Get multiline input
        lines = []
        while True:
            try:
                prompt = "> " if not lines else "... (press Enter again to send)"
                line = input(prompt)
                if line:
                    lines.append(line)
                elif lines:  # Empty line and we have content
                    print("\nProcessing your question...", flush=True)
                    break
            except KeyboardInterrupt:
                print("\nGoodbye!")
                sys.exit(0)
        
        user_input = '\n'.join(lines)
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        chat_session.chat(user_input)  # Response is now printed during streaming

if __name__ == "__main__":
    start_chat_interface()
