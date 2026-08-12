#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from rfc_engine.solvers.big_implosion import run_big_implosion

PARENT_H = '198816819e027409812de925efe42878f9898d628b8c7a137e92c2d52bc568a6'
PARENT_STATE = 'f04f69ae94e9c4ce0105c835f0ba421377cc47df322d180b0b253cdcc8e5257b'
PARENT_BUNDLE = '58a735dc94366ed57d592bc5535918a477976bf93efbe736dfb39325b19154d4'

def sha(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def save(name,obj):
    (RUN/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def path_laplacian(n):
    L=np.zeros((n,n),dtype=float)
    for i in range(n-1):
        L[i,i]+=1.0; L[i+1,i+1]+=1.0; L[i,i+1]-=1.0; L[i+1,i]-=1.0
    return L

def main():
    cfg=json.loads((RUN/'solver_configs/B_big_implosion.json').read_text())
    primary=json.loads((RUN/'solver_outputs/big_implosion/result.json').read_text())
    model=cfg['model']; delta=float(model['delta']); n=int(model['node_count'])
    x=np.asarray(model['initial_state'],dtype=float).reshape(n,1)
    tol=float(model['tolerance']); margin=float(model['strict_compression_margin'])

    handoff=ROOT/'modules/A/runs/A-100-20260811T115001Z/H_A_to_B.json'
    astate=ROOT/'modules/A/runs/A-100-20260811T115001Z/solver_outputs/triad_kernel/result.json'
    registry=json.loads((ROOT/'memory/ARTIFACT_REGISTRY.json').read_text())
    parent_reg=[r for r in registry['artifacts'] if r.get('run_id')=='A-100-20260811T115001Z']
    exact_parent=(sha(handoff)==PARENT_H and sha(astate)==PARENT_STATE and len(parent_reg)==1 and parent_reg[0]['sha256']==PARENT_BUNDLE)

    L=path_laplacian(n)
    Q=np.linalg.inv(np.eye(n)+L/(delta-1.0))
    y=Q@x; reopened=np.linalg.solve(Q,y)
    ones=np.ones((n,1)); P=np.eye(n)-ones@ones.T/n
    eigL=np.linalg.eigvalsh(L); eigQ=np.linalg.eigvalsh(Q)
    independent={
      'classification':'INDEPENDENT_B_RECONSTRUCTION',
      'laplacian_match':bool(np.array_equal(L,np.asarray(primary['laplacian']))),
      'operator_match':bool(np.allclose(Q,np.asarray(primary['operator']),rtol=0.0,atol=1e-15)),
      'manifested_match':bool(np.allclose(y,np.asarray(primary['manifested_state']),rtol=0.0,atol=1e-15)),
      'reopened_parent_max_abs':float(np.max(np.abs(reopened-x))),
      'constant_mode_residual':float(np.linalg.norm(L@ones)),
      'pregeometry_connected':int(np.sum(eigL>tol))==n-1,
      'operator_spd':bool(np.min(eigQ)>0.0),
      'operator_spectrum_le_one':bool(np.max(eigQ)<=1.0+tol),
      'compression_ratio':float(np.linalg.norm(P@y)/np.linalg.norm(P@x)),
      'total_ledger_change':float(abs(y.sum()-x.sum()))
    }
    independent['pass']=all([independent['laplacian_match'],independent['operator_match'],independent['manifested_match'],independent['pregeometry_connected'],independent['operator_spd'],independent['operator_spectrum_le_one'],independent['compression_ratio']<1.0-margin,independent['reopened_parent_max_abs']<=tol,independent['total_ledger_change']<=tol])

    parent_weights=json.loads(astate.read_text())['normalized_weights']
    prefix=[]; prefix_states={}
    for m in [8,16,24,32,40]:
        mm={'delta':delta,'node_count':m,'weighted_edges':[[i,i+1,1.0] for i in range(m-1)],'initial_state':parent_weights[:m],'pre_event_clock':None,'sector_projection':[[1.0]*m],'tolerance':tol,'strict_compression_margin':margin}
        r=run_big_implosion(mm); prefix_states[m]=np.asarray(r['manifested_state'],dtype=float).reshape(m)
        prefix.append({'N':m,'success':r['success'],'compression_ratio':r['compression_ratio'],'conserved_mode_error':r['conserved_mode_error'],'reopening_error':r['reopening_error'],'total_relative_change':r['total_relative_change'],'pre_event_clock_null':r['pass_flags']['no_pre_event_clock_imported']})
    prefix_pass=all(z['success'] and z['compression_ratio']<1.0-margin and z['conserved_mode_error']<=tol and z['reopening_error']<=tol and z['pre_event_clock_null'] for z in prefix)
    boundary=[float(np.linalg.norm(prefix_states[a][:4]-prefix_states[b][:4])) for a,b in [(8,16),(16,24),(24,32),(32,40)]]
    convergence={'boundary_first4_differences':boundary,'last_difference_below_tolerance':boundary[-1]<=tol,'all_prefix_sizes_pass':prefix_pass}
    convergence['pass']=convergence['last_difference_below_tolerance'] and prefix_pass

    norm_before=float(np.linalg.norm(P@x)); identity_after=norm_before
    compression_ablation={'countermodel':'Q=I','norm_before':norm_before,'norm_after':identity_after,'strict_compression':identity_after<norm_before-margin}
    coupling_model=dict(model); coupling_model['weighted_edges']=[]
    coupling=run_big_implosion(coupling_model)
    coupling_ablation={'countermodel':'L=0','solver_success':coupling['success'],'strict_compression':coupling['pass_flags']['strict_nontrivial_compression'],'compression_ratio':coupling['compression_ratio']}
    ablations={'compression_ablation_rejected':not compression_ablation['strict_compression'],'relational_coupling_ablation_rejected':not coupling_ablation['solver_success'] and not coupling_ablation['strict_compression'],'compression':compression_ablation,'coupling':coupling_ablation}
    ablations['pass']=ablations['compression_ablation_rejected'] and ablations['relational_coupling_ablation_rejected']

    replay=run_big_implosion(model)
    replay_rec={'full_result_equal':replay==primary,'restart_reopened_matches_parent':bool(np.max(np.abs(np.asarray(primary['reopened_state']).reshape(n,1)-x))<=tol)}
    replay_rec['pass']=all(replay_rec.values())

    errs=np.array([[z['conserved_mode_error'],z['reopening_error'],z['total_relative_change']] for z in prefix],dtype=float)
    cov=np.cov(errs,rowvar=False,bias=True)
    covariance={'classification':'INTERNAL_NUMERICAL_ONLY','residual_vectors':errs.tolist(),'covariance':cov.tolist(),'covariance_psd':bool(np.min(np.linalg.eigvalsh((cov+cov.T)/2))>=-1e-30),'max_residual':float(np.max(np.abs(errs))),'public_or_empirical_uncertainty_used':False}
    covariance['pass']=covariance['covariance_psd'] and covariance['max_residual']<=tol

    allowed_keys={'delta','node_count','weighted_edges','initial_state','pre_event_clock','sector_projection','tolerance','strict_compression_margin'}
    no_later=(set(model)==allowed_keys and model.get('pre_event_clock') is None and len(model['sector_projection'])==1 and json.loads((RUN/'SOURCE_REGISTER.json').read_text())['public_data_declaration']=='NONE')
    physical_state={'event_type':'BIG_IMPLOSION','event_order_origin':0,'pre_event_physical_time':None,'carrier_type':'FIRST_PHYSICAL_CARRIER_AMPLITUDE_ON_PREGEOMETRY','pregeometry_nodes':n,'named_later_sectors_assigned':False,'metric_geometry_assumed':False,'particles_assumed':False}

    gates={
      'no_pre_event_physical_time':model.get('pre_event_clock') is None,
      'exact_parent_bytes':exact_parent,
      'strict_nontrivial_compression':bool(primary['pass_flags']['strict_nontrivial_compression'] and primary['compression_ratio']<1.0-margin),
      'total_ledger_preservation':bool(primary['conserved_mode_error']<=tol and primary['total_relative_change']<=tol),
      'no_loss_reopening':bool(primary['reopening_error']<=tol),
      'no_later_physics_smuggled_into_B':no_later,
      'multiple_graph_sizes_and_convergence':convergence['pass'],
      'compression_and_relational_ablations':ablations['pass'],
      'restart_and_replay':replay_rec['pass'],
      'uncertainty_covariance':covariance['pass'],
      'independent_reconstruction':independent['pass']
    }
    overall=all(gates.values())
    out={'run_id':'B-110-20260811T140258Z','classification':'B110_FROZEN_GATE_EXECUTION','overall':'PASS' if overall else 'FAIL','gates':gates,'primary_summary':{'success':primary['success'],'compression_ratio':primary['compression_ratio'],'reopening_error':primary['reopening_error'],'conserved_mode_error':primary['conserved_mode_error'],'total_relative_change':primary['total_relative_change']},'physical_state':physical_state,'prefix_runs':prefix,'convergence':convergence,'ablations':ablations,'replay_restart':replay_rec,'uncertainty_covariance':covariance,'independent_reconstruction':independent,'claim_boundary':'First physical RFC state at MINIMAL_SPINE fidelity; no microscopic or cosmological late-time completion.'}
    save('B110_GATE_EXECUTION.json',out); save('independent_reconstruction.json',independent)
    print(json.dumps({'overall':out['overall'],'gates':gates},indent=2))
    if not overall: raise SystemExit(1)

if __name__=='__main__': main()
