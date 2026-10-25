"""ローカル開発タスクの記録を、別途提供されたキットで検証する。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def outside(value):
    path = Path(value).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Keep the kit and task records outside the public checkout')
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['authorize', 'start', 'revise', 'complete', 'status', 'route'])
    parser.add_argument('--request', required=True)
    for name in ('state', 'policy', 'input', 'output'):
        parser.add_argument('--' + name)
    args = parser.parse_args(argv)
    try:
        if sys.version_info[:2] != (3, 12):
            raise ValueError('Python 3.12 is required; the kit uses only the standard library')
        kit = outside(os.environ['DEV_GUARDRAIL_KIT'])
        expected = os.environ['DEV_GUARDRAIL_REVISION']
        if len(expected) != 40 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('Supply the full reviewed kit commit in DEV_GUARDRAIL_REVISION')
        def git(*parts):
            return subprocess.check_output(['git', '-C', str(kit), *parts], text=True).strip()
        if git('rev-parse', '--show-toplevel') != str(kit):
            raise ValueError('Kit path must be its checkout root')
        if git('rev-parse', 'HEAD') != expected or git('status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Kit must be clean and match the consumer-reviewed revision')
        if not (kit / 'guardrails' / '__main__.py').is_file():
            raise ValueError('The supplied kit has no compatible task entry point')
        command = [sys.executable, '-B', '-m', 'guardrails', 'task', args.action]
        for name in ('request', 'state', 'policy', 'input', 'output'):
            value = getattr(args, name)
            if value:
                command.extend(['--' + name, str(outside(value))])
        # 外部の入力をシェルとして実行せず、キットの探索場所を固定する。
        env = dict(os.environ, PYTHONPATH=str(kit), PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run(command, cwd=kit, env=env, capture_output=True, text=True)
        result = json.loads(run.stdout)
        if not isinstance(result, dict):
            raise ValueError('Kit returned a non-object result')
        accepted = {
            'authorize': {'proceed_existing_authorization'},
            'route': {'canonical_context_ready', 'canonical_context_partial'},
            'start': {'audit_required'}, 'revise': {'audit_required'},
            'complete': {'local_workflow_contract_satisfied'},
            'status': {'local_workflow_contract_satisfied'},
        }
        ok = run.returncode == 0 and result.get('result') in accepted[args.action]
        if args.action == 'authorize':
            ok = ok and result.get('next_step') in {
                'execute_within_existing_scope', 'preserve_completed_action_do_not_repeat'}
        if args.action in ('complete', 'status'):
            ok = ok and result.get('local_workflow_complete') is True
        if args.action == 'route':
            result['next_step'] = ('continue_independent_paths_and_read_dependent_sources'
                                   if result.get('result') == 'canonical_context_partial'
                                   else 'review_declared_source_reads')
        result.setdefault('next_step', 'review_required_checks' if result.get('result') == 'audit_required'
                          else 'review_local_result' if ok else 'resolve_blocker')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    except (KeyError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'result': 'wrapper_blocked', 'next_step': 'resolve_local_configuration',
                          'reason': str(exc), 'external_actions_authorized': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
