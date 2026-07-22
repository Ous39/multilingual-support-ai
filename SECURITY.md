# Security policy

This repository uses synthetic support content and must not contain real customer data, credentials, internal endpoints, production prompts, or company-confidential information.

Please report vulnerabilities privately to the repository owner rather than opening a public issue. Rotate any credential immediately if it is accidentally committed. The `.env` file is ignored; use `.env.example` only as a template.

The demonstration redacts common contact details and credentials, blocks basic prompt-injection patterns, and escalates low-confidence requests. These controls are educational and require additional testing, policy review, access controls, audit logging, rate limits, and threat modelling before production use.
