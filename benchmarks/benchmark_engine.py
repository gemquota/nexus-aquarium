#!/usr/bin/env python3
"""Repeatable NEXUS simulation scaling and snapshot benchmark. Timings are machine-specific."""
from __future__ import annotations
import argparse,json,statistics,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import Engine

def percentile(values,q):
    a=sorted(values); return a[min(len(a)-1,max(0,int((len(a)-1)*q)))]

def benchmark(population,steps,warmup):
    engine=Engine(seed=20261031,config={"max_organisms":max(5000,population+64)})
    for i in range(max(0,population-len(engine.organisms))):
        engine.add("reef_fish",float((i*37)%(engine.config["world_width"]-2)+1),float(engine.config["world_height"]*(.82+((i*13)%17)/100)),vx=.1)
    for _ in range(warmup): engine.step(1/30)
    step_ms=[]; snapshot_ms=[]; encode_ms=[]; stages={}; payload_bytes=0
    for _ in range(steps):
        start=time.perf_counter(); engine.step(1/30); step_ms.append((time.perf_counter()-start)*1000)
        for name,value in engine.performance.get("stages_ms",{}).items(): stages.setdefault(name,[]).append(float(value))
        start=time.perf_counter(); snap=engine.snapshot(); snapshot_ms.append((time.perf_counter()-start)*1000)
        start=time.perf_counter(); encoded=json.dumps(snap,separators=(",",":")); encode_ms.append((time.perf_counter()-start)*1000); payload_bytes=len(encoded.encode())
    mean=statistics.fmean(step_ms); last=engine.performance.get("stages_ms",{})
    return {"target_population":population,"alive":sum(o.alive for o in engine.organisms),
      "step_mean_ms":mean,"step_median_ms":statistics.median(step_ms),"step_p95_ms":percentile(step_ms,.95),"step_p99_ms":percentile(step_ms,.99),
      "snapshot_mean_ms":statistics.fmean(snapshot_ms),"json_encode_mean_ms":statistics.fmean(encode_ms),"snapshot_bytes":payload_bytes,
      "steps_per_second":1000/mean if mean else 0,"30fps_budget_pct":mean/(1000/30)*100,
      "stage_mean_ms":{k:statistics.fmean(v) for k,v in stages.items()},
      "slowest_stage":max(last,key=last.get) if last else "none"}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--steps",type=int,default=60);p.add_argument("--warmup",type=int,default=10);p.add_argument("--populations",default="39,200,500,1000");p.add_argument("--json",dest="json_path")
    a=p.parse_args()
    if a.steps<1 or a.warmup<0:p.error("--steps must be positive and --warmup non-negative")
    counts=[int(v.strip()) for v in a.populations.split(",") if v.strip()]
    if not counts or any(v<1 for v in counts) or len(set(counts))!=len(counts):p.error("--populations must contain unique positive integers")
    results=[benchmark(n,a.steps,a.warmup) for n in counts]
    print("NEXUS AQUARIUM PERFORMANCE BENCHMARK");print(f"steps={a.steps} warmup={a.warmup} fixed_dt={1/30:.6f}s")
    print("population | mean | p95 | p99 | snapshot | JSON encode | payload | 30fps budget")
    for r in results:print(f"{r['target_population']:10d} | {r['step_mean_ms']:7.2f}ms | {r['step_p95_ms']:7.2f}ms | {r['step_p99_ms']:7.2f}ms | {r['snapshot_mean_ms']:7.2f}ms | {r['json_encode_mean_ms']:7.2f}ms | {r['snapshot_bytes']:8d} B | {r['30fps_budget_pct']:6.1f}%")
    if a.json_path:Path(a.json_path).write_text(json.dumps({"steps":a.steps,"warmup":a.warmup,"results":results},indent=2)+"\n",encoding="utf-8")
    print("Machine-specific timings: compare equivalent hardware and Python versions.")
if __name__=="__main__":main()
