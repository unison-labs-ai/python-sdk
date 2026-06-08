"""Async usage example for the Unison brain Python SDK."""
import asyncio
import os

from unisonlabs import AsyncUnisonBrain


async def main() -> None:
    async with AsyncUnisonBrain(token=os.environ["UNISON_TOKEN"]) as client:
        me = await client.whoami()
        print(f"Authenticated as {me.user.email}")

        results = await client.search("auth decision", limit=3)
        for hit in results.results:
            print(f"  [{hit.score:.2f}] {hit.doc.path}")

        doc = await client.write(
            "/private/notes/async-example.md",
            "# Async Example\n\nWritten from the async client.",
        )
        print(f"Written: {doc.path}")


asyncio.run(main())
