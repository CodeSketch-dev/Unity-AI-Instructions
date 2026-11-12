# usage: python -I cut_icon.py src dst size [--holes]
import sys
from PIL import Image
from collections import deque
src,dst,size=sys.argv[1],sys.argv[2],int(sys.argv[3]); holes='--holes' in sys.argv
im=Image.open(src).convert('RGBA'); px=im.load(); w,h=im.size
D=lambda p:(255-p[0])+p[1]+(255-p[2])
def flood(seeds):
    seen=bytearray(w*h); q=deque(seeds)
    while q:
        x,y=q.popleft()
        if x<0 or y<0 or x>=w or y>=h or seen[y*w+x]: continue
        seen[y*w+x]=1; p=px[x,y]; d=D(p)
        if d<70: px[x,y]=(0,0,0,0); q.extend(((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
        elif d<200 and p[3]>0: t=max(0.0,1-(d-70)/130.0); px[x,y]=(int(p[0]*(1-t*.6)),p[1],int(p[2]*(1-t*.6)),int(p[3]*(1-t)))
flood([(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)])
if holes:   # enclosed canvas pockets: only BIG pure-magenta regions (>= 400 px) are background, small pink facets stay
    seen=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            if seen[y*w+x] or px[x,y][3]==0 or D(px[x,y])>=30: continue
            reg=[]; q=deque([(x,y)])
            while q:
                a,b=q.popleft()
                if a<0 or b<0 or a>=w or b>=h or seen[b*w+a]: continue
                p=px[a,b]
                if p[3]==0 or D(p)>=30: continue
                seen[b*w+a]=1; reg.append((a,b)); q.extend(((a+1,b),(a-1,b),(a,b+1),(a,b-1)))
            if len(reg)>=400:
                for a,b in reg: px[a,b]=(0,0,0,0)
                flood([(a+dx,b+dy) for a,b in reg[::7] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))])
bb=im.getchannel('A').point(lambda v:255 if v>200 else 0).getbbox(); c=im.crop(bb); c.thumbnail((size,size),Image.LANCZOS)
sq=Image.new('RGBA',(max(c.size),)*2,(0,0,0,0)); sq.alpha_composite(c,((sq.width-c.width)//2,(sq.height-c.height)//2)); sq.resize((size,size),Image.LANCZOS).save(dst)
