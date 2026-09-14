#!/usr/bin/env python3
"""Inspect a fresh official-client thread without submitting any model turn.

Restrictive configuration is invocation-local. No global configuration, login,
managed policy, or provider safety setting is changed. Streams are filtered
before saving; this command does not request or retain reasoning content.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from codex_subscription import OfficialMetadataClient, MetadataError, METADATA_METHODS

PROFILE_OVERRIDES = [
    'forced_login_method="chatgpt"', 'model_provider="openai"',
    'default_permissions="realgame_subject"',
    'features.shell_tool=false', 'features.unified_exec=false',
    'features.apps=false', 'apps._default.enabled=false',
    'features.plugins=false', 'features.remote_plugin=false',
    'features.multi_agent=false', 'agents.enabled=false',
    'features.memories=false', 'memories.use_memories=false',
    'memories.generate_memories=false', 'features.hooks=false',
    'features.goals=false', 'features.skill_mcp_dependency_install=false',
    'features.code_mode.enabled=false',
    'features.context_management.experimental_mode=false',
    'tools.view_image=false', 'web_search="disabled"',
    'project_doc_max_bytes=0', 'history.persistence="none"',
    'developer_instructions=""', 'notify=[]', 'mcp_servers={}',
    'model_reasoning_summary="none"', 'show_raw_agent_reasoning=false',
    'hide_agent_reasoning=true', 'shell_environment_policy.inherit="none"',
    'permissions.realgame_subject.filesystem={ ":minimal"="read", "/home"="deny", "/workspaces"="deny", "/root"="deny", "/tmp"="deny", "/proc"="deny" }',
    'permissions.realgame_subject.network.enabled=false',
]


class BoundaryInspectionClient(OfficialMetadataClient):
    allowed_methods = METADATA_METHODS | frozenset({
        'skills/list', 'mcpServerStatus/list', 'thread/start'})


def skill_inventory(result):
    output = []
    if not isinstance(result.get('data'), list):
        raise MetadataError('invalid_skill_catalog')
    for entry in result['data']:
        if entry.get('errors'):
            raise MetadataError('skill_catalog_errors')
        for skill in entry.get('skills', []):
            if not isinstance(skill.get('path'), str):
                raise MetadataError('invalid_skill_path')
            output.append({key: skill.get(key) for key in ('name', 'path', 'enabled', 'scope')})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--disabled-skills-from', type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh inspection path')
    cfg = json.loads(args.config.read_text())
    effective_overrides = list(PROFILE_OVERRIDES)
    if args.disabled_skills_from:
        prior = json.loads(args.disabled_skills_from.read_text())
        effective_overrides.append(prior['skill_disable_cli_override'])
    output = {
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'protocol_version': cfg['protocol_version'],
        'inspection_kind': 'official_client_pre_turn_boundary_audit',
        'experimental_turn_submissions': 0, 'model_prompt_submissions': 0,
        'thread_start_requests': 0, 'passed': False,
        'client_version': cfg['client_version'],
        'profile_overrides': effective_overrides,
        'raw_stream_retained': False, 'managed_and_service_controls_retained': True,
        'complete_native_tool_inventory_available': False,
    }
    client = BoundaryInspectionClient(overrides=effective_overrides, experimental=True)
    try:
        with client:
            skills = skill_inventory(client.request('skills/list', {
                'cwds': [client.folder.name], 'forceReload': True}))
            output['initial_skills'] = skills
            disabled = 'skills.config=[' + ','.join(
                '{path=' + json.dumps(item['path']) + ',enabled=false}' for item in skills) + ']'
            overrides = dict()
            # thread/start accepts typed config overrides; dotted paths match
            # official invocation-local configuration names.
            overrides['skills.config'] = [{'path': item['path'], 'enabled': False} for item in skills]
            overrides['model_reasoning_effort'] = cfg['reasoning_effort']
            output['skill_disable_cli_override'] = disabled
            params = {
                'model': cfg['models'][0], 'modelProvider': 'openai',
                'allowProviderModelFallback': False,
                'cwd': client.folder.name, 'ephemeral': True,
                'environments': [], 'runtimeWorkspaceRoots': [],
                'selectedCapabilityRoots': [], 'dynamicTools': [],
                'permissions': 'realgame_subject', 'approvalPolicy': 'never',
                'baseInstructions': 'This thread is being inspected before any model turn. No model request is authorized by thread creation.',
                'developerInstructions': '', 'experimentalRawEvents': False,
                'config': overrides, 'serviceTier': 'default',
            }
            output['thread_start_requests'] += 1
            result = client.request('thread/start', params)
            thread = result.get('thread') or {}
            output['thread_start_response'] = {key: result.get(key) for key in (
                'model', 'modelProvider', 'reasoningEffort', 'serviceTier',
                'instructionSources', 'runtimeWorkspaceRoots', 'sandbox', 'activePermissionProfile')}
            output['thread_metadata'] = {key: thread.get(key) for key in (
                'ephemeral', 'environments', 'parentThreadId', 'forkedFromId')}
            mcp = client.request('mcpServerStatus/list', {
                'threadId': thread['id'], 'limit': 100, 'detail': 'toolsAndAuthOnly'})
            output['mcp_server_count'] = len(mcp.get('data', []))
            output['mcp_catalog_complete'] = not bool(mcp.get('nextCursor'))
            checks = {
                'all_catalog_skills_disabled': all(item.get('enabled') is False for item in skills),
                'no_instruction_sources': result.get('instructionSources') == [],
                'no_workspace_roots': result.get('runtimeWorkspaceRoots') == [],
                'no_environments': thread.get('environments') == [],
                'ephemeral': thread.get('ephemeral') is True,
                'fresh_thread': thread.get('parentThreadId') is None and thread.get('forkedFromId') is None,
                'requested_model_retained': result.get('model') == cfg['models'][0],
                'effort_retained': result.get('reasoningEffort') == cfg['reasoning_effort'],
                'named_restricted_profile': (result.get('activePermissionProfile') or {}).get('id') == 'realgame_subject',
                'no_mcp_servers': mcp.get('data') == [] and not mcp.get('nextCursor'),
            }
            output['checks'] = checks
            output['passed'] = all(checks.values())
            output['note'] = 'A passing structural startup check is not a full effective-tool or effective-instruction audit. Skills suppression and a benign host-denial test also require verification before inference.'
    except (MetadataError, OSError, KeyError, ValueError, TypeError) as error:
        output['error_category'] = str(error) if isinstance(error, MetadataError) else type(error).__name__
    finally:
        output['metadata_rpc_attempts'] = client.calls
        output['metadata_rpc_submissions'] = client.submissions
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(output, indent=2, allow_nan=False)+'\n')
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
