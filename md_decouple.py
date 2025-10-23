#!/usr/bin/env python3
"""
Advanced Markdown Line Processor
Extracts code blocks from markdown files and saves them to appropriate file paths.
"""

import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging

class AdvancedMarkdownProcessor:
    """
    Advanced processor for extracting code blocks from markdown files.
    Supports multiple output formats, language detection, and advanced filtering.
    """
    
    def __init__(self, 
                 output_base_dir: str = "extracted_files",
                 log_level: str = "INFO",
                 overwrite: bool = False,
                 dry_run: bool = False):
        
        self.output_base_dir = Path(output_base_dir)
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.code_block_count = 0
        self.processed_files = 0
        
        # Initialize state variables
        self.state = ""  # "", "code-block", "frontmatter"
        self.lines: List[str] = []
        self.current_file_path = ""
        self.current_language = ""
        self.code_block_start_line = 0
        
        # Statistics
        self.stats = {
            'code_blocks': 0,
            'files_created': 0,
            'headlines': 0,
            'errors': 0
        }
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Language to file extension mapping
        self.language_extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yml',
            'yml': 'yml',
            'markdown': 'md',
            'bash': 'sh',
            'shell': 'sh',
            'sql': 'sql',
            'php': 'php',
            'ruby': 'rb',
            'go': 'go',
            'rust': 'rs'
        }
        
        self.logger.info(f"Initialized processor with output directory: {output_base_dir}")

    def process_markdown_file(self, input_file_path: str) -> bool:
        """
        Process a single markdown file.
        
        Args:
            input_file_path: Path to the markdown file to process
            
        Returns:
            bool: True if processing completed successfully
        """
        input_path = Path(input_file_path)
        
        if not input_path.exists():
            self.logger.error(f"Input file not found: {input_file_path}")
            return False
        
        self.logger.info(f"Processing markdown file: {input_file_path}")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    self._process_line(line.rstrip('\n\r'), line_num, input_path.name)
            
            # Flush any remaining code block at end of file
            if self.state == "code-block":
                self._flush_code_block()
            
            self.processed_files += 1
            self.logger.info(f"Completed processing {input_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {input_file_path}: {e}")
            self.stats['errors'] += 1
            return False

    def _process_line(self, line: str, line_num: int, filename: str):
        """Process a single line according to the rules with enhanced detection."""
        
        # Rule 1: File path declaration - **path/to/file** or ```path/to/file
        file_path_match = self._extract_file_path(line)
        if file_path_match:
            self.current_file_path = file_path_match
            self.logger.debug(f"File path captured at line {line_num}: {self.current_file_path}")
            return
        
        # Rule 2: Code block start with language specification
        code_block_match = re.match(r'^```(\w*)', line)
        if code_block_match and len(line) > 3:
            language = code_block_match.group(1)
            self._start_code_block(language, line_num)
            return
        
        # Rule 3: Code block end
        if line.strip() == '```':
            self._end_code_block()
            return
        
        # Rule 4: Frontmatter detection (for Jekyll/Hugo style markdown)
        if line.strip() == '---' and line_num == 1:
            if self.state == "":
                self.state = "frontmatter"
                self.logger.debug("Frontmatter started")
            elif self.state == "frontmatter":
                self.state = ""
                self.logger.debug("Frontmatter ended")
            return
        
        # Rule 5: In code block state - capture content
        if self.state == "code-block" and not line.startswith('`'):
            self.lines.append(line + '\n')
            return
        
        # Rule 6: Headline detection with level tracking
        headline_match = re.match(r'^(#+)\s+(.+)', line)
        if headline_match and self.state == "":
            level = len(headline_match.group(1))
            text = headline_match.group(2)
            self._process_headline(level, text, line_num)
            return
        
        # Rule 7: Table detection (skip processing tables)
        if line.strip().startswith('|') and self.state == "":
            self.logger.debug(f"Skipping table row at line {line_num}")
            return

    def _extract_file_path(self, line: str) -> Optional[str]:
        """Extract file path from various formats."""
        
        if line.startswith("**"):
            line =  line[0:line.rindex("**")]
            return line.replace("*","") 
        
        
    def _start_code_block(self, language: str, line_num: int):
        """Start a new code block."""
        if self.state == "code-block":
            self.logger.warning(f"Starting new code block at line {line_num} while previous one is active")
            self._flush_code_block()
        
        self.state = "code-block"
        self.current_language = language.lower() if language else ""
        self.code_block_start_line = line_num
        self.lines = []
        
        self.logger.debug(f"Code block started at line {line_num} (language: {language or 'none'})")

    def _end_code_block(self):
        """End the current code block."""
        if self.state == "code-block":
            self._flush_code_block()
        self.state = ""

    def _flush_code_block(self):
        """Flush the current code block to file."""
        if not self.lines:
            self.logger.debug("No content to flush")
            self.lines = []
            return
        
        # Determine output file path
        output_path = self._determine_output_path()
        if not output_path:
            self.logger.warning("No valid file path determined for code block")
            self.lines = []
            return
        
        # Skip if dry run
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create: {output_path} ({len(self.lines)} lines)")
            self.stats['code_blocks'] += 1
            self.lines = []
            return
        
        # Create directory structure
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and handle overwrite
            if output_path.exists() and not self.overwrite:
                self.logger.warning(f"File exists, skipping: {output_path} (use --overwrite to replace)")
                self.lines = []
                return
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(self.lines)
            
            self.stats['code_blocks'] += 1
            self.stats['files_created'] += 1
            self.logger.info(f"Created: {output_path} ({len(self.lines)} lines)")
            
        except Exception as e:
            self.logger.error(f"Error writing to {output_path}: {e}")
            self.stats['errors'] += 1
        
        # Reset for next code block
        self.lines = []
        self.current_file_path = ""
        self.current_language = ""

    def _determine_output_path(self) -> Optional[Path]:
        """Determine the output file path with intelligent extension detection."""
        
        if not self.current_file_path:
            # Generate filename based on language and block count
            if self.current_language and self.current_language in self.language_extensions:
                ext = self.language_extensions[self.current_language]
                filename = f"code_block_{self.stats['code_blocks'] + 1}.{ext}"
            else:
                filename = f"code_block_{self.stats['code_blocks'] + 1}.txt"
            
            self.current_file_path = filename
            self.logger.debug(f"Generated filename: {filename}")
        
        # Add extension if missing and language is known
        file_path = Path(self.current_file_path)
        if not file_path.suffix and self.current_language in self.language_extensions:
            ext = self.language_extensions[self.current_language]
            file_path = file_path.with_suffix(f'.{ext}')
        
        return self.output_base_dir / file_path

    def _process_headline(self, level: int, text: str, line_num: int):
        """Process headline with level information."""
        self.stats['headlines'] += 1
        self.logger.debug(f"Heading level {level} at line {line_num}: {text}")
        
        # Optional: Use headlines to create directory structure
        if level == 1 and not self.current_file_path:
            # Use H1 as base directory name
            safe_name = re.sub(r'[^\w\-_.]', '_', text.lower())
            self.output_base_dir = self.output_base_dir.parent / safe_name
            self.logger.info(f"Using H1 as base directory: {safe_name}")

    def process_directory(self, directory_path: str, pattern: str = "*.md"):
        """Process all markdown files in a directory."""
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            self.logger.error(f"Directory not found: {directory_path}")
            return
        
        md_files = list(dir_path.rglob(pattern))
        self.logger.info(f"Found {len(md_files)} markdown files in {directory_path}")
        
        for md_file in md_files:
            self.process_markdown_file(str(md_file))

    def print_statistics(self):
        """Print processing statistics."""
        print("\n" + "="*50)
        print("PROCESSING STATISTICS")
        print("="*50)
        print(f"Files processed:    {self.processed_files}")
        print(f"Code blocks found:  {self.stats['code_blocks']}")
        print(f"Files created:      {self.stats['files_created']}")
        print(f"Headlines found:    {self.stats['headlines']}")
        print(f"Errors encountered: {self.stats['errors']}")
        print(f"Output directory:   {self.output_base_dir}")
        print("="*50)
 
def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Advanced Markdown Line Processor")
    parser.add_argument("input", help="Input markdown file or directory")
    parser.add_argument("-o", "--output", default="extracted_files", 
                       help="Output directory (default: extracted_files)")
    parser.add_argument("--overwrite", action="store_true", 
                       help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be created without writing files")
    parser.add_argument("-l", "--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level (default: INFO)")
    parser.add_argument("--pattern", default="*.md",
                       help="File pattern for directory processing (default: *.md)")
    parser.add_argument("--create-sample", action="store_true",
                       help="Create a sample markdown file and exit")
    
    args = parser.parse_args()
 
    
    processor = AdvancedMarkdownProcessor(
        output_base_dir=args.output,
        log_level=args.log_level,
        overwrite=args.overwrite,
        dry_run=args.dry_run
    )
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        success = processor.process_markdown_file(args.input)
    elif input_path.is_dir():
        processor.process_directory(args.input, args.pattern)
    else:
        print(f"Error: Input path '{args.input}' not found")
        sys.exit(1)
    
    processor.print_statistics()
    
    if processor.stats['errors'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()