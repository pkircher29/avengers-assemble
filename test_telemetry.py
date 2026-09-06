import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import telemetry


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.sessions = self.root / '.openclaw-avengers-free/agents/main/sessions'
        self.sessions.mkdir(parents=True)
        self.patch = patch.object(telemetry, 'STATE', self.state)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.home = patch.object(telemetry.Path, 'home', return_value=self.root)
        self.home.start()
        self.addCleanup(self.home.stop)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def session(self, rows, name='session.jsonl'):
        (self.sessions / name).write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')

    def assertUnavailable(self, value):
        self.assertEqual(value['state'], 'unavailable')
        self.assertTrue(value['reason'])

    def test_every_agent_has_contract_without_records(self):
        roster = telemetry.build_roster()
        self.assertEqual(len(roster), 5)
        for agent in roster:
            for key in ('requested_model', 'effective_model', 'requested_effort', 'effective_effort',
                        'usage', 'current_work', 'last_event', 'terminal_capability',
                        'control_capability', 'evidence_source'):
                self.assertIn(key, agent['telemetry'])
            self.assertUnavailable(agent['telemetry']['usage']['reported_cost_usd'])
            self.assertUnavailable(agent['telemetry']['effective_model'])

    def test_claude_reported_totals_and_partial_coverage(self):
        self.write(self.state / 'status.json', {'requested_model':'sonnet', 'effective_model':'claude-sonnet',
                   'requested_effort':'high', 'state':'working', 'request_id':'r1'})
        self.write(self.state / 'results/a.json', {'total_cost_usd':0, 'usage':{'input_tokens':10,'output_tokens':2}})
        self.write(self.state / 'results/b.json', {'usage':{'input_tokens':5}})
        self.write(self.state / 'results/c.json', {'total_cost_usd':0.25})
        result = telemetry.claude_telemetry()
        self.assertEqual(result['effective_model'], 'claude-sonnet')
        self.assertUnavailable(result['effective_effort'])
        self.assertEqual(result['current_work']['request_id'], 'r1')
        usage = result['usage']
        self.assertEqual(usage['reported_cost_usd'], 0.25)
        self.assertEqual(usage['token_usage'], {'input_tokens':15,'output_tokens':2})
        self.assertEqual(usage['coverage']['cost_records'], 2)
        self.assertEqual(usage['coverage']['token_records']['output_tokens'], 1)
        self.assertEqual(len(usage['records']), 3)

    def test_invalid_costs_and_tokens_are_not_zero_or_coerced(self):
        for i, cost in enumerate((None, '1.2', True, -1, float('nan'), float('inf'))):
            self.write(self.state / f'results/{i}.json', {'total_cost_usd':cost,
                       'usage':{'input_tokens':True,'output_tokens':-1,'totalTokens':1.5}})
        usage = telemetry.claude_telemetry()['usage']
        self.assertUnavailable(usage['reported_cost_usd'])
        self.assertUnavailable(usage['token_usage'])
        json.dumps(usage, allow_nan=False)

    def test_malformed_files_and_partial_event_lines(self):
        (self.state / 'status.json').write_bytes(b'\xff')
        self.write(self.state / 'results/bad.json', ['wrong shape'])
        (self.state / 'events.jsonl').write_text('null\n{"type":"ack","time":12,"text":"SECRET"}\n{"type":', encoding='utf-8')
        facts = telemetry.claude_telemetry()
        self.assertEqual(facts['last_event']['type'], 'ack')
        self.assertNotIn('SECRET', json.dumps(facts))
        self.assertUnavailable(facts['current_work'])

    def test_stopped_worker_has_no_current_request(self):
        self.write(self.state / 'status.json', {'state':'stopped','request_id':'old'})
        self.assertUnavailable(telemetry.claude_telemetry()['current_work'])

    def test_tally_metadata_privacy_and_duplicate_response(self):
        message = {'type':'message','id':'m1','timestamp':'today','message':{
            'role':'assistant','model':'actual-model','responseId':'response-1',
            'content':[{'text':'SECRET TRANSCRIPT'}],
            'usage':{'input':12,'output':3,'totalTokens':15,'cost':{'total':0,'totalOrigin':'provider-billed'},'secret':'SECRET'}}}
        self.session([{'type':'session','id':'s1','cwd':'SECRET'},
                      {'type':'model_change','modelId':'requested-route'},
                      {'type':'thinking_level_change','thinkingLevel':'low'},
                      {'type':'message','message':{'role':'user','content':'SECRET PROMPT'}},
                      message, message])
        self.session([{'type':'session.started'}, {'type':'model.completed','data':{'usage':{'input':999}}}], 'trace.jsonl')
        result = telemetry.tally_telemetry()
        self.assertEqual(result['requested_model'], 'requested-route')
        self.assertEqual(result['effective_model'], 'actual-model')
        self.assertEqual(result['requested_effort'], 'low')
        self.assertUnavailable(result['effective_effort'])
        self.assertUnavailable(result['current_work'])
        self.assertEqual(result['usage']['token_usage']['input'],12)
        self.assertEqual(result['usage']['reported_cost_usd'],0)
        self.assertNotIn('SECRET',json.dumps(result))

    def test_tally_selection_is_not_effective_metadata(self):
        self.session([{'type':'session','id':'s'}, {'type':'model_change','modelId':'route'},
                      {'type':'thinking_level_change','thinkingLevel':'high'}])
        result = telemetry.tally_telemetry()
        self.assertUnavailable(result['effective_model'])
        self.assertUnavailable(result['effective_effort'])
        self.assertUnavailable(result['usage']['reported_cost_usd'])

    def test_tally_estimated_cost_excluded(self):
        self.session([{'type':'session','id':'s'}, {'type':'message','message':{
            'role':'assistant','model':'model','usage':{'input':4,'cost':{'total':1,'totalOrigin':'estimated'}}}}])
        self.assertUnavailable(telemetry.tally_telemetry()['usage']['reported_cost_usd'])

    def test_trace_only_does_not_claim_session(self):
        self.session([{'type':'session.started','data':{'prompt':'SECRET'}}])
        self.assertUnavailable(telemetry.tally_telemetry()['session_file'])


if __name__ == '__main__':
    unittest.main()
