"""Basic usage examples for the Unison brain Python SDK.

Set UNISON_TOKEN=usk_live_... before running.
"""

import os

from unisonlabs import UnisonBrain

client = UnisonBrain(
    token=os.environ["UNISON_TOKEN"],  # or omit to read from env automatically
)

# Confirm auth
me = client.whoami()
print(f"Authenticated as {me.user.email} (tenant: {me.tenant.name})")

# Search the brain
results = client.search("architecture decisions", limit=5)
for hit in results.results:
    print(f"  [{hit.score:.2f}] {hit.doc.path} — {hit.doc.title}")

# Read a document
doc = client.get("/tenant/projects/architecture.md")
print(doc.body)

# Write a document (path must be under /private/, /tenant/, or /teams/<slug>/)
doc = client.write(
    "/private/notes/my-note.md",
    "# My Note\n\nThis is a test note.",
    title="My Note",
    tags=["test"],
)
print(f"Written: {doc.path}")

# Surgical in-place edit
doc = client.edit_doc(
    "/private/notes/my-note.md",
    "This is a test note.",
    "This is an updated note.",
)

# Entity graph
entity_resp = client.entities.resolve("Daniel")
if entity_resp.entity:
    entity = entity_resp.entity
    facts = client.entities.facts(entity.id)
    for f in facts.facts:
        print(f"  {f.predicate}: {f.factText}")

# Record a new fact
client.facts.record(
    subject_id="entity-id-here",
    predicate="works_at",
    fact_text="Joined Unison in 2026",
    confidence=0.9,
)

# Brain status
status = client.status()
print(f"Brain: {status.docCount} docs, {status.entityCount} entities, {status.factCount} facts")

client.close()
