import asyncio, websockets, sys

async def main():
    token = sys.argv[1]
    uri = f"ws://127.0.0.1:8000/ws/notifications?token={token}"
    async with websockets.connect(uri) as ws:
        print("Connected! Waiting for events... (trigger a checkout in another terminal)")
        try:
            async with asyncio.timeout(30):
                msg = await ws.recv()
                print("RECEIVED:", msg)
        except asyncio.TimeoutError:
            print("No message received in 30s (connection itself still succeeded)")

asyncio.run(main())
