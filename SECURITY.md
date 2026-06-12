# Security Policy

## Reporting a vulnerability

Please report security issues privately — **do not open a public GitHub issue.**

Email **security@unisonlabs.ai** with:

- a description of the issue and its impact,
- steps to reproduce (a proof-of-concept if you have one),
- any suggested remediation.

We aim to acknowledge within 3 business days and to keep you updated as we
investigate. We will credit reporters who want it once a fix ships.

## Scope

This repository is the **Python SDK** for the Unison brain API. It holds no
secrets and is not a security boundary — all authentication, authorization,
tenant isolation, and rate limiting are enforced **server-side** by the Unison
brain API. Reports about the client are most useful when they concern:

- credential handling in environment variables or on disk,
- dependency or supply-chain risks (e.g. malicious transitive deps),
- accidental credential logging or exposure via error messages.

Server-side or account issues should also go to the same address.

## Handling of credentials

The client reads your API key from the `UNISON_TOKEN` environment variable (or
the `token=` constructor argument). The token is never written to disk by this
library, never logged, and is transmitted only to the configured API host
(`UNISON_API_URL`, default `https://brain.unisonlabs.ai`) as an HTTP
`Authorization: Bearer <token>` header.

Store your key in a `.env` file (covered by `.gitignore`) or a secrets manager.
Never hard-code it in source files.
