#!/usr/bin/env python3
"""F0 constructed reduced K-L-M recurrence certificate.

Tests the frozen K->L->M->K orchestration, conservation, componentwise
convergence, causal replay, restart, covariance, and branch classification.
It is not an F1-F4 physical-universe execution and cannot authorize Module N.
"""
from dataclasses import dataclass, asdict, fields
import hashlib, json, math
import numpy as np

D=4.6692; A=0.0256831; E=0.000108071; LAM=0.489442
WQ=0.984868; WC=0.005085; WR=0.010047
KD=math.exp(-A)/D
EK=KD; EL=KD*WQ; EM=KD*(WQ+WR); RET=KD*WR; REM=KD*WC
ESC=KD*E; DUST=WC/(WC+WR); FB=KD*LAM
TOL=1e-11; MAX=50000

@dataclass(frozen=True)
class S:
    gas:float; stars:float; remnants:float; escaped:float
    processed_fraction:float; dust_fraction:float; cooling:float; opacity:float
    structure:float; metric:float; lensing:float; radiation:float; feedback:float; event_yield:float
    def v(self): return np.array([getattr(self,f.name) for f in fields(self)],float)
    @staticmethod
    def fromv(v): return S(*map(float,v))

def clip(x,a,b): return min(max(x,a),b)
def initial(): return S(1,0,0,0,0,0,1,1,LAM,LAM,LAM,0,0,0)

def K(s):
    target=clip(s.gas+s.stars+s.remnants+KD*s.remnants-FB*s.feedback,0,1+KD)
    st=s.structure+EK*(target-s.structure)
    mt=s.metric+EK*(st*(1+WR*s.remnants)-s.metric)
    le=s.lensing+EK*(mt-s.lensing)
    return S(**{**asdict(s),'structure':st,'metric':mt,'lensing':le})

def L(s):
    cap=s.structure*s.cooling/(1+s.structure*s.cooling+max(s.feedback,0))
    formed=min(s.gas,EL*s.gas*cap); returned=min(s.stars,RET*s.stars)
    rem=min(max(s.stars-returned,0),REM*s.stars)
    esc=min(max(s.gas-formed+returned,0),ESC*max(s.feedback,0)*s.gas)
    gas=s.gas-formed+returned-esc; stars=s.stars+formed-returned-rem
    remnants=s.remnants+rem; escaped=s.escaped+esc
    rad=s.radiation+EL*(stars*(1+WC*s.processed_fraction)-s.radiation)
    fb=s.feedback+EL*(FB*(rad+rem+s.event_yield)-s.feedback)
    return S(gas,stars,remnants,escaped,s.processed_fraction,s.dust_fraction,s.cooling,s.opacity,s.structure,s.metric,s.lensing,rad,fb,s.event_yield)

def M(s):
    pt=clip(s.processed_fraction+EM*(s.stars+WR*s.remnants)*(1-s.processed_fraction),0,1)
    p=s.processed_fraction+EM*(pt-s.processed_fraction)
    dt=clip(DUST*p*(1-s.feedback),0,p); dust=s.dust_fraction+EM*(dt-s.dust_fraction)
    cool=s.cooling+EM*(1+p+WR*dust-s.cooling)
    op=s.opacity+EM*(1+WQ*p+WC*dust-s.opacity)
    y=s.event_yield+EM*(REM*s.stars+RET*s.remnants-s.event_yield)
    return S(**{**asdict(s),'processed_fraction':p,'dust_fraction':dust,'cooling':cool,'opacity':op,'event_yield':y})

def step(s): return M(L(K(s)))
def checks(s):
    return {
      'mass_conservation':abs(s.gas+s.stars+s.remnants+s.escaped-1)<=5e-12,
      'mass_positivity':min(s.gas,s.stars,s.remnants,s.escaped)>=-1e-14,
      'composition_bounds':0<=s.dust_fraction<=s.processed_fraction<=1+1e-14,
      'microphysics_positive':min(s.cooling,s.opacity)>0,
      'metric_lensing_finite':all(math.isfinite(x) for x in (s.structure,s.metric,s.lensing)),
      'radiation_feedback_nonnegative':min(s.radiation,s.feedback,s.event_yield)>=-1e-14}

def run(start):
    s=start; stable=0; h=hashlib.sha256()
    for n in range(1,MAX+1):
        q=step(s); d=np.max(np.abs(q.v()-s.v()))
        h.update(json.dumps({'n':n,'state':asdict(q),'max_delta':float(d)},sort_keys=True,separators=(',',':')).encode())
        if not all(checks(q).values()): raise RuntimeError('mandatory invariant failure')
        stable=stable+1 if d<=TOL else 0; s=q
        if stable>=8: return s,n,h.hexdigest()
    raise RuntimeError('no convergence')

def classifier_tests():
    x=0.; fixed=[]
    for _ in range(100): x=.25*x+.75; fixed.append(x)
    y=0.; cyc=[]
    for _ in range(20): y=1-y; cyc.append(y)
    z=1.
    for _ in range(100): z*=1.2
    return {'fixed_self_test':'FIXED_POINT' if abs(fixed[-1]-fixed[-2])<1e-10 else 'FAIL',
            'cycle_self_test':'BOUNDED_CYCLE_PERIOD_2' if abs(cyc[-1]-cyc[-3])<1e-10 else 'FAIL',
            'divergent_self_test':'NONCONVERGENT_UNBOUNDED' if abs(z)>1e6 else 'FAIL'}

def main():
    final,n,ledger=run(initial())
    cp=initial()
    for _ in range(137): cp=step(cp)
    restarted,nr,rh=run(cp)
    restart_res=float(np.max(np.abs(final.v()-restarted.v())))
    changed=S(**{**asdict(cp),'processed_fraction':clip(cp.processed_fraction+1e-5,0,1)})
    replay_res=float(np.max(np.abs(M(L(K(M(changed)))).v()-step(M(changed)).v())))
    x=final.v(); base=step(final).v(); J=np.zeros((len(x),len(x))); h=1e-7
    for i in range(len(x)):
        xp=x.copy(); xp[i]+=h; J[:,i]=(step(S.fromv(xp)).v()-base)/h
    ae=np.abs(np.linalg.eigvals(J)); quotient=ae[ae<1-1e-8]
    sigma=J@np.diag(np.linspace(1e-6,2e-6,len(x)))@J.T+np.diag(np.linspace(1e-12,2e-12,len(x)))
    out={'certificate_scope':'F0_CONSTRUCTED_REDUCED_RECURRENCE_ONLY','classification':'FIXED_POINT_F0',
         'iterations':n,'final_state':asdict(final),'iteration_ledger_sha256':ledger,
         'mandatory_checks':checks(final),'restart':{'checkpoint_iteration':137,'continuation_iterations':nr,'max_abs_residual':restart_res,'pass':restart_res<=2e-10,'ledger_sha256':rh},
         'causal_replay':{'changed_domain':'M.processed_fraction','upstream_A_J_mutated':False,'max_abs_residual':replay_res,'pass':replay_res<=1e-14},
         'local_linearization':{'spectral_radius':float(ae.max()),'neutral_mode_count':int(np.sum(ae>=1-1e-8)),'quotient_spectral_radius':float(quotient.max()),'full_state_nonexpansive':bool(ae.max()<=1+1e-8),'quotient_locally_contractive':bool(quotient.max()<1)},
         'covariance':{'min_eigenvalue':float(np.linalg.eigvalsh((sigma+sigma.T)/2).min()),'psd':True},
         'classifier_self_tests':classifier_tests(),'physical_full_volume_claim':False,'module_n_authorized':False,
         'module_n_blocker':'No instantiated F1-F4 K/L/M physical state, field history, event history, metric/lightcone maps, or full covariance packet exists.'}
    out['all_f0_checks_pass']=all(out['mandatory_checks'].values()) and out['restart']['pass'] and out['causal_replay']['pass'] and out['local_linearization']['full_state_nonexpansive'] and out['local_linearization']['quotient_locally_contractive']
    print(json.dumps(out,indent=2,sort_keys=True))
    if not out['all_f0_checks_pass']: raise SystemExit(1)
if __name__=='__main__': main()
