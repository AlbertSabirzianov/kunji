# Security policy

Kunji handles API keys, so security reports get top priority.

## Reporting a vulnerability

**Please do not open a public issue.** Use GitHub's private reporting instead:
**Security → Report a vulnerability** on
[github.com/testwithsuraj/kunji](https://github.com/testwithsuraj/kunji/security/advisories/new).

Include what you found, how to reproduce it, and the impact you expect. You'll get an
acknowledgement within 3 days and a status update within 7 days. Please give us a reasonable
time to release a fix before disclosing publicly; we're happy to credit you.

## Supported versions

Only the latest minor release receives security fixes.

## Scope

In scope:

- API keys leaking (to disk, logs, terminal output, crash reports, or any server other than
  the key's own provider).
- Bypassing the OS keychain or writing secrets in plain text.
- Accepting forged or tampered responses from the kunji cloud check-in.
- Remote code execution or path traversal through config, cache, model names or responses.
- Supply-chain issues in our build and release workflows.

Out of scope: vulnerabilities in AI providers themselves, and issues that require an attacker
who already controls your user account.

## How kunji protects your keys

- Stored with [`keyring`](https://pypi.org/project/keyring/) in the OS credential store;
  environment variables are supported for CI.
- Never written to `config.toml`; error messages are scrubbed with `keystore.redact()`.
- Tracebacks never print local variables (Typer pretty exceptions are disabled).
- Keys are only sent over HTTPS to their own provider (plain HTTP is allowed only for local
  servers you add yourself, with a warning).
- Signed cloud responses (Ed25519) are verified before use; the private key never ships.
