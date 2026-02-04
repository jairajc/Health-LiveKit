# How to Test the Agent

## ✅ Option 1: Console Mode (Immediate Testing)

Test with text input/output (no LiveKit room needed):

```bash
uv run src/agent.py console
```

Then type your responses:
```
Agent: Hi! I'm your insurance eligibility assistant...
You: Jane Doe
Agent: Thank you. Could you provide your member ID?
You: AETNA12345
Agent: [Checks STEDI API and responds with copay]
```

---

## ✅ Option 2: Web Interface (Real Voice)

1. **Start the agent:**
   ```bash
   uv run src/agent.py dev
   ```

2. **Create a test room:**
   - Go to: https://agents-playground.livekit.io/
   - Or go to your LiveKit Cloud dashboard
   - Create a new room
   - The agent will automatically join

3. **Join the room and speak:**
   - Use your microphone
   - Speak naturally: "My name is Jane Doe"
   - Agent will respond with voice

---

## ✅ Option 3: Production Mode

For production deployment:

```bash
uv run src/agent.py start
```

This connects to LiveKit Cloud and waits for room assignments from your application.

---

## 🎯 Quick Test Now

Just run:
```bash
uv run src/agent.py console
```

This lets you test immediately with text!
