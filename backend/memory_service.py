import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import UserMemory


class MemoryExtractor:
    """Extract user preferences and facts from conversations"""
    
    # Patterns to detect user preferences
    MEMORY_PATTERNS = [
        # Bootloader
        (r"(?:i use|i have|i'm using|i run)\s+(grub|limine|systemd-boot|refind)", "bootloader", "name"),
        (r"(?:my bootloader is|bootloader:\s*)(grub|limine|systemd-boot|refind)", "bootloader", "name"),
        (r"(?:not|don't use|don't have)\s+(grub|limine|systemd-boot)", "bootloader", "not_{}"),
        
        # Desktop Environment / Window Manager
        (r"(?:i use|i have|i'm using|i run)\s+(kde|gnome|xfce|i3|sway|hyprland|dwm|bspwm|awesome)", "desktop", "name"),
        (r"(?:my (?:de|wm|desktop) is|desktop:\s*)(kde|gnome|xfce|i3|sway|hyprland|dwm)", "desktop", "name"),
        
        # AUR Helper
        (r"(?:i use|i prefer|i have)\s+(yay|paru|trizen|pikaur)\b", "aur_helper", "name"),
        
        # GPU/Driver
        (r"(?:i have|i'm using|i use)\s+(?:an?\s+)?(nvidia|amd|intel)\s+(?:gpu|graphics|card)", "gpu", "vendor"),
        (r"(?:my gpu is|graphics:\s*)(nvidia|amd|intel)", "gpu", "vendor"),
        
        # Init System
        (r"(?:i use|i'm using)\s+(systemd|openrc|runit|s6)\b", "init_system", "name"),
        
        # Shell
        (r"(?:i use|i prefer|my shell is)\s+(bash|zsh|fish|dash)\b", "shell", "name"),
        
        # Text Editor
        (r"(?:i use|i prefer)\s+(vim|neovim|emacs|nano|helix)\b", "editor", "name"),
    ]
    
    @staticmethod
    def extract_memories(user_message: str, db: Session, user_id: int) -> List[Dict]:
        """Extract and store memories from user message"""
        extracted = []
        user_message_lower = user_message.lower()
        
        for pattern, category, key_template in MemoryExtractor.MEMORY_PATTERNS:
            matches = re.finditer(pattern, user_message_lower, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                
                # Handle negative patterns (e.g., "not grub")
                if key_template.startswith("not_"):
                    key = "excluded"
                    context = f"User does not use {value}"
                else:
                    key = key_template
                    context = f"User uses {value}"
                
                # Check if memory already exists
                existing = db.query(UserMemory).filter(
                    UserMemory.user_id == user_id,
                    UserMemory.category == category,
                    UserMemory.value == value
                ).first()
                
                if not existing:
                    memory = UserMemory(
                        user_id=user_id,
                        category=category,
                        key=key,
                        value=value,
                        confidence=0.9
                    )
                    db.add(memory)
                    extracted.append({
                        "category": category,
                        "key": key,
                        "value": value,
                        "context": context
                    })
        
        if extracted:
            db.commit()
        
        return extracted
    
    @staticmethod
    def get_user_memories(db: Session, user_id: int) -> str:
        """Format user memories for injection into LLM context"""
        memories = db.query(UserMemory).filter(UserMemory.user_id == user_id).all()
        
        if not memories:
            return ""
        
        # Group memories by category
        memory_groups = {}
        for mem in memories:
            if mem.category not in memory_groups:
                memory_groups[mem.category] = []
            memory_groups[mem.category].append(mem)
        
        # Format for LLM context
        context = "\n\n**USER PREFERENCES (remember these):**\n"
        
        category_names = {
            "bootloader": "Bootloader",
            "desktop": "Desktop Environment",
            "aur_helper": "AUR Helper",
            "gpu": "GPU",
            "init_system": "Init System",
            "shell": "Shell",
            "editor": "Text Editor"
        }
        
        for category, mems in memory_groups.items():
            category_label = category_names.get(category, category.replace("_", " ").title())
            values = [m.value for m in mems if m.key != "excluded"]
            excluded = [m.value for m in mems if m.key == "excluded"]
            
            if values:
                context += f"- **{category_label}**: {', '.join(values)}\n"
            if excluded:
                context += f"- Does NOT use: {', '.join(excluded)}\n"
        
        context += "\n*Always reference these preferences in your responses when relevant.*"
        return context
