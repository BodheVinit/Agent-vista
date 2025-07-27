import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/interview"

candidate_id = "candidate_google_search_001"

# A simulated response broken into 7 chunks
# discussion_chunks = [
#     "First, when you type google.com into the browser, it checks if it already has the IP cached.",
#     "If not, the browser initiates a DNS lookup. This may go to the OS cache, or even your router, and eventually hit a DNS resolver.",
#     "Once the IP address is resolved, the browser opens a TCP connection using a 3-way handshake, often secured with TLS if it's HTTPS.",
#     "The browser then sends an HTTP GET request for the homepage of google.com.",
#     "The server responds with HTML, which includes links to CSS, JS, and images.",
#     "The browser parses the HTML, builds the DOM, and issues parallel requests for static assets.",
#     "Finally, once all assets are loaded and JavaScript is executed, the page becomes interactive.",
# ]
discussion_chunks = [
    # ✅ Good
    "When you type google.com into the browser, it checks if it already has the IP cached.",
    
    # 🚫 Wrong: DNS is not done over FTP
    "If not, the browser performs a DNS request using the FTP protocol to find the server's MAC address.",  # ❌ FTP, MAC address = wrong
    
    # ✅ Good
    "Once the IP is found, the browser uses TCP with a three-way handshake, then wraps it in TLS for HTTPS.",
    
    # 🚫 Misleading: HTTP doesn't run inside DNS
    "HTTP is sent directly inside DNS, which is more efficient because it's closer to the user.",  # ❌ HTTP inside DNS = false
    
    # ✅ Good
    "The browser receives the HTML and parses it into a DOM tree, then issues more requests for linked resources.",
    
    # 🚫 Vague/incorrect: DOM and cookies confused
    "The browser stores the entire DOM in cookies for faster reload next time.",  # ❌ DOM stored in cookies = wrong
    
    # ✅ Good
    "Once scripts and assets are loaded, the page is rendered and becomes interactive for the user."
]

async def run_test():
    print(f"[0.0 sec] 🚀 Starting test: What happens when you search google.com")
    start_time = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Start the interview
        start_payload = {
            "questions": "Can you walk me through what happens when you type google.com in the browser and hit enter?",
            "candidate_id": candidate_id,
        }
        resp = await client.post(f"{BASE_URL}/start", json=start_payload)
        t = round(time.time() - start_time, 1)
        print(f"[{t} sec] 📩 /start → {resp.status_code}")
        if resp.status_code != 200:
            print(f"[{t} sec] ❌ Interview start failed")
            return

        qid = resp.json()["Qid"]
        print(f"[{t} sec] ✅ Interview started. Qid = {qid}")

        # Stream discussion chunks
        for i, chunk in enumerate(discussion_chunks):
            stream_payload = {
                "Qid": qid,
                "transcript": chunk,
                "candidate_id": candidate_id,
                "final_chunk": i == len(discussion_chunks) - 1
            }

            await asyncio.sleep(1.5)  # Simulate real delay
            resp = await client.post(f"{BASE_URL}/stream", json=stream_payload)
            t = round(time.time() - start_time, 1)
            status = resp.status_code
            print(f"[{t} sec] 🗣️ Sending chunk {i+1}/{len(discussion_chunks)}")
            print(f"[{t} sec] 🔁 /stream → {status}")

            if i == len(discussion_chunks) - 1:
                print(f"[{t} sec] ✅ Final Response: {resp.json()}")
            else:
                accepted = resp.json().get("status", "-")
                prio = resp.json().get("priority", "-")
                print(f"[{t} sec] 📢 Chunk accepted: {accepted} (priority={prio})")

    t = round(time.time() - start_time, 1)
    print(f"[{t} sec] 🎉 Google.com discussion simulation completed")

if __name__ == "__main__":
    asyncio.run(run_test())
