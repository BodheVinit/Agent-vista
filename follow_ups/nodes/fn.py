import asyncio
from transcribe import split_audio
from followup_gen import InterviewState
from predefined_questions import pre_decided_questions
from convert_to_text import audio_to_transcribe  # Must return string transcript
from speak import text_to_speech

OUTPUT_DIR = "audio_chunk"
CHUNK_LENGTH_MS = 3*10 * 1000
audio_path = "./Docker in 100 Seconds.mp3"

agent = InterviewState(pre_decided_questions)
question_outputs = set()

# Process one chunk: transcribe + follow-up generation
async def process_chunk(chunk_path):
    transcribe_text = await asyncio.to_thread(audio_to_transcribe, chunk_path)
    await asyncio.to_thread(agent.update_transcript, transcribe_text)

    # Get question from this transcript chunk
    qtype, question_data = await asyncio.to_thread(agent.pick_next_question, transcribe_text)
    if question_data["score"] is not None:
        question_outputs.add((
            question_data["question"],
            question_data["score"]
        ))

async def follow_up_generations():
    chunk_paths = list(split_audio(audio_path, OUTPUT_DIR, CHUNK_LENGTH_MS))

    # Create async tasks
    tasks = [process_chunk(chunk) for chunk in chunk_paths]

    await asyncio.gather(*tasks)

    # Sort by score descending
    sorted_qs = sorted(question_outputs, key=lambda x: x[1], reverse=True)

    # print("\n🎯 Ranked Follow-Up Questions:\n")
    for i, (q, score) in enumerate(sorted_qs, 1):
        # print(f"{i}. {q} ({score}/5)")
        await text_to_speech(q,f"follow_up{i}","en-US-AndrewMultilingualNeural")


if __name__ == "__main__":
    asyncio.run(follow_up_generations())
