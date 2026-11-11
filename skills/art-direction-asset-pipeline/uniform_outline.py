import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
def smooth(im, k=2, sigma=18.0, T=None):
    a = np.asarray(im.convert('RGBA'),dtype=np.float32)/255
    h,w = a.shape[:2]; rgb=a[...,:3]; al=a[...,3]
    lum = rgb@np.array([.3,.59,.11],dtype=np.float32)
    dark = (lum<0.28)&(al>0.5)
    nd = (~dark)&(al>0.5)
    idx = ndi.distance_transform_edt(~nd, return_distances=False, return_indices=True)
    base = rgb[idx[0],idx[1]]
    for c in range(3): base[...,c] = ndi.gaussian_filter(base[...,c], 3.0)
    oc = rgb[dark].mean(axis=0)
    # smooth silhouette at k x
    big = np.asarray(Image.fromarray((al*255).astype(np.uint8)).resize((w*k,h*k),Image.BICUBIC),dtype=np.float32)/255
    g = ndi.gaussian_filter(big, sigma)
    inside = g>0.5
    dist = ndi.distance_transform_edt(inside)            # px at k-x scale, distance to silhouette edge
    # signed distance with sub-pixel: outside negative
    sd = dist - ndi.distance_transform_edt(~inside)
    if T is None:
        perim = (inside & ~ndi.binary_erosion(inside)).sum()
        T = float(np.clip(dark.sum()*k*k/max(perim,1), 2, 60))   # uniform outline width at k-x scale
    A = np.clip(sd+0.5,0,1)                                       # 1px AA on the silhouette
    O = np.clip(T-(sd-0.5)+0.0,0,1)*A                             # outline = band of width T inside the edge
    O = np.clip(np.minimum(O,1),0,1)
    # downsample
    def ds(m): return np.asarray(Image.fromarray((np.clip(m,0,1)*255).astype(np.uint8)).resize((w,h),Image.LANCZOS),dtype=np.float32)/255
    A2,O2 = ds(A),ds(O)
    O2 = np.minimum(O2,A2)
    col = base*(1-O2[...,None]) + oc*O2[...,None]
    return Image.fromarray((np.dstack([np.clip(col,0,1),A2])*255).astype(np.uint8)), T/k
if __name__=='__main__':
    im,T=smooth(Image.open(sys.argv[1])); print('outline px',T); im.save(sys.argv[2])
