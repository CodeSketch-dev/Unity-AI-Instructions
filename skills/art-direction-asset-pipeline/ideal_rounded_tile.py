import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
F='docs/ui-redesign/art-staging/hq-v3-final/'; D='Assets/_Art/2D/UiKit/'
W,HB,SH=310,200,12; H=HB+SH; K=4
R=0.22*HB*K; T=0.064*HB*K
def sdf(W_,H_,R_,cy):
    yy,xx=np.mgrid[0:H*K,0:W*K].astype(np.float32); px=xx+0.5-W*K/2; py=yy+0.5-cy
    qx=np.abs(px)-(W_/2-R_); qy=np.abs(py)-(H_/2-R_)
    return np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-R_
GREY=False
def build(src):
    a=np.asarray(src.convert('RGBA'),dtype=np.float32)/255; rgb=a[...,:3]; al=a[...,3]; LUM=np.array([.3,.59,.11],dtype=np.float32)
    dark=((rgb@LUM)<0.28)&(al>0.5); nd=(~dark)&(al>0.5)
    idx=ndi.distance_transform_edt(~nd,return_distances=False,return_indices=True); base=rgb[idx[0],idx[1]]
    for c in range(3): base[...,c]=ndi.gaussian_filter(base[...,c],0.9)
    oc=rgb[dark].mean(axis=0); ys,xs=np.where(al>0.5); base=base[ys.min():ys.max()+1,xs.min():xs.max()+1]
    big=np.zeros((H*K,W*K,3),dtype=np.float32)
    body=np.asarray(Image.fromarray((np.clip(base,0,1)*255).astype(np.uint8)).resize((W*K,HB*K),Image.BICUBIC),dtype=np.float32)/255
    big[:HB*K]=body; big[HB*K:]=body[-1]
    d=sdf(W*K,HB*K,R,HB*K/2); A=np.clip(0.5-d,0,1); O=np.clip(T-(-d)+0.5,0,1)*A
    gy=np.linspace(1.10,0.90,H*K,dtype=np.float32)[:,None,None] if GREY else 1.0
    big=np.clip(big*gy,0,1)
    col=big*(1-O[...,None])+oc*O[...,None]
    ds_=sdf(W*K,HB*K,R,HB*K/2+SH*K); As=ndi.gaussian_filter(np.clip(0.5-ds_,0,1),1.3*K)*0.30*(1-A)       # soft blurred Knife-Tower style drop shadow
    sc=np.array([.05,.08,.18],dtype=np.float32)
    A2=A+As*(1-A); col2=np.where(A2[...,None]>1e-4,(col*A[...,None]+sc*As[...,None]*(1-A[...,None]))/np.maximum(A2[...,None],1e-4),0)
    def ds(x): return np.asarray(Image.fromarray((np.clip(x,0,1)*255).astype(np.uint8)).resize((W,H),Image.LANCZOS),dtype=np.uint8)
    return Image.fromarray(np.dstack([ds(col2[...,i]) for i in range(3)]+[ds(A2)]))
for tgt,src in (('btn_on_kt','btn_blue'),('btn_off_kt','btn_grey')):
    GREY=(tgt=='btn_off_kt')
    build(Image.open(F+src+'.png')).save(D+tgt+'.png')
mp=D+'kit_manifest.json'; raw=open(mp,encoding='utf-8').read(); d=json.loads(raw)
for e in d['sprites']:
    if e['name'] in('btn_on_kt','btn_off_kt'): e.update(w=W,h=H,border=[60,60,60,60+SH],lips=[0,31,0,SH],ppu=400)
open(mp,'w',encoding='utf-8',newline='').write(json.dumps(d,indent=2) if raw.lstrip().startswith('{\n') else json.dumps(d))
