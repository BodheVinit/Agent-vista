import asyncio
import httpx
import time
import random

BASE_URL = "http://localhost:8000/interview"

def format_time(t0):
    return f"[{time.time() - t0:.1f} sec]"

def print_divider():
    print("=" * 60)

# Simulated real discussion with a few weak chunks mixed in
discussion_chunks = [
    "Uh... I don't really remember exactly, but I think I worked with some people.",  # Weak
    "Actually, wait — let me think... um, yeah so it was with a senior dev.",         # Filler
    "In my final year project, our team had to refactor an entire legacy codebase.",
    "One member was unfamiliar with Git and caused some merge issues repeatedly.",
    "At first, I was frustrated, but then I offered to run a quick Git workshop.",
    "It helped the team work more efficiently, and the project shipped ahead of time.",
    "I learned that patience and small leadership actions matter a lot.",             # Strong
    "Also, sometimes you just have to step up when no one else does."                # Strong
]

async def test_interview_flow(simulate_delay=True):
    async with httpx.AsyncClient(timeout=60.0) as client:
        t0 = time.time()
        print_divider()
        print(f"{format_time(t0)} 🚀 Starting full interview flow test")

        # Step 1: Start
        start_payload = {
            "questions": "Tell me about a time you had to lead under pressure.",
            "candidate_id": "candidate_test_789"
        }

        start_resp = await client.post(f"{BASE_URL}/start", json=start_payload)
        print(f"{format_time(t0)} 📩 POST /start → {start_resp.status_code}")

        if start_resp.status_code != 200:
            print(f"{format_time(t0)} ❌ Failed to start interview: {start_resp.text}")
            return

        Qid = start_resp.json()["Qid"]
        print(f"{format_time(t0)} ✅ Interview started. Qid = {Qid}")
        print_divider()

        # Step 2: Stream transcript chunks
        for idx, chunk in enumerate(discussion_chunks):
            is_final = idx == len(discussion_chunks) - 1

            stream_payload = {
                "Qid": Qid,
                "transcript": chunk,
                "candidate_id": "candidate_test_789",
                "final_chunk": is_final
            }

            print(f"{format_time(t0)} 🗣️ Sending chunk {idx + 1}/{len(discussion_chunks)} {'(final)' if is_final else ''}")
            stream_resp = await client.post(f"{BASE_URL}/stream", json=stream_payload)
            print(f"{format_time(t0)} 🔁 POST /stream → {stream_resp.status_code}")

            try:
                resp_json = stream_resp.json()
                if "message" in resp_json:
                    print(f"{format_time(t0)} 📢 Chunk accepted: {resp_json['message']}")
                else:
                    print(f"{format_time(t0)} ✅ Final Response: {resp_json}")
            except Exception:
                print(f"{format_time(t0)} ⚠️ Non-JSON response: {stream_resp.text}")

            # Optional delay to simulate real-time chunking
            if simulate_delay:
                await asyncio.sleep(random.uniform(0.3, 0.7))

        print_divider()
        print(f"{format_time(t0)} 🎉 Interview simulation completed")

if __name__ == "__main__":
    asyncio.run(test_interview_flow(simulate_delay=True))
