#!/usr/bin/env python3
"""Read-only blind JSON ingestion. Never import report code or load tensor/pickle files."""
import json, math, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
REVISION = '90ae91001090110a3689688bfde6140584ede102'
MAX_BYTES = 16 * 1024 * 1024
class InvalidReport(Exception): pass

def reject(*_): raise InvalidReport()
def number(v): return type(v) in (int, float) and math.isfinite(v)
def close(a,b): return number(a) and number(b) and math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-9)
def pairs(items):
    d={}
    for k,v in items:
        if k in d: reject()
        d[k]=v
    return d

def load(path):
    # Suffix-independent JSON; bounded reads; no pickle or tensor loading fallback.
    with open(path,'rb') as f: data=f.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES: reject()
    return json.loads(data,parse_constant=reject,object_pairs_hook=pairs)

def validate_schema(value,schema,root):
    """Subset of Draft 2020-12 used by the bundled upstream schema; no remote refs."""
    if '$ref' in schema:
        s=root
        for part in schema['$ref'].split('/')[1:]: s=s[part]
        return validate_schema(value,s,root)
    kinds={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),
           'string':lambda x:isinstance(x,str),'null':lambda x:x is None,
           'boolean':lambda x:type(x) is bool,'number':number,
           'integer':lambda x:type(x) is int}
    if 'type' in schema:
        ts=schema['type']; ts=[ts] if isinstance(ts,str) else ts
        if not any(kinds[t](value) for t in ts): reject()
    if 'const' in schema and (value!=schema['const'] or type(value)!=type(schema['const'])): reject()
    if 'enum' in schema and value not in schema['enum']: reject()
    if number(value):
        if 'minimum' in schema and value<schema['minimum']: reject()
        if 'maximum' in schema and value>schema['maximum']: reject()
    if isinstance(value,dict):
        if any(k not in value for k in schema.get('required',[])): reject()
        for k,v in value.items():
            if k in schema.get('properties',{}): validate_schema(v,schema['properties'][k],root)
            elif isinstance(schema.get('additionalProperties'),dict): validate_schema(v,schema['additionalProperties'],root)
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',100000): reject()
        for v in value: validate_schema(v,schema.get('items',{}),root)
    for s in schema.get('allOf',[]): validate_schema(value,s,root)
    if 'if' in schema:
        try: validate_schema(value,schema['if'],root)
        except InvalidReport: pass
        else: validate_schema(value,schema.get('then',{}),root)
    if 'oneOf' in schema:
        count=0
        for s in schema['oneOf']:
            try: validate_schema(value,s,root); count+=1
            except InvalidReport: pass
        if count!=1: reject()

def blind_schema():
    s=json.loads((ROOT/'references/report-schema.json').read_text())
    # Truth fields and free text are never required for analysis or validated.
    dropped={'stored_label_counts','selected_signal_stored_label_counts',
             'selected_background_stored_label_counts','class_semantics','raw_text',
             'display_text','raw_rule','simplified_rule','display','selected_condition',
             'path','created_utc'}
    def walk(x):
        if not isinstance(x,dict): return
        x['required']=[k for k in x.get('required',[]) if k not in dropped]
        for k in list(x.get('properties',{})):
            if k in dropped and not (k=='path' and x is s['$defs']['leaf']): del x['properties'][k]
        for v in x.values():
            if isinstance(v,dict):
                for w in v.values(): walk(w)
            elif isinstance(v,list):
                for w in v: walk(w)
    walk(s)
    if 'path' not in s['$defs']['leaf']['required']: s['$defs']['leaf']['required'].append('path')
    return s

CONFIG_NUM = set('reference_penalty stricter_score_improvement input_rate_mhz max_trigger_rate_khz max_reference_acceptance max_rule_depth beam_width max_candidate_rules max_thresholds minimum_count min_signal_efficiency beam_signal_similarity_threshold beam_background_similarity_threshold final_signal_similarity_threshold final_background_similarity_threshold max_depth min_samples_leaf decision_threshold signal_similarity_threshold background_similarity_threshold'.split())
CONFIG_BOOL=set('require_complete_priority object_features_enabled event_features_enabled beam_similarity_filter final_similarity_pruning penalty_applied_during_search pair_tensor basic_object_features allow_validity_cuts progress'.split())
ENUM={
 'scope':{'event','slot'},'branch':{'positive','negative'},
 'kind':{'continuous','ordinal','categorical','boolean'},
 'observable_kind':{'continuous','ordinal','categorical','boolean'},
 'cut_type':{'threshold','category'},'comparison':{'>','>=','<','<='},
 'status':{'retained','incomplete_object_priority','reference_rate_limit','equivalent_rule','stricter_score_improvement','similarity'},
 'direction':{'mixture-enriched','reference-enriched','equal-acceptance'},
 'feature_mode':{'event_only','object_only','combined'},'object_tensor_key':{'obj','pair_obj'},
 'scoring_function':{'gini_gain_minus_reference_acceptance_penalty','weighted_gini_gain_of_rule_vs_complement'},
 'gain_function':{'gini_gain'},
}
NUM=set('rank rule_id leaf_id depth effective_depth_after_simplification minimum_count score gini_gain reference_penalty_term pruned_rank estimated_reference_rate_khz leaf_signal_fraction predicted_class_at_default_threshold source_node_id source_split_gain prefix_gini_gain prefix_score prefix_reference_penalty_term prefix_signal_accepted prefix_background_accepted prefix_signal_acceptance prefix_reference_acceptance pruned_by_rule_id retained_witness_rule_id score_gap score_improvement threshold signal_accepted signal_total background_accepted background_total signal_acceptance background_acceptance acceptance_difference acceptance_ratio mixture_label_purity'.split())
BOOL=set('logical_pruning_applicable object_cut_priority_complete retained_after_final_pruning retained_after_nested_pruning retained_after_similarity_pruning passes_reference_rate_limit required_value'.split())

def inspect(raw):
    if not isinstance(raw,dict): reject()
    if raw.get('schema_version')!=1: return {'error':'unsupported_schema_version'}
    schema=blind_schema(); validate_schema(raw,schema,schema)
    catalog=json.loads((ROOT/'references/feature-catalog.json').read_text())
    catalog={x['name']:x for group in catalog.values() for x in group}
    aliases={}; blocked=set(); notes=[]
    metadata={}
    for key in ['event_feature_schema','obj_feature_schema','pair_obj_feature_schema']:
        for item in raw.get(key) or []:
            n=item.get('name'); metadata[n]=item
            if re.search(r'\b(truth|generator|process|label|injected)\b',json.dumps(item),re.I): blocked.add(n)
    observables=raw['object_observables']+raw['event_observables']
    for i,item in enumerate(observables):
        n=item['name']; aliases[n]=n if n in catalog and n not in blocked else f'feature_{i+1}'
    def feature(n): return aliases.get(n,'unknown_feature')
    def priorities(values):
        out=[]
        for v in values:
            name,sep,direction=v.partition(':')
            out.append(feature(name)+(sep+direction if direction in ENUM['comparison'] else ''))
        return out
    def project(d):
        out={}
        for k,v in d.items():
            key='training_class_purity' if k=='mixture_label_purity' else k
            if k in NUM and (v is None or number(v)): out[key]=v
            elif k in BOOL and type(v) is bool: out[k]=v
            elif k in ENUM: out[k]=v if isinstance(v,str) and v in ENUM[k] else 'unknown'
            elif k=='observable': out[k]=feature(v); out['usable_observable']=v in catalog and v not in blocked
            elif k=='accepted_codes' and isinstance(v,list): out[k]=[x for x in v if type(x) is int]
            elif k in ('metrics','cut','validity_guard','pruning') and isinstance(v,dict): out[k]=project(v)
            elif k in ('steps','path','normalized_cuts') and isinstance(v,list): out[k]=[project(x) for x in v]
            elif k=='object_cut_priority_remaining': out[k]=priorities(v)
        return out
    config={}
    vocabulary=json.loads((ROOT/'references/config-vocabulary.json').read_text())
    for k,v in raw['configuration'].items():
        if k in CONFIG_NUM and (v is None or number(v)): config[k]=v
        elif k in CONFIG_BOOL and type(v) is bool: config[k]=v
        elif k in ENUM and isinstance(v,str): config[k]=v if v in ENUM[k] else 'unknown'
        elif k=='object_cut_priority' and isinstance(v,list): config[k]=priorities(v)
        elif k in vocabulary and v in vocabulary[k]: config[k]=v
    fam='rules' if 'rules' in raw['results'] else 'leaves'
    out={'format':'blind_set_run_v1','report_id':'run_A','evidence_level':'report-only',
         'retrieved_code_revision':REVISION,'run_code_revision':'unknown',
         'model_family':'ERL' if fam=='rules' else 'EDT','configuration':config,'inputs':{},
         'observables':{},'results':{fam:[project(x) for x in raw['results'][fam]]},
         'limitations':['No tensor evaluation, overlap, combined ERL acceptance, or independent validation.',
                       'Unknown fields and free text withheld; no historical defaults inferred.'],
         'checks':notes}
    out['model_variant']=raw['model'] if raw['model'] in {'EDT','ERL_Gini','ERL_Gini_nested','ERL_Gini_penalized','ERL_Gini_nested_flexible'} else 'unknown'
    for k in ('feature_mode','object_tensor_key'):
        if k in raw: out[k]=raw[k] if raw[k] in ENUM[k] else 'unknown'
    for k in ('validity_flags_are_automatic_guards','validity_flags_are_guard_only','native_event_only'):
        if type(raw.get(k)) is bool: out[k]=raw[k]
    for source,alias in [('signal','mixture_A'),('background','reference_A')]:
        d=raw['inputs'][source]
        out['inputs'][alias]={k:d[k] for k in ('event_count','object_shape','event_feature_shape') if k in d}
    for scope,key in [('slot','object_observables'),('event','event_observables')]:
        out['observables'][scope]=[]
        for item in raw[key]:
            n=item['name']; entry={'name':feature(n),'kind':item['kind'],'usable_observable':n in catalog and n not in blocked}
            if item.get('validity_column') is not None: entry['validity_column']=feature(item['validity_column'])
            # Copy only metadata equal to vetted physical values. Never fill absent metadata.
            meta=metadata.get(n,{})
            for k in ('units','definition','applicable_types','required_columns','raw_columns'):
                if n not in blocked and k in meta and meta[k]==catalog.get(n,{}).get(k): entry[k]=meta[k]
            cats=item.get('categories')
            if isinstance(cats,dict):
                entry['categories']={str(k):v if v in {'jet','jets','muon','muons','electron','electrons','photon','photons','false','true','False','True'} else 'category_withheld' for k,v in cats.items() if re.fullmatch(r'-?\d+',str(k))}
            out['observables'][scope].append(entry)
    records=out['results'][fam]
    summary_keys=set('candidate_rule_count pruned_rule_count mixture_enriched_rule_count reference_enriched_rule_count equivalent_rules_removed rate_rules_removed stricter_rules_removed incomplete_priority_rules_removed similarity_rules_removed node_count leaf_count logical_pruning_applicable_rule_count'.split())
    out['summary']={k:v for k,v in raw['summary'].items() if k in summary_keys and type(v) is int and v>=0}
    def check(ok,where,code):
        if not ok: notes.append({'field':where,'issue':code})
    def metrics(m,where):
        for role,alias in [('signal','mixture_A'),('background','reference_A')]:
            a,t=m[role+'_accepted'],m[role+'_total']
            check(a<=t,where,'accepted_exceeds_total')
            check(t==out['inputs'][alias]['event_count'],where,'input_total_mismatch')
            if t: check(close(m[role+'_acceptance'],a/t),where,'acceptance_mismatch')
        a,b=m['signal_accepted'],m['background_accepted']; x,y=m['signal_acceptance'],m['background_acceptance']
        check(close(m['training_class_purity'],a/(a+b) if a+b else 0),where,'purity_mismatch')
        check(close(m['acceptance_difference'],x-y),where,'difference_mismatch')
        check(m['acceptance_ratio'] is None if y==0 else close(m['acceptance_ratio'],x/y),where,'ratio_mismatch')
        check(m['direction']==('mixture-enriched' if x>y else 'reference-enriched' if x<y else 'equal-acceptance'),where,'direction_mismatch')
    ids=[r.get('rule_id',r.get('leaf_id')) for r in records]
    check(len(ids)==len(set(ids)),'results','duplicate_ids')
    check([r['rank'] for r in records]==list(range(1,len(records)+1)),'results','rank_sequence')
    byid=dict(zip(ids,records))
    for i,r in enumerate(records):
        where=f'results.{fam}[{i}]'; m=r['metrics']; metrics(m,where+'.metrics')
        if fam=='rules':
            if 'score' in r and 'reference_penalty_term' in r: check(close(r['score'],r['gini_gain']-r['reference_penalty_term']),where,'score_mismatch')
            if 'reference_penalty_term' in r and 'reference_penalty' in config: check(close(r['reference_penalty_term'],config['reference_penalty']*m['background_acceptance']),where,'penalty_mismatch')
            if 'input_rate_mhz' in config and config['input_rate_mhz'] is not None:
                rate=m['background_acceptance']*config['input_rate_mhz']*1000
                r['computed_reference_rate_khz']=rate
                if 'estimated_reference_rate_khz' in r: check(close(r['estimated_reference_rate_khz'],rate),where,'rate_mismatch')
            ceiling=config.get('max_reference_acceptance')
            if 'max_reference_acceptance' in config and 'passes_reference_rate_limit' in r:
                check(r['passes_reference_rate_limit']==(ceiling is None or m['background_acceptance']<=ceiling),where,'rate_flag_mismatch')
            last=(m['signal_total'],m['background_total'])
            for j,s in enumerate(r['steps']):
                cur=(s['prefix_signal_accepted'],s['prefix_background_accepted'])
                check(all(a<=b for a,b in zip(cur,last)),where+f'.steps[{j}]','prefix_counts_increase'); last=cur
                for a,t,key in zip(cur,(m['signal_total'],m['background_total']),('prefix_signal_acceptance','prefix_reference_acceptance')):
                    if t: check(close(s[key],a/t),where,'prefix_acceptance_mismatch')
                if 'prefix_score' in s and 'prefix_reference_penalty_term' in s: check(close(s['prefix_score'],s['prefix_gini_gain']-s['prefix_reference_penalty_term']),where,'prefix_score_mismatch')
                if 'prefix_reference_penalty_term' in s and number(config.get('reference_penalty')): check(close(s['prefix_reference_penalty_term'],config['reference_penalty']*s['prefix_reference_acceptance']),where,'prefix_penalty_mismatch')
            if r['steps']: check(last==(m['signal_accepted'],m['background_accepted']),where,'final_prefix_mismatch')
            if 'object_cut_priority' in config:
                priority=config['object_cut_priority'];position=0
                for step in r['steps']:
                    cut=step['cut']
                    if cut['scope']=='slot' and position<len(priority):
                        name,_,direction=priority[position].partition(':')
                        if cut['observable']==name and (not direction or cut.get('comparison')==direction): position+=1
                if 'object_cut_priority_complete' in r: check(r['object_cut_priority_complete']==(position==len(priority)),where,'priority_completion_mismatch')
                if 'object_cut_priority_remaining' in r: check(r['object_cut_priority_remaining']==priority[position:],where,'priority_remaining_mismatch')
            audit=r.get('pruning',{}); witness=audit.get('pruned_by_rule_id')
            if 'retained_after_final_pruning' in r and audit.get('status') not in (None,'unknown'):
                check(r['retained_after_final_pruning']==(audit['status']=='retained'),where,'retention_status_mismatch')
            if witness is not None:
                check(witness in byid,where,'missing_witness')
                if witness in byid:
                    w=byid[witness]; gap=w.get('score',w['gini_gain'])-r.get('score',r['gini_gain'])
                    if audit.get('score_gap') is not None: check(close(audit['score_gap'],gap),where,'witness_gap_mismatch')
                    if audit.get('score_improvement') is not None: check(close(audit['score_improvement'],-gap),where,'improvement_mismatch')
                    threshold=config.get('stricter_score_improvement')
                    if audit.get('status')=='stricter_score_improvement' and number(threshold):
                        check(-gap<threshold or math.isclose(-gap,threshold,rel_tol=1e-12,abs_tol=1e-12),where,'logical_threshold_mismatch')
            for k in ('retained_witness_rule_id',):
                if audit.get(k) is not None: check(audit[k] in byid,where,'missing_retained_witness')
        elif r.get('leaf_signal_fraction') is not None:
            check(close(r['leaf_signal_fraction'],m['training_class_purity']),where,'leaf_fraction_mismatch')
            if number(config.get('decision_threshold')): check(r['predicted_class_at_default_threshold']==int(r['leaf_signal_fraction']>=config['decision_threshold']),where,'default_prediction_mismatch')
    if fam=='leaves':
        for role,alias in [('signal','mixture_A'),('background','reference_A')]:
            check(sum(r['metrics'][role+'_accepted'] for r in records)==out['inputs'][alias]['event_count'],'results.leaves','partition_mismatch')
        out['default_selection_counts']={role:sum(r['metrics'][role+'_accepted'] for r in records if r['predicted_class_at_default_threshold']==1) for role in ('signal','background')}
        if isinstance(raw['summary'].get('default_prediction'),dict):
            saved=project(raw['summary']['default_prediction'])
            try:
                metrics(saved,'summary.default_prediction')
                for role in ('signal','background'): check(saved[role+'_accepted']==out['default_selection_counts'][role],'summary.default_prediction','default_union_mismatch')
            except (KeyError,TypeError): notes.append({'field':'summary.default_prediction','issue':'incomplete_metrics'})
    else:
        scores=[r.get('score',r['gini_gain']) for r in records]
        check(all(a>=b-1e-12 for a,b in zip(scores,scores[1:])),'results.rules','score_order')
        retained=[r for r in records if r.get('retained_after_final_pruning',r.get('retained_after_similarity_pruning',False))]
        check([r.get('pruned_rank') for r in retained]==list(range(1,len(retained)+1)),'results.rules','retained_rank_sequence')
    return out

def main():
    # Generic errors never include the input filename, values, or exception strings.
    try:
        if len(sys.argv) not in (2,4): reject()
        offset=0;limit=None
        if len(sys.argv)==4: offset=int(sys.argv[2]);limit=int(sys.argv[3]); assert offset>=0 and 1<=limit<=100
        out=inspect(load(sys.argv[1]))
        if limit is not None and 'results' in out:
            fam=next(iter(out['results']));rs=out['results'][fam];out['results'][fam]=rs[offset:offset+limit]
            out['pagination']={'offset':offset,'total':len(rs),'next_offset':offset+limit if offset+limit<len(rs) else None}
        print(json.dumps(out,allow_nan=False,indent=2))
        return 1 if 'error' in out else 0
    except Exception:
        print('{"error":"invalid_or_inaccessible_report","detail":"Expected bounded version-1 JSON; no raw error text is exposed."}')
        return 1
if __name__=='__main__': sys.exit(main())
