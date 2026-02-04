# Health LiveKit Insurance Agent

Voice agent that collects patient insurance info, checks eligibility via STEDI API, and provides copay information.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Voice Framework | LiveKit Agents |
| LLM | OpenAI GPT-4o |
| STT | Deepgram Nova-3 |
| TTS | ElevenLabs |
| VAD | Silero |
| Insurance API | STEDI |

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create `.env.local`:
```bash
STEDI_API_KEY=your_key
OPENAI_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
```

3. Run:
```bash
uv run src/agent.py console
```

## Testing

**Aetna only** For now (Trading Partner ID: 60054)

Test with:
- **Name:** Jane Doe
- **Member ID:** Say "A E T N A one two three four five"

System auto-converts to `AETNA12345` for API compatibility.

## Architecture: Agent + Tools (Not Workflows)

### Why We Chose This

The challenge requested **Workflow Nodes**, but I have used **Agent + Function Tools** instead.

**Workflow Nodes Approach:**
```
CollectName → CollectMemberID → RunStediQuery → CheckValid →
CheckActive → CheckCopay → RespondInNetwork/RespondOutNetwork
```

**Our Agent + Tools Approach:**
```
Agent (GPT-4o) → Decides which tool to call → Tools execute → Agent responds
```

### Benefits

1. **Natural conversation** - LLM manages state, handles corrections
2. **Faster iteration** - Change flow via prompt, not code
3. **Self-healing** - LLM handles unexpected inputs

### Tools

| Tool | Purpose |
|------|---------|
| `collect_patient_name` | Get/confirm name |
| `collect_member_id` | Get/confirm ID (auto-uppercase) |
| `run_stedi_query` | Call STEDI API |
| `validate_stedi_response` | Verify structure |
| `check_insurance_active` | Check active status |
| `find_stc98_copay` | Get copay + network status |

LLM orchestrates when to call these based on conversation context.

### Trade-off

**Workflows better for:** Compliance auditing, visual debugging, rigid processes

**Agent + Tools better for:** Natural conversation, voice assistants, rapid development

I chose Agent + Tools for better voice UX and simpler code.

## Structure

```
src/
├── agent.py                    # Entry point
├── assistant.py                # Agent + tools
├── prompts/insurance_agent.py  # Instructions
├── services/stedi_client.py    # API client
├── logic/                      # Business logic
└── utils/                      # Config + logging
```

## Limitations for now

- Aetna only (hardcoded Trading Partner ID: 60054)
- STEDI test/mock data only
- Console interface only
