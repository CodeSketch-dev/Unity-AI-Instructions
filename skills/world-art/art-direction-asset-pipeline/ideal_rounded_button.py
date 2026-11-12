import os,shutil,numpy as np
from PIL import Image
from scipy import ndimage as ndi
F='docs/ui-redesign/art-staging/hq-v3-final/'; D='Assets/_Art/2D/UiKit/'
W,H=448,155; K=4                       # output size, supersample
R=0.30*H*K; T=0.078*H*K                # corner radius (30% H), outline thickness (5.8% H ~ 9 px at 155)
def build(src):
    a=np.asarray(src.convert('RGBA'),dtype=np.float32)/255
    rgb=a[...,:3]; al=a[...,3]; LUM=np.array([.3,.59,.11],dtype=np.float32); lum=rgb@LUM
    dark=(lum<0.28)&(al>0.5); nd=(~dark)&(al>0.5)
    idx=ndi.distance_transform_edt(~nd,return_distances=False,return_indices=True)
    base=rgb[idx[0],idx[1]]
    for c in range(3): base[...,c]=ndi.gaussian_filter(base[...,c],3.0)
    oc=rgb[dark].mean(axis=0)
    ys,xs=np.where(al>0.5); base=base[ys.min():ys.max()+1,xs.min():xs.max()+1]
    # fill resampled to the K-x canvas (bicubic)
    big=np.asarray(Image.fromarray((np.clip(base,0,1)*255).astype(np.uint8)).resize((W*K,H*K),Image.BICUBIC),dtype=np.float32)/255
    yy,xx=np.mgrid[0:H*K,0:W*K].astype(np.float32); px=xx+0.5-W*K/2; py=yy+0.5-H*K/2
    qx=np.abs(px)-(W*K/2-R); qy=np.abs(py)-(H*K/2-R)
    d=np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-R   # <0 inside
    A=np.clip(0.5-d,0,1); depth=-d; O=np.clip(T-depth+0.5,0,1)*A
    col=big*(1-O[...,None])+oc*O[...,None]
    out=np.dstack([col,A])
    def ds(x): return np.asarray(Image.fromarray((np.clip(x,0,1)*255).astype(np.uint8)).resize((W,H),Image.LANCZOS),dtype=np.float32)
    o=np.dstack([ds(col[...,i]) for i in range(3)]+[ds(A)])
    return Image.fromarray(o.astype(np.uint8))
for c in ['blue','green','orange','red','yellow','cyan','purple','grey']:
    im=build(Image.open(F+f'btn_{c}.png'))
    a=np.asarray(im,dtype=np.float32); rgb=a[...,:3]; lum=(rgb@np.array([.3,.59,.11],dtype=np.float32))[...,None]
    var={'':rgb,'_pressed':np.clip(rgb*0.88,0,255),'_disabled':np.clip((rgb+(lum-rgb)*0.7)*0.94,0,255)}
    for suf,arr in var.items():
        n=f'btn_{c}{suf}'
        if os.path.exists(D+n+'.png.meta'): Image.fromarray(np.dstack([arr,a[...,3:]]).astype(np.uint8)).save(D+n+'.png')
    t=f'tag_label_{c}'
    if os.path.exists(D+t+'.png.meta'): shutil.copyfile(D+f'btn_{c}.png',D+t+'.png')
print('R px at 448x155:',R/K,'T px:',T/K)
