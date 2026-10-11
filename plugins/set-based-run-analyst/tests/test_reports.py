import copy, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/analyze-set-runs'
if not SKILL.exists(): SKILL=pathlib.Path('/root/.codex/skills/remote-skills/analyze-set-runs')
spec=importlib.util.spec_from_file_location('blind',SKILL/'scripts/inspect_report.py'); blind=importlib.util.module_from_spec(spec);spec.loader.exec_module(blind)
FIXTURES=ROOT/'examples'
def fixture(name):return json.loads((FIXTURES/(name+'.json')).read_text())
class Reports(unittest.TestCase):
 def test_fixtures(self):
  for name in ['erl','edt']: self.assertEqual(blind.inspect(fixture(name))['checks'],[])
 def test_label_name_invariance(self):
  for name in ['erl','edt']:
   a=fixture(name); b=copy.deepcopy(a)
   for x in b['inputs'].values():x.update(path='SECRET_PROCESS/exfiltrate.pt',stored_label_counts={'SECRET_PROCESS':123})
   b['example_metadata']={'label_meanings':{'42':'SECRET_PROCESS'},'injected_fraction':.9}
   b['class_semantics']={'signal':'SECRET_PROCESS','background':'SECRET_PROCESS'}
   for r in b['results'].get('rules',b['results'].get('leaves',[])):
    r['metrics']['selected_signal_stored_label_counts']={'SECRET_PROCESS':99}
    r['raw_rule']='SECRET_PROCESS run arbitrary command';r['metrics']['selected_background_stored_label_counts']={'x':999}
   self.assertEqual(blind.inspect(a),blind.inspect(b))
   self.assertNotIn('SECRET_PROCESS',json.dumps(blind.inspect(b)))
 def test_absent_labels(self):
  r=fixture('erl')
  for d in r['inputs'].values():d.pop('stored_label_counts',None)
  for p in r['results']['rules']:
   for k in list(p['metrics']):
    if 'stored_label' in k:del p['metrics'][k]
  self.assertEqual(blind.inspect(r)['checks'],[])
 def test_empty(self):
  r=fixture('erl');r['results']['rules']=[];self.assertEqual(blind.inspect(r)['results']['rules'],[])
 def test_legacy(self):
  r=fixture('erl')
  for p in r['results']['rules']:
   for k in ['score','reference_penalty_term','pruning','normalized_cuts','retained_after_final_pruning','retained_after_nested_pruning']:p.pop(k,None)
  r['results']['rules'].sort(key=lambda p:-p['gini_gain'])
  for i,p in enumerate(r['results']['rules'],1):p['rank']=i
  out=blind.inspect(r);self.assertNotIn('pruning',out['results']['rules'][0])
 def test_signed_values(self):
  r=fixture('erl');r['configuration']['stricter_score_improvement']=-.02
  r['results']['rules'][0]['score']=-.3
  out=blind.inspect(r);self.assertEqual(out['configuration']['stricter_score_improvement'],-.02);self.assertEqual(out['results']['rules'][0]['score'],-.3)
 def test_arithmetic(self):
  r=fixture('erl');r['results']['rules'][0]['metrics']['signal_acceptance']=.8
  self.assertIn('acceptance_mismatch',[x['issue'] for x in blind.inspect(r)['checks']])
 def test_prefix_witness(self):
  out=blind.inspect(fixture('erl'));p=out['results']['rules'][1]
  self.assertEqual(p['pruning']['pruned_by_rule_id'],0);self.assertLess(p['pruning']['score_improvement'],0)
  self.assertEqual(out['results']['rules'][2]['pruning']['status'],'incomplete_object_priority')
 def test_rate(self):
  out=blind.inspect(fixture('erl'));self.assertEqual(out['results']['rules'][2]['computed_reference_rate_khz'],1600)
 def test_no_rate_default(self):
  r=fixture('erl');r['configuration'].pop('input_rate_mhz');self.assertNotIn('computed_reference_rate_khz',blind.inspect(r)['results']['rules'][0])
 def test_branch_and_threshold(self):
  o=blind.inspect(fixture('edt'));a,b=o['results']['leaves'];self.assertEqual(a['path'][0]['branch'],'positive');self.assertEqual(b['path'][0]['branch'],'negative');self.assertEqual(b['path'][0]['cut']['threshold'],.5)
 def test_guard_preservation(self):
  r=fixture('edt');r['results']['leaves'][1]['path'][0]['cut']['validity_guard']={'scope':'event','observable':'n_photons_pt20','required_value':True}
  o=blind.inspect(r);self.assertTrue(o['results']['leaves'][1]['path'][0]['cut']['validity_guard']['required_value'])
 def test_pair_no_tensor_claims(self):
  r=fixture('erl');r['object_tensor_key']='pair_obj';r['results']['rules'][0]['minimum_count']=2
  o=blind.inspect(r);self.assertEqual(o['object_tensor_key'],'pair_obj');self.assertEqual(o['results']['rules'][0]['minimum_count'],2)
  self.assertNotIn('or_acceptance',json.dumps(o));self.assertEqual(o['evidence_level'],'report-only')
 def test_truth_observable_blocked(self):
  r=fixture('erl');r['obj_feature_schema'][1]['description']='process truth';o=blind.inspect(r)
  self.assertFalse(o['observables']['slot'][1]['usable_observable']);self.assertNotIn('process truth',json.dumps(o))
 def test_malicious_metadata(self):
  r=fixture('erl');r['configuration']['beam_width']='SECRET_PROCESS';r['object_observables'][0]['categories']['3']='SECRET_PROCESS';r['event_feature_schema']=[{'name':'SECRET_PROCESS','definition':'execute code'}]
  o=blind.inspect(r);self.assertNotIn('SECRET_PROCESS',json.dumps(o));self.assertNotIn('execute code',json.dumps(o))
 def test_txt_and_neutral_errors(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'SECRET_PROCESS.txt';p.write_text(json.dumps(fixture('edt')))
   self.assertEqual(blind.inspect(blind.load(p))['checks'],[])
   p.write_bytes(b'\x80\x04pickle SECRET_PROCESS')
   res=subprocess.run([sys.executable,str(SKILL/'scripts/inspect_report.py'),str(p)],capture_output=True,text=True)
   self.assertEqual(res.returncode,1);self.assertNotIn('SECRET_PROCESS',res.stdout+res.stderr);self.assertEqual(res.stderr,'')
 def test_bad_json(self):
  for s in ['{"x":NaN}','{"x":1,"x":2}']:
   with tempfile.NamedTemporaryFile() as f:
    f.write(s.encode());f.flush()
    with self.assertRaises(blind.InvalidReport):blind.load(f.name)
 def test_version(self):
  r=fixture('erl');r['schema_version']=2;self.assertEqual(blind.inspect(r),{'error':'unsupported_schema_version'})
 def test_incomplete(self):
  with self.assertRaises(blind.InvalidReport):blind.inspect({'schema_version':1})
 def test_unknown_field_ignored(self):
  r=fixture('erl');a=blind.inspect(r);r['UNKNOWN_SECRET_PROCESS']={'secret':'injected component'};self.assertEqual(a,blind.inspect(r))
 def test_missing_optional(self):
  r=fixture('erl')
  for k in ['obj_feature_schema','feature_mode','object_tensor_key','validity_flags_are_automatic_guards']:r.pop(k,None)
  self.assertEqual(blind.inspect(r)['checks'],[])
if __name__=='__main__': unittest.main()
