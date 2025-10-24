import aiofiles
from pathlib import Path

CONTENT_DIR = Path(__file__).parent

async def get_content(file_name: str) -> str:
    """Read markdown content from file"""
    file_path = CONTENT_DIR / f"{file_name}.md"
    
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        return content
    except FileNotFoundError:
        return f"Content for '{file_name}' not found."
    except Exception as e:
        return f"Error reading content: {str(e)}"
