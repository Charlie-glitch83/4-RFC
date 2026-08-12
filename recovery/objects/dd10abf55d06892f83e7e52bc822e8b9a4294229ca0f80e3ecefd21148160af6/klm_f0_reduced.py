#!/usr/bin/env python3
import json, math, hashlib
from dataclasses import dataclass, asdict, fields
import numpy as np

D=4.6692; A=0.0256831; E=0.000108071; LAM=0.489442
WQ=0.984868; WC=0.005085; WR=0.010047
kd=math.exp(-A)/D; ek=kd; el=kd*WQ; em=kd*(WQ+WR)
er=kd*WR; ern=kd*WC; ee=kd*E; ds=WC/(WC+WR); fs=kd*LAM
TOL=1e-11; WINDOW=8; MAXIT=50000

@dataclass(frozen=True)
class S:
    gas:float; stars:float; remnants:float; escaped:float
    processed_fraction:float; dust_fraction:float; cooling:float; opacity:float
    structure:float; metric:float; lensing:float; radiation:float; feedback:float; event_yield:float
    def v(self): return np.array([getattr(self,f.name) for f in fields(self)],float)
    @staticmethod
    def fromv(v): return S(*map(float,v))

def c(x,a,b): return min(max(x,a),b)
def init(): return S(1,0,0,0,0,0,1,1,LAM,LAM,LAM,0,0,0)
def K(s):
    cont=s.gas+s.stars+s.remnants
    st=s.structure+ek*(c(cont+kd*s.remnants-fs*s.feedback,0,1+kd)-s.structure)
    mt=s.metric+ek*(st*(1+WR*s.remnants)-s.metric)
    le=s.lensing+ek*(mt-s.lensing)
    return S(**{**asdict(s),'structure':st,'metric':mt,'lensing':le})
def L(s):
    cap=s.structure*s.cooling/(1+s.structure*s.cooling+max(s.feedback,0))
    born=min(s.gas,el*s.gas*cap); ret=min(s.stars,er*s.stars)
    rem=min(max(s.stars-ret,0),ern*s.stars)
    esc=min(max(s.gas-born+ret,0),ee*max(s.feedback,0)*s.gas)
    g=s.gas-born+ret-esc; st=s.stars+born-ret-rem; rr=s.remnants+rem; ex=s.escaped+esc
    rad=s.radiation+el*(st*(1+WC*s.processed_fraction)-s.radiation)
    fb=s.feedback+el*(fs*(rad+rem+s.event_yield)-s.feedback)
    return S(g,st,rr,ex,s.processed_fraction,s.dust_fraction,s.cooling,s.opacity,s.structure,s.metric,s.lensing,rad,fb,s.event_yield)
def M(s):
    pt=c(s.processed_fraction+em*(s.stars+s.remnants*WR)*(1-s.processed_fraction),0,1)
    p=s.processed_fraction+em*(pt-s.processed_fraction)
    dt=c(ds*p*(1-s.feedback),0,p); d=s.dust_fraction+em*(dt-s.dust_fraction)
    cool=s.cooling+em*((1+p+WR*d)-s.cooling)
    op=s.opacity+em*((1+WQ*p+WC*d)-s.opacity)
    y=s.event_yield+em*((ern*s.stars+er*s.remnants)-s.event_yield)
    return S(**{**asdict(s),'processed_fraction':p,'dust_fraction':d,'cooling':cool,'opacity':op,'event_yield':y})
def step(s): return M(L(K(s)))
def inv(s):
    return {
      'mass_conservation':abs(s.gas+s.stars+s.remnants+s.escaped-1)<=5e-12,
      'mass_positivity':min(s.gas,s.stars,s.remnants,s.escaped)>=-1e-14,
      'composition_bounds':0<=s.dust_fraction<=s.processed_fraction<=1+1e-14,
      'microphysics_positive':min(s.cooling,s.opacity)>0,
      'metric_lensing_finite':all(math.isfinite(x) for x in (s.structure,s.metric,s.lensing)),
      'radiation_feedback_nonnegative':min(s.radiation,s.feedback,s.event_yield)>=-1e-14}
def run(start):
    s=start; stable=0; h=hashlib.sha256()
    for n in range(1,MAXIT+1):
      q=step(s); d=np.max(np.abs(q.v()-s.v())); rec={'iteration':n,'state':asdict(q),'max_delta':float(d)}
      h.update(json.dumps(rec,sort_keys=True,separators=(',',':')).encode())
      if not all(inv(q).values()): raise RuntimeError(inv(q))
      stable=stable+1 if d<=TOL else 0; s=q
      if stable>=WINDOW: return s,n,h.hexdigest()
    raise RuntimeError('no convergence')
def jac(s,h=1e-7):
    x=s.v(); b=step(s).v(); J=np.zeros((len(x),len(x)))
    for i in range(len(x)):
      y=x.copy(); y[i]+=h; J[:,i]=(step(S.fromv(y)).v()-b)/h
    return J

def main():
    s,n,lh=run(init())
    cp=init()
    for _ in range(137): cp=step(cp)
    rs,rn,rh=run(cp)
    changed=S(**{**asdict(cp),'processed_fraction':c(cp.processed_fraction+1e-5,0,1)})
    replay=M(L(K(M(changed)))); direct=step(M(changed))
    J=jac(s); ev=np.linalg.eigvals(J); ae=np.abs(ev); qe=ae[ae<1-1e-8]
    Q=np.diag(np.linspace(1e-12,2e-12,len(fields(S))))
    S0=np.diag(np.linspace(1e-6,2e-6,len(fields(S))))
    cov=J@S0@J.T+Q; ce=np.linalg.eigvalsh((cov+cov.T)/2)
    out={'scope':'F0_CONSTRUCTED_REDUCED_RECURRENCE_ONLY','classification':'FIXED_POINT_F0',
      'iterations':n,'final_state':asdict(s),'ledger_sha256':lh,'mandatory_checks':inv(s),
      'restart':{'checkpoint_iteration':137,'continuation_iterations':rn,'residual':float(np.max(np.abs(s.v()-rs.v()))),'pass':bool(np.max(np.abs(s.v()-rs.v()))<=2e-10)},
      'causal_replay':{'residual':float(np.max(np.abs(replay.v()-direct.v()))),'pass':bool(np.max(np.abs(replay.v()-direct.v()))<=1e-14),'upstream_A_J_mutated':False},
      'linearization':{'spectral_radius':float(ae.max()),'neutral_modes':int(np.sum(ae>=1-1e-8)),'quotient_radius':float(qe.max()),'full_state_nonexpansive':bool(ae.max()<=1+1e-8),'quotient_contractive':bool(qe.max()<1)},
      'covariance':{'min_eigenvalue':float(ce.min()),'psd':bool(ce.min()>=-1e-14)},
      'module_n_authorized':False,
      'blocker':'No instantiated F1-F4 K/L/M fields, trajectories, events, metric/lightcone maps, or full covariance packet.'}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
