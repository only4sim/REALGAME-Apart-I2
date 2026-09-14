# Subscription access decision

Status: prospective execution decision, recorded before target-model outcomes
on 2026-09-14. This document authorizes no expansion beyond the human-approved
pilot and does not report that the pilot has run or succeeded. Final adapter
tests and a fresh source/configuration/design freeze must precede experimental
calls. Subsequent outcomes belong in the immutable pilot ledger and
PILOT_RUN_REPORT.md, not in a retrospective rewrite of this decision.

## Incoming evidence and supported route

The requested incoming access/ACCESS_DECISION.md and the entire access/
directory were absent. Current access records were created during this
continuation; they are not recovered historical attachments. The earlier
verification/gate1_20260914T100612Z/ record reports zero experimental model
calls. Its API-route blockers are historical findings, not requirements for
the separate subscription route.

Official Codex CLI 0.154.0 is installed on the intended host. Direct version,
login-status and help checks established ChatGPT authentication and CLI/App
Server capabilities independently of the coordinator's conversation. Initial
ACCESS_DISCOVERY.json records three metadata RPC submissions: initialize,
model/list with includeHidden=false, and account/rateLimits/read. Metadata may
use the network; discovery was covered by the user's authorization. Later
boundary-audit RPCs are recorded separately below.

The visible catalog contains six models. The prospectively selected subject is
gpt-6-astra with medium reasoning effort and default service tier, using normal
official-client ChatGPT authentication. Startup metadata confirms these
configured settings. Startup configuration is not effective per-turn inference
telemetry: model_returned remains null unless the client explicitly returns
execution metadata. Never substitute a requested slug for a missing returned ID.

## Human approval and billing evidence

AUTHORIZE_PILOT.txt preserves permission for synthetic E1 prompts and permitted
visible histories, one worker, at most 20 episodes, 140 client invocations or
turn submissions, and 2700 seconds of experimental inference. Main-study
expansion, paid API fallback, extra credits, top-ups, auto-recharge changes,
resets, account rotation and publication are excluded.

The initial metadata snapshot reports ordinaryUsageAllowed=true, 7 percent
used in the codex bucket, hasCredits=false, unlimited=false, and balance="0".
Its returned planType remains prolite. These observations did not establish an
included-only billing lock, so inference initially stopped.

BILLING_CONTROL_CONFIRMATION.txt then records the human's statement that access
is from ChatGPT Pro and that the account has a control preventing extra-credit
use and automatic top-up. This account-control attestation resolves the
specific previously open billing question for the existing authorization. It
is human confirmation, not independently queried backend enforcement, and does
not relabel the earlier prolite telemetry. Unavailable credit-consumption and
monetary-cost telemetry remains null. No per-token zero-dollar claim follows
from the absence of an API key. Stop at quota or billing-route uncertainty
without purchasing, redeeming, changing authentication or falling back.

## Subject boundary evidence and limitations

Boundary preparation occurred before target-model prompts. Initial
SUBJECT_BOUNDARY_DISCOVERY.json records a process-closed error before thread
creation. A local configuration diagnostic identified that the named permission
profile also required default_permissions="realgame_subject". Adding that
invocation-local selection resolved startup; global login state and managed
service controls were not changed.

SUBJECT_BOUNDARY_DISCOVERY_02.json records structural startup success but lists
six system skills as enabled in its initial catalog. Its passed flag concerns
that audit's listed checks only; it was not final isolation acceptance and
produced no experimental turn. Explicit per-skill disables were then included
before a fresh audit.

SUBJECT_BOUNDARY_DISCOVERY_03.json records the accepted structural startup: all
six cataloged system skills disabled; empty instructionSources,
runtimeWorkspaceRoots and environments; an ephemeral fresh root thread with no
parent or fork; zero MCP servers with complete catalog pagination; and the
named realgame_subject permission profile. Exact invocation-local feature,
memory, instruction, tool and filesystem restrictions are preserved there.
HOST_BOUNDARY_CHECK.json records denied reads of benign temporary-directory and
repository markers under that same profile. The two checks are MOCK-NOT-LLM
host checks. No credentials or evidence files were read, and no target-model
turn or network probe was used for those checks.

These records support a constrained observation interface for this bounded
pilot. They do not expose a complete built-in-tool inventory or complete
assembled instructions, and benign read checks are not a universal containment
or blindness proof. Fresh threads, read-only mode and ephemeral history are
insufficient by themselves; acceptance rests on the combined restrictions,
disabled catalogs and host-denial checks. Retain this limitation in the pilot
and manuscript. Stop and preserve records if startup differs from the frozen
boundary or an unsupported tool is attempted.

## Prospective execution decision

Proceed with the authorized pilot after final adapter tests and the fresh
freeze. Use a fresh official App Server process and thread for each action or
probability response. Deliver unchanged benchmark SYSTEM/PROB text through
baseInstructions, the frozen wrapper through developerInstructions, and only
the remaining permitted role/content history as serialized input. Use no
outputSchema, replacement completion, wrapper retry, model/effort fallback or
separate compatibility turn.

Record process invocations and turn submissions separately, each capped at 140
under one persistent global ledger across output directories. A process serves
at most one turn; startup failures consume the invocation allowance. Do not sum
a startup and its single turn as two invocations. The 2700-second deadline
starts at the first experimental process invocation. Client-internal backend
retries may occur and must not be described as absent when counts are
unavailable. The full 20-cell schedule permits at most 108 benchmark turns. An announced
internal retry stops the pilot. Timeouts stop local waiting and new submissions;
unfinished turns receive one best-effort interrupt before process termination.
Backend cancellation acknowledgement and exact cessation time remain unknown.

This decision applies only to codex-subscription-pilot-v8. The original API
adapter remains unchanged with its separate credential, price and global-dollar
budget requirements. Historical scripted/mock evidence and the prospective
raw-API study remain separate. Human scientific, authorship, disclosure,
artifact-location and venue gates remain open; nothing is submitted or
published by this decision.
