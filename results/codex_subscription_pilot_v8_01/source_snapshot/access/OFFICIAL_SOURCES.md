# Official access sources

Access date: 2026-09-14 (UTC). The incoming workspace did not contain the
referenced access source file; this record was created during this continuation.
Only official OpenAI documentation and installed-client public help/schema were
used. Documentation retrieval and model/usage metadata are separate from
experimental inference.

- [Codex App Server](https://learn.chatgpt.com/docs/app-server): documented
  initialization, model/list with hidden entries excluded, and account usage
  metadata. The local official client, not a private HTTP bridge, performed the
  three recorded metadata RPC submissions. No model thread was created.
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference):
  ChatGPT login restriction and service-tier controls do not document an
  included-only credit-consumption guarantee. No such request-side switch was
  established in the reviewed reference. The older
  https://developers.openai.com/codex/config-reference/ URL redirected here.
- [Codex pricing](https://learn.chatgpt.com/docs/pricing): included usage and
  additional credits are distinct; an active turn may continue after a usage
  limit. This is why a quota snapshot alone does not establish the requested
  billing boundary. No historical promotion was used to infer entitlement.
- [Workspace usage limits](https://learn.chatgpt.com/docs/enterprise/usage-limits)
  and [ChatGPT Work usage and cost](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-usage-and-cost):
  plan-specific controls must be applicable to the user's account. A limit on
  overage beyond workspace credits does not by itself prohibit consuming
  existing credits.

Installed-client evidence: Codex 0.154.0; successful `codex --version`, sanitized
`codex login status`, `codex exec --help`, and `codex app-server --help`.
`codex app-server generate-json-schema --experimental --out TEMP_DIRECTORY`
generated public schemas locally. Selected unmodified schemas and their hashes
are retained in verification/subscription_v8/client_schema/. They contain
interface definitions, not credentials or account data. No inference flags
were tested by sending an experimental prompt.

The billing conclusion is limited: the inspected interfaces did not establish
a control preventing extra-credit consumption and automatic top-ups. It is not
a claim that every official account configuration lacks such a control.
