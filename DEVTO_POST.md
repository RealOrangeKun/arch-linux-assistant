---
title: "Archy: AI-Powered Arch Linux Assistant with Memory"
published: false
description: "Full-stack AI assistant that remembers your system config and provides real-time Arch package data"
tags: github, copilot, archlinux, ai
cover_image: https://dev-to-uploads.s3.amazonaws.com/uploads/articles/YOUR_COVER_IMAGE.png
---

*This is a submission for the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21)*

## What I Built

**Archy** is an intelligent Arch Linux assistant that remembers your system preferences across conversations and provides real-time package information. Built entirely with GitHub Copilot CLI in ~5 hours.

### 🎯 Key Features

**🧠 Cross-Chat Memory**
```
You (Chat 1): "I use Hyprland and yay"
[Memory stored]

You (Chat 2): "How do I update my system?"
Archy: "Run yay -Syu to update..." (uses your AUR helper!)
```

**📦 Real-Time Package Data** - Fetches live versions from archlinux.org
**🔍 Web Search** - Searches when it doesn't know something
**🛡️ Strict Boundaries** - Only responds to Arch Linux topics (zero tolerance)
**💬 Modern UI** - Skeleton loading, stop button, markdown rendering

### Tech Stack
- **Backend**: FastAPI + PostgreSQL + Ollama (llama3.2)
- **Frontend**: React + Vite
- **Deployment**: Docker Compose (fully containerized)

## Demo

### 🚀 Try It Live

```bash
git clone https://github.com/RealOrangeKun/arch-linux-assistant.git
cd arch-linux-assistant
docker-compose up -d
docker exec -it arch-assistant-ollama ollama pull llama3.2
# Visit http://localhost:3000
```

**🔐 Test Account (for judges)**
- Email: `judge@devto.com`
- Password: `ArchyDemo2024!`

### Screenshots

**Chat Interface with Memory**
![Chat Demo](https://via.placeholder.com/800x400?text=Chat+Interface)

**Real-Time Package Search**
![Package Search](https://via.placeholder.com/800x400?text=Package+Search)

[🎥 Video Demo - Add your link here]

## GitHub Copilot CLI Experience

### 🚀 The Game Changer

GitHub Copilot CLI transformed this from a 2-3 week project into a **5-hour sprint**:

**Rapid Prototyping**
```bash
Me: "Create streaming chat endpoint with Ollama"
Copilot: [Complete async implementation with error handling]
Me: "Add skeleton loading with shimmer effect"
Copilot: [Full CSS animation + React component]
```

**Instant Debugging**
- SQLAlchemy session errors? Fixed in one go.
- CORS for streaming? Configured instantly.
- bcrypt compatibility? Downgraded and patched automatically.

**Architecture Guidance**
Copilot didn't just write code - it suggested:
- Using AbortController for cancellable requests
- Pattern matching for memory extraction
- Proper Docker networking with health checks

### 💡 Key Moments

**Most Impressive**: Asked for "skeleton loading animation" - got complete CSS with keyframes, shimmer effect, and React integration. First try. Just worked.

**Time Saved**: What would take 2-3 weeks of Stack Overflow searches took 5 focused hours.

## Technical Highlights

### Memory Extraction
```python
patterns = [
    (r"i use (hyprland|i3|kde)", "window_manager", "name"),
    (r"i prefer (yay|paru)", "aur_helper", "name"),
]
# Auto-stores in PostgreSQL for cross-chat recall
```

### Real-Time Package Intelligence
```python
if "install" in message:
    pkg = extract_package_name(message)
    data = await fetch_arch_api(pkg)  # Live version!
    inject_into_llm_context(data)
```

### Strict Boundaries
```python
SYSTEM_PROMPT = """
ABSOLUTE RULES - ZERO TOLERANCE:
- Only help with Arch Linux topics
- Refuse all off-topic questions immediately
- No fallback offers
"""
```

## Development Timeline

- **Hour 1**: Docker Compose + FastAPI + Auth ✅
- **Hour 2-3**: Chat streaming + Session management ✅
- **Hour 4**: Memory system + Package API ✅
- **Hour 5**: UI polish + Web search ✅

**Total: 5 hours** from zero to production-ready!

## Challenges Solved

**LLM Hallucinations** → Real-time API + context injection
**Rate Limits** → Graceful fallback with error messages
**Boundary Violations** → Extremely strict system prompts

## What I Learned

1. **Copilot CLI is a 10x multiplier** - Not replacing devs, amplifying them
2. **LLMs need guardrails** - Strict prompts prevent scope creep
3. **Context injection** - Real-time data prevents hallucinations
4. **UX matters** - Loading states and stop buttons improve experience

## Future Plans

- [ ] RAG with Arch Wiki
- [ ] AUR package support
- [ ] Command validation
- [ ] Voice interface

## Repository

🔗 **GitHub**: [RealOrangeKun/arch-linux-assistant](https://github.com/RealOrangeKun/arch-linux-assistant)

⭐ Star if you find it useful!

---

**Built with**: GitHub Copilot CLI, FastAPI, React, Ollama, PostgreSQL, Docker
**Time**: 5 hours | **Lines**: ~3,000 | **Fun**: Immeasurable 🚀

Try Archy and never repeat your system config again!

#GitHubCopilot #ArchLinux #AI #OpenSource
