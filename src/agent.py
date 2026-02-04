"""Main LiveKit agent entry point."""

import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, cli
from livekit.plugins import deepgram, elevenlabs, openai, silero

from src.assistant import InsuranceAssistant
from src.prompts.insurance_agent import INITIAL_GREETING_INSTRUCTIONS
from src.utils.constants import ELEVENLABS_VOICE_ID
from src.utils.logger import get_logger, setup_logger

# load environment variables
load_dotenv(".env.local")

# setup logging
setup_logger()
logger = get_logger(__name__)


async def insurance_agent(ctx: agents.JobContext):
    """Main insurance eligibility agent session. """
    logger.info(
        "starting_agent_session",
        room_name=ctx.room.name if ctx.room else None,
    )

    # speech-to-text (Deepgram)
    stt = deepgram.STT(
        model="nova-3",
        language="en",
    )

    # language model (OpenAI GPT-4o)
    llm = openai.LLM(
        model="gpt-4o",
        temperature=0.7,
    )

    # text-to-speech (ElevenLabs)
    # using default voice - can be overridden via ELEVENLABS_VOICE_ID env var
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", ELEVENLABS_VOICE_ID)
    tts = elevenlabs.TTS(
        voice_id=voice_id,
    )

    # voice activity detection (Silero)
    vad = silero.VAD.load()

    # agent session
    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
    )

    # initialize assistant with function tools
    assistant = InsuranceAssistant()

    # start session with room and assistant
    await session.start(room=ctx.room, agent=assistant)

    # initialize userdata for session storage
    session.userdata = {}

    # generate initial greeting
    await session.generate_reply(instructions=INITIAL_GREETING_INSTRUCTIONS)

    logger.info("agent_session_started")


if __name__ == "__main__":
    # Run the agent CLI
    cli.run_app(agents.WorkerOptions(entrypoint_fnc=insurance_agent))
