import cv2, numpy as np
def detect(frame):
    h,w=frame.shape[:2]
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    m=cv2.inRange(hsv,(99,50,50),(122,255,235))
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,21),np.uint8))
    boxes=[]
    for c in cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        x,y,bw,bh=cv2.boundingRect(c)
        if bw<18 or bh<6: continue
        ar=bw/bh
        edge = x<=2 or x+bw>=w-2
        if (1.2<ar<6.5 or (edge and 0.6<ar<6.5)) and bw<w*0.4 and cv2.contourArea(c)/(bw*bh)>0.35:
            boxes.append((x,y,bw,bh))
    return boxes

def blur_video_frames(frames, win=8, margin=0.45):
    det=[detect(f) for f in frames]
    out=[]
    for i,f in enumerate(frames):
        g=f.copy(); H,W=f.shape[:2]
        for j in range(max(0,i-win),min(len(frames),i+win+1)):
            for x,y,w,h in det[j]:
                mx,my=int(w*margin),int(h*margin*1.6)
                x0,y0=max(0,x-mx),max(0,y-my); x1,y1=min(W,x+w+mx),min(H,y+h+my)
                roi=g[y0:y1,x0:x1]
                if roi.size: g[y0:y1,x0:x1]=cv2.GaussianBlur(cv2.resize(cv2.resize(roi,(max(1,(x1-x0)//10),max(1,(y1-y0)//10))),(x1-x0,y1-y0),interpolation=cv2.INTER_LINEAR),(0,0),6)
        out.append(g)
    return out
