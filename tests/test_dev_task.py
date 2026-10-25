"""外部キットを実際に呼び出す、ローカル限定の結合テスト。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


class DevelopmentTaskTests(unittest.TestCase):
    def setUp(self):
        source = Path(os.environ['DEV_TASK_TEST_INPUTS']).resolve()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.request, self.policy, self.package = [json.loads((source / (name + '.json')).read_text())
                                                  for name in ('request', 'policy', 'completion')]
        self.assertEqual(self.request['origin'], 'fixture')
        self.write('request', self.request)
        self.write('policy', self.policy)
        self.write('completion', self.package)
        self.write('authorization', self.package['authorization'][0])

    def write(self, name, value):
        (self.directory / (name + '.json')).write_text(json.dumps(value))

    def call(self, action, success=True, **files):
        args = [sys.executable, '-B', str(ROOT / 'tools/dev_task.py'), action,
                '--request', str(self.directory / 'request.json')]
        for key, name in files.items():
            args += ['--' + key, str(self.directory / (name + '.json'))]
        run = subprocess.run(args, capture_output=True, text=True)
        result = json.loads(run.stdout)
        self.assertEqual(run.returncode == 0, success, result)
        self.assertIn('next_step', result)
        self.assertFalse(result['external_actions_authorized'])
        return result

    def start(self):
        return self.call('start', policy='policy', output='started')

    def complete(self):
        self.start()
        return self.call('complete', state='started', input='completion', output='finished')

    def test_lifecycle_and_status(self):
        result = self.call('authorize', input='authorization')
        self.assertEqual(result['next_step'], 'execute_within_existing_scope')
        self.assertTrue(self.complete()['local_workflow_complete'])
        result = self.call('status', state='finished')
        self.assertFalse(result['semantic_truth_verified'])
        self.assertFalse(result['overall_complete'])

    def test_pending_status_is_not_success(self):
        self.start()
        self.assertEqual(self.call('status', success=False, state='started')['result'], 'audit_required')

    def test_authorization_denial_uncertainty_and_scope(self):
        for case in ('denied', 'uncertain', 'target', 'revoked', 'completed'):
            with self.subTest(case=case):
                record = copy.deepcopy(self.package['authorization'][0])
                if case == 'denied':
                    record['access']['status'] = 'denied'
                elif case in ('uncertain', 'completed'):
                    record['prior_execution'] = dict(status=case, action_digest=digest(record['action']),
                                                     evidence_ref='fixture://execution')
                elif case == 'target':
                    record['action']['target'] = 'outside-scope'
                else:
                    record['grants'][0]['status'] = 'revoked'
                self.write('authorization', record)
                result = self.call('authorize', success=case == 'completed', input='authorization')
                self.assertFalse(result['action_may_proceed_under_declared_grants'])
                if case == 'completed':
                    self.assertEqual(result['next_step'], 'preserve_completed_action_do_not_repeat')

    def test_invalid_completion_is_not_saved(self):
        self.start()
        for case in ('stale', 'necessity', 'audit', 'hash', 'circular', 'followup'):
            with self.subTest(case=case):
                package = copy.deepcopy(self.package)
                if case == 'stale':
                    package['request_digest'] = 'outdated'
                elif case == 'necessity':
                    package['assessment']['necessity'] = 'unknown'
                elif case == 'audit':
                    package['audit']['reviewed_rules'] = []
                elif case == 'hash':
                    package['audit']['check_evidence'][0]['artifact_hash'] = 'changed'
                elif case == 'circular':
                    package['assessment']['evidence_refs'] += [package['audit']['record_id']]
                else:
                    package['followups'] = [dict(outcome=self.request['outcome'], target='outside-scope',
                        necessary_for_paths=[self.policy['paths'][0]['id']], evidence_ref='fixture://evidence', rationale='test')]
                self.write('bad', package)
                self.call('complete', success=False, state='started', input='bad', output='rejected')
                self.assertFalse((self.directory / 'rejected.json').exists())

    def test_revision_reuses_only_unchanged_checks(self):
        self.complete()
        self.policy['previous_inventory'] = [dict(id=n['id'], node_digest=digest(n))
                                             for n in self.policy['rules'] + self.policy['paths']]
        self.policy['requirement_revision'] += '-updated'
        self.policy['rules'][0]['version'] += '-updated'
        self.request['instruction'] += ' Updated requirement.'
        self.write('request', self.request)
        self.write('policy', self.policy)
        result = self.call('revise', state='finished', policy='policy', output='revised')
        self.assertTrue(result['prior_completion_stale'])
        self.assertTrue(result['reusable_checks'])
        self.assertTrue(result['plan']['required_checks'])
        self.assertFalse(set(result['reusable_checks']) & set(result['plan']['required_checks']))
        self.call('complete', success=False, state='revised', input='completion', output='stale')

    def test_unchanged_revision_and_overwrite_rejected(self):
        self.complete()
        self.call('revise', success=False, state='finished', policy='policy', output='revised')
        self.call('start', success=False, policy='policy', output='started')

    def route(self, context, success=True):
        self.write('canonical', context)
        return self.call('route', success=success, policy='policy', input='canonical')

    def test_canonical_fields_required_and_ready_route(self):
        result = self.route(self.package['canonical'])
        self.assertEqual(result['result'], 'canonical_context_ready')
        self.assertFalse(result['canonical_truth_authenticated'])
        self.start()
        del self.package['canonical']
        self.write('old-package', self.package)
        self.call('complete', success=False, state='started', input='old-package', output='old-finished')

    def test_stale_source_preserves_independent_work(self):
        for field, value in [('version', 'stale'), ('identity', 'fixture://wrong'),
                             ('request_digest', 'old-session'), ('status', 'unavailable')]:
            with self.subTest(field=field):
                context = copy.deepcopy(self.package['canonical'])
                for binding in context['rule_bindings'][1:]:
                    binding.update(kind='current_user_instruction', source_id='',
                                   version=digest(self.request), requirement_ref=self.request['source_ref'])
                context['reads'][0][field] = value
                result = self.route(context)
                self.assertEqual(result['result'], 'canonical_context_partial')
                self.assertTrue(result['blocked_paths'])
                self.assertTrue(result['independently_available_paths'])
                self.assertEqual(result['next_step'], 'continue_independent_paths_and_read_dependent_sources')
        self.start()
        self.package['canonical'] = context
        self.write('partial-package', self.package)
        self.call('complete', success=False, state='started', input='partial-package', output='partial-finished')

    def test_superseded_source_cannot_be_revived(self):
        context = copy.deepcopy(self.package['canonical'])
        source = copy.deepcopy(context['sources'][0])
        source.update(id='replacement', identity='fixture://designated-repo-procedure',
                      layer='repo_procedure', supersedes=[source['id']])
        context['sources'].append(source)
        read = copy.deepcopy(context['reads'][0])
        read.update(id=source['id'], identity=source['identity'])
        context['reads'].append(read)
        self.route(context, success=False)
        for binding in context['rule_bindings']:
            binding.update(source_id=source['id'], requirement_ref=source['identity'])
        self.assertEqual(self.route(context)['result'], 'canonical_context_ready')

    def test_observations_cannot_be_requirements_or_operations(self):
        context = copy.deepcopy(self.package['canonical'])
        context['rule_bindings'][0]['kind'] = 'observation_log'
        self.route(context, success=False)
        context = copy.deepcopy(self.package['canonical'])
        context['operations'] = [dict(id='old-log', path=self.policy['paths'][0]['id'],
            requirement_kind='observation_log', requirement_ref='fixture://old-log',
            change_kind='ci_only', generated_hash=None, deployed_hash=None, comparison_ref='')]
        self.route(context, success=False)

    def test_missing_kit_and_public_record_paths_rejected(self):
        command = [sys.executable, '-B', str(ROOT / 'tools/dev_task.py'), 'status', '--request', str(ROOT / 'request.json')]
        for env in (os.environ.copy(), dict(os.environ, DEV_GUARDRAIL_KIT='')):
            run = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(json.loads(run.stdout)['result'], 'wrapper_blocked')


if __name__ == '__main__':
    unittest.main()
