import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/interview"

def format_time(t0):
    return f"[{time.time() - t0:.1f} sec]"

async def test_axios_webhook_discussion():
    async with httpx.AsyncClient(timeout=60.0) as client:
        t0 = time.time()

        print(f"{format_time(t0)} 🚀 Starting test: Axios & Webhook Discussion")

        # Start interview
        start_payload = {
            "questions": "Explain how Axios and Webhooks work together and how to handle them securely.",
            "candidate_id": "candidate_axwh_001"
        }

        start_resp = await client.post(f"{BASE_URL}/start", json=start_payload)
        print(f"{format_time(t0)} 📩 /start → {start_resp.status_code}")

        if start_resp.status_code != 200:
            print(f"{format_time(t0)} ❌ Failed to start interview: {start_resp.text}")
            return

        Qid = start_resp.json()["Qid"]
        print(f"{format_time(t0)} ✅ Interview started. Qid = {Qid}")

        # Discussion
        discussion_chunks = [
            "Sure. So Axios is a popular HTTP client in JavaScript, commonly used in frontend apps like React to send POST or GET requests.",
            "When it comes to handling webhooks, the backend typically exposes an endpoint like /webhook to receive events from external systems.",
            "Axios can be used on the client side to test or trigger webhook events during development by simulating real payloads.",
            "On the backend, handling a webhook means verifying the payload, ensuring the signature is valid, and then processing the event, like 'user.created'.",
            "For example, Stripe or GitHub sends a POST request to our /webhook endpoint, and we need to parse the body and take actions like saving data or triggering workflows.",
            "Security is crucial. We often validate a signature header like X-Hub-Signature-256 to ensure the request came from a trusted source.",
            "Axios itself can also be used in Node.js to forward the webhook payload internally or to retry on failure.",
            "So in summary, Axios helps send or forward webhooks, while the backend needs to carefully receive, verify, and act on them."
        ]

        for idx, chunk in enumerate(discussion_chunks):
            is_final = idx == len(discussion_chunks) - 1

            stream_payload = {
                "Qid": Qid,
                "transcript": chunk,
                "candidate_id": "candidate_axwh_001",
                "final_chunk": is_final
            }

            print(f"{format_time(t0)} 🗣️ Sending chunk {idx + 1}/{len(discussion_chunks)} {'(final)' if is_final else ''}")
            stream_resp = await client.post(f"{BASE_URL}/stream", json=stream_payload)
            print(f"{format_time(t0)} 🔁 /stream → {stream_resp.status_code}")

            try:
                json_resp = stream_resp.json()
                if is_final:
                    print(f"{format_time(t0)} ✅ Final Response: {json_resp}")
                else:
                    print(f"{format_time(t0)} 📢 Chunk accepted: {json_resp.get('status', 'unknown')} (priority={json_resp.get('priority', '-')})")
            except Exception:
                print(f"{format_time(t0)} ⚠️ Non-JSON response: {stream_resp.text}")

        print(f"{format_time(t0)} 🎉 Axios & Webhook discussion simulation completed")

if __name__ == "__main__":
    asyncio.run(test_axios_webhook_discussion())
