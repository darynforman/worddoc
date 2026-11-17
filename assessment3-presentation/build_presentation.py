"""Build an editable PowerPoint plus slide previews, using standard OOXML and Pillow.
Run: python3 build_presentation.py --project /path/to/test3 --out /path/to/output
No network or additional Python packages beyond Pillow are required.
"""
import argparse, copy, csv, hashlib, json, math, statistics, textwrap, zipfile
from pathlib import Path
from xml.etree import ElementTree as E
from PIL import Image, ImageDraw, ImageFont

parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,default=Path('/home/daryn-forman/Documents/test3'));parser.add_argument('--out',type=Path,default=Path('/tmp/imagelab-presentation-build/output'));args=parser.parse_args()
ROOT=args.project;OUT=args.out;OUT.mkdir(parents=True,exist_ok=True);(OUT/'previews').mkdir(exist_ok=True)
DATA=ROOT/'assessment3/results/measured-suite'
ROWS=list(csv.DictReader((DATA/'runs.csv').open()));SUMMARY=list(csv.DictReader((DATA/'summary.csv').open()))
assert len(ROWS)==18 and all(sum(r['condition']==c and r['mode']==m for r in ROWS)==3 for c in 'ABC' for m in ['sse','long'])
A='http://schemas.openxmlformats.org/drawingml/2006/main';P='http://schemas.openxmlformats.org/presentationml/2006/main';R='http://schemas.openxmlformats.org/officeDocument/2006/relationships';REL='http://schemas.openxmlformats.org/package/2006/relationships';CT='http://schemas.openxmlformats.org/package/2006/content-types'
for name,ns in [('a',A),('p',P),('r',R)]:E.register_namespace(name,ns)
def tag(ns,name):return '{'+ns+'}'+name
def el(parent,ns,name,attrs=None,text=None):
 x=E.SubElement(parent,tag(ns,name),{k:str(v) for k,v in (attrs or {}).items()});x.text=text;return x
def xml(x):return E.tostring(x,encoding='utf-8',xml_declaration=True)
def emu(px):return str(round(px*6350))
def solid(parent,color):el(el(parent,A,'solidFill'),A,'srgbClr',{'val':color})
BG='F7F8F6';WHITE='FFFFFF';INK='152D2B';TEAL='147D70';PURPLE='6357AC';MUTED='60716E';LINE='DAE3DE';PALE='E7F1ED';LAV='EEEAF6';AMBER='A76720'
FONTREG='/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf';FONTBOLD='/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf';FONTMONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
if not Path(FONTREG).exists():FONTREG='/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf';FONTBOLD=FONTREG.replace('Regular','Bold')
def font(pt,bold=False,mono=False):return ImageFont.truetype(FONTMONO if mono else FONTBOLD if bold else FONTREG,round(pt*2))
SLIDES=[];WARNINGS=[];MEDIA={}
def blank_tree():
 tree=E.Element(tag(P,'spTree'));n=el(tree,P,'nvGrpSpPr');el(n,P,'cNvPr',{'id':1,'name':''});el(n,P,'cNvGrpSpPr');el(n,P,'nvPr');g=el(tree,P,'grpSpPr');x=el(g,A,'xfrm');
 for name,attrs in [('off',{'x':0,'y':0}),('ext',{'cx':0,'cy':0}),('chOff',{'x':0,'y':0}),('chExt',{'cx':0,'cy':0})]:el(x,A,name,attrs)
 return tree
class Slide:
 def __init__(self,title,section='IMPLEMENTATION',dark=False,subtitle=None,source=None,clean=False):
  self.title=title;self.dark=dark;self.root=E.Element(tag(P,'sld'),{'showMasterSp':'0'});c=el(self.root,P,'cSld',{'name':title});solid(el(c,P,'bg').makeelement(tag(P,'bgPr'),{}) if False else el(c.find(tag(P,'bg')) if c.find(tag(P,'bg')) is not None else el(c,P,'bg'),P,'bgPr'),INK if dark else BG)
  self.tree=blank_tree();c.append(self.tree);el(el(self.root,P,'clrMapOvr'),A,'masterClrMapping');self.id=1;self.rels=[];self.img=Image.new('RGB',(1920,1080),'#'+(INK if dark else BG));self.draw=ImageDraw.Draw(self.img);self.notes='';SLIDES.append(self)
  if section:
   self.text(96,48,1700,40,'IMAGELAB  /  '+section,12,PALE if dark else TEAL,True)
   self.text(96,113,1730,96,title,32,WHITE if dark else INK,True)
   if subtitle:self.text(98,203,1710,54,subtitle,17,PALE if dark else MUTED)
  self.line(96,1005,1824,1005,TEAL if dark else LINE,1)
  if not clean:self.text(96,1020,1500,36,source or 'CMPS 4191  •  Assessment 3  •  Daryn Forman',10,PALE if dark else MUTED)
  self.text(1740,1017,84,40,f'{len(SLIDES):02}',12,PALE if dark else MUTED,align='right')
 def shape(self,x,y,w,h,fill=WHITE,outline=None,kind='rect',stroke=1):
  self.id+=1;s=el(self.tree,P,'sp');n=el(s,P,'nvSpPr');el(n,P,'cNvPr',{'id':self.id,'name':f'{kind} {self.id}'});el(n,P,'cNvSpPr');el(n,P,'nvPr');sp=el(s,P,'spPr');tf=el(sp,A,'xfrm');el(tf,A,'off',{'x':emu(x),'y':emu(y)});el(tf,A,'ext',{'cx':emu(w),'cy':emu(h)});el(el(sp,A,'prstGeom',{'prst':kind}),A,'avLst');solid(sp,fill) if fill else el(sp,A,'noFill');ln=el(sp,A,'ln',{'w':emu(stroke)});solid(ln,outline) if outline else el(ln,A,'noFill')
  if fill is None and outline is None:return s
  box=(round(x),round(y),round(x+w),round(y+h))
  if kind=='ellipse':self.draw.ellipse(box,fill='#'+fill if fill else None,outline='#'+outline if outline else None,width=max(1,round(stroke)))
  elif kind=='roundRect':self.draw.rounded_rectangle(box,radius=16,fill='#'+fill if fill else None,outline='#'+outline if outline else None,width=max(1,round(stroke)))
  else:self.draw.rectangle(box,fill='#'+fill if fill else None,outline='#'+outline if outline else None,width=max(1,round(stroke)))
  return s
 def text(self,x,y,w,h,text,pt=20,color=INK,bold=False,align='left',mono=False):
  f=font(pt,bold,mono);lines=[]
  for para in str(text).split('\n'):
   if not para:lines.append('');continue
   words=para.split(' ');current=''
   for word in words:
    candidate=(current+' '+word).strip()
    if f.getlength(candidate)>w-4 and current:lines.append(current);current=word
    else:current=candidate
   lines.append(current)
  leading=pt*2*1.20
  if leading*len(lines)>h+3:WARNINGS.append({'slide':len(SLIDES),'text':str(text)[:90],'need':round(leading*len(lines)),'height':h})
  for line in lines:
   if f.getlength(line)>w:WARNINGS.append({'slide':len(SLIDES),'overwide':line})
  s=self.shape(x,y,w,h,fill=None);s.find(tag(P,'nvSpPr')).find(tag(P,'cNvPr')).set('name',str(text)[:100]);s.find(tag(P,'nvSpPr')).find(tag(P,'cNvSpPr')).set('txBox','1');body=el(s,P,'txBody');el(body,A,'bodyPr',{'wrap':'none','lIns':0,'rIns':0,'tIns':0,'bIns':0,'anchor':'t'});el(body,A,'lstStyle')
  for i,line in enumerate(lines):
   p=el(body,A,'p');ppr=el(p,A,'pPr',{'algn':{'left':'l','center':'ctr','right':'r'}[align]});el(el(ppr,A,'lnSpc'),A,'spcPts',{'val':round(pt*1.2*100)});el(ppr,A,'buNone');run=el(p,A,'r');rp=el(run,A,'rPr',{'lang':'en-US','sz':round(pt*100),'b':int(bold)});solid(rp,color);el(rp,A,'latin',{'typeface':'DejaVu Sans Mono' if mono else 'Arial'});el(run,A,'t',text=line)
   yy=y+i*leading;xx=x if align=='left' else x+(w-f.getlength(line))/2 if align=='center' else x+w-f.getlength(line)
   self.draw.text((round(xx),round(yy)),line,font=f,fill='#'+color,anchor='lt')
  return s
 def vertical_text(self,cx,cy,width,height,text,pt=19,color=MUTED):
  before=self.img.copy()
  shape=self.text(cx-width/2,cy-height/2,width,height,text,pt,color,align='center')
  shape.find(tag(P,'spPr')).find(tag(A,'xfrm')).set('rot','16200000')
  self.img=before;self.draw=ImageDraw.Draw(self.img)
  layer=Image.new('RGBA',(width,height),(0,0,0,0));d=ImageDraw.Draw(layer);f=font(pt)
  d.text(((width-f.getlength(text))/2,0),text,font=f,fill='#'+color,anchor='lt')
  layer=layer.rotate(90,expand=True)
  self.img.paste(layer,(round(cx-layer.width/2),round(cy-layer.height/2)),layer)
  return shape
 def line(self,x1,y1,x2,y2,color=LINE,width=2):
  self.id+=1;s=el(self.tree,P,'cxnSp');nv=el(s,P,'nvCxnSpPr');el(nv,P,'cNvPr',{'id':self.id,'name':f'Line {self.id}'});el(nv,P,'cNvCxnSpPr');el(nv,P,'nvPr');sp=el(s,P,'spPr');tf=el(sp,A,'xfrm',{'flipH':int(x2<x1),'flipV':int(y2<y1)});el(tf,A,'off',{'x':emu(min(x1,x2)),'y':emu(min(y1,y2))});el(tf,A,'ext',{'cx':emu(abs(x2-x1)),'cy':emu(abs(y2-y1))});el(el(sp,A,'prstGeom',{'prst':'line'}),A,'avLst');solid(el(sp,A,'ln',{'w':emu(width)}),color);self.draw.line((round(x1),round(y1),round(x2),round(y2)),fill='#'+color,width=max(1,round(width)))
 def picture(self,path,x,y,w,h):
  path=Path(path);im=Image.open(path).convert('RGB');iw,ih=im.size;scale=min(w/iw,h/ih);nw,nh=round(iw*scale),round(ih*scale);x+=round((w-nw)/2);y+=round((h-nh)/2);w,h=nw,nh
  self.id+=1;name='image'+str(len(MEDIA)+1)+'.png';MEDIA[name]=path.read_bytes();rid='rIdImage'+str(self.id);self.rels.append((rid,R+'/image','../media/'+name));pic=el(self.tree,P,'pic');nv=el(pic,P,'nvPicPr');el(nv,P,'cNvPr',{'id':self.id,'name':path.name});el(nv,P,'cNvPicPr');el(nv,P,'nvPr');b=el(pic,P,'blipFill');el(b,A,'blip',{tag(R,'embed'):rid});el(el(b,A,'stretch'),A,'fillRect');sp=el(pic,P,'spPr');tf=el(sp,A,'xfrm');el(tf,A,'off',{'x':emu(x),'y':emu(y)});el(tf,A,'ext',{'cx':emu(w),'cy':emu(h)});el(el(sp,A,'prstGeom',{'prst':'rect'}),A,'avLst');self.img.paste(im.resize((w,h),Image.Resampling.LANCZOS),(round(x),round(y)))
 def card(self,x,y,w,h,number,title,body,color=TEAL):
  self.shape(x,y,w,h,WHITE,kind='roundRect');self.text(x+28,y+24,w-56,48,number,15,color,True);self.text(x+28,y+83,w-56,88,title,24,INK,True);self.text(x+28,y+180,w-56,h-195,body,19,MUTED)
 def note(self,seconds,script,sources=''):
  self.notes=f'Target time: {seconds} seconds.\n\n{script}\n\nEvidence / references: {sources}'
 def table(self,x,y,width,headers,rows,widths=None,rowh=78,pt=17):
  widths=widths or [1/len(headers)]*len(headers);self.shape(x,y,width,rowh,INK)
  for ri,row in enumerate([headers]+rows):
   yy=y+ri*rowh
   if ri:self.shape(x,yy,width,rowh,WHITE if ri%2 else 'EFF3F0')
   xx=x
   for j,value in enumerate(row):
    ww=width*widths[j];self.text(xx+18,yy+20,ww-30,rowh-25,str(value),pt if ri else min(pt,15),WHITE if not ri else (TEAL if str(value)=='SSE' else PURPLE if str(value)=='Long' else INK),bool(not ri));xx+=ww
   if ri:self.line(x,yy+rowh,x+width,yy+rowh,LINE,1)

def summary(c,m):return next(r for r in SUMMARY if r['condition']==c and r['mode']==m)
def n(v):return f'{float(v):g}'
def banner(s,text,y=885,fill=PALE,color=INK):s.shape(96,y,1728,76,fill,kind='roundRect');s.text(124,y+20,1672,48,text,19,color)

# 01 — title
s=Slide('ImageLab',section=None,dark=True)
s.text(100,74,1550,42,'CMPS 4191  /  ADVANCED WEB TECHNOLOGIES',13,PALE,True)
s.text(96,220,1050,280,'One response.\nLive job updates.',57,WHITE,True)
s.text(100,541,1080,180,'Server-Sent Events in ImageLab\nImplementation and measured comparison',23,'C1DAD3')
s.shape(1310,229,410,410,TEAL,kind='roundRect')
for i,yy in enumerate([292,402,512]):
 s.shape(1360,yy,310,66,WHITE,kind='roundRect');s.text(1384,yy+16,265,45,['queued  ·  v1','processing  ·  v2','completed  ·  v6'][i],15,INK,True)
s.text(1310,690,410,95,'ONE GET\nMULTIPLE SNAPSHOTS',17,PALE,True,align='center')
s.text(100,802,1050,90,'Daryn Forman\nAssessment 3  •  16 November 2026',19,WHITE)
s.note(25,'My project extends ImageLab with Server-Sent Events. I will show how one streaming response delivers changing job snapshots, demonstrate the observer lifecycle, and compare SSE with long polling using the recorded 18-run experiment. The main presentation is approximately 13–15 minutes; detailed tables and answers are in the appendix.','Both supplied Assessment 3 documents; assessment3/results/measured-suite.')

# 02 — pipeline
s=Slide('The worker owns processing. PostgreSQL owns state.',subtitle='SSE changes observation; the existing image pipeline stays in place.')
for x,title,body in [(96,'Upload','POST /v1/images\nValidate image'),(545,'Accept','Commit queued job\nReturn 202 + URL'),(994,'Process','One worker\nStore 3 variants'),(1443,'Finish','Save terminal state\nShow all variants')]:
 s.shape(x,310,381,280,WHITE,kind='roundRect');s.text(x+26,342,330,60,title,25,INK,True);s.text(x+26,431,330,120,body,18,MUTED)
 if x<1443:s.text(x+391,411,48,60,'→',22,TEAL,True)
s.shape(96,680,1728,152,PALE,kind='roundRect');s.text(124,703,1672,74,'queued  →  processing  →  completed / failed',29,TEAL,True,align='center');s.text(125,779,1668,46,'Thumbnail 150 × 150    •    Preview fits 800 × 600    •    Display fits 1200 × 900',18,INK,align='center')
s.note(40,'The request validates the image, stores its original bytes and commits an image and queued job together. Only then does it return 202 Accepted. This guarantees durable acceptance, not successful processing. One background worker claims the job and generates the three required variants. Partial metadata may describe truthful progress, but result URLs and the browser result cards are available only after completed. A failed job gets a safe error. Disconnecting an observer never owns or cancels this worker.','cmd/api/images.go; cmd/api/worker.go; internal/data/jobs.go; JOB-01 to JOB-06.')

# 03 — transport comparison
s=Slide('Three observation modes. One job representation.',subtitle='The controlled experiment compares SSE with version-based long polling.')
for i,(label,desc,col) in enumerate([('Short polling','GET a snapshot, wait one second, repeat.',MUTED),('Long polling','Hold a GET until change or timeout; then send another.',PURPLE),('SSE','Hold one response; deliver successive job-update events.',TEAL)]):
 yy=300+i*192;s.text(98,yy,340,60,label,25,col,True);s.text(98,yy+64,510,100,desc,18,MUTED)
 start=735;end=1780;liney=yy+65
 s.line(start,liney,end,liney,LINE,3)
 if i==0:
  for xx in [760,1030,1300,1570]:s.shape(xx,liney-16,116,32,'B6C2BD',kind='roundRect')
 elif i==1:
  for xx in [760,1100,1440]:s.shape(xx,liney-16,270,32,PURPLE,kind='roundRect')
 else:
  s.shape(760,liney-16,940,32,TEAL,kind='roundRect')
  for xx in [810,1070,1270,1510,1660]:s.shape(xx,liney-30,20,60,INK,kind='ellipse')
s.text(736,903,1050,50,'Illustrative request timelines; lengths are not measured durations.',14,MUTED)
s.note(40,'Short polling always replies promptly and the browser schedules another request after one second. Long polling sends the last observed version and holds an unchanged active job for up to twenty seconds. When the response ends, the client sends another GET. SSE is different: the server can flush several named updates through a single open response. All modes use the same authoritative job representation and browser renderer. This picture is conceptual rather than measured timing. Count HTTP requests, not TCP connections.','cmd/api/jobs.go; web/assets/app.js; SSE-01; assessment3/README.md.')

# 04 — wire contract
s=Slide('A named event carries a complete current snapshot.',subtitle='GET /v1/jobs/{public-job-id}/events',source='Contract: SSE-01–09  •  Example values below are illustrative, not measured records.')
s.shape(96,290,1728,136,INK,kind='roundRect');s.text(125,300,1672,122,'Content-Type: text/event-stream; charset=utf-8\nCache-Control: no-cache, no-transform\nX-Accel-Buffering: no',16,WHITE,mono=True)
s.shape(96,455,1160,411,WHITE,kind='roundRect')
code='event: job-update\ndata: {"version":1,"stage":"starting",\n       "variants_completed":0,"simulation_step":0,\n       "id":"669b0881-54d5-4740-9a81-bd2fc0a3e9f9",\n       "image_id":"11111111-2222-4333-8444-555555555555",\n       "status":"queued","queued_at":"2026-11-16T14:00:00Z",\n       "started_at":null,"completed_at":null,"failed_at":null}\n\n'
s.text(126,480,1100,340,code,15,INK,mono=True)
s.text(1280,470,520,76,'Blank line + Flush',24,TEAL,True);s.text(1280,561,520,128,'Send bytes now.\nKeep the response open.',22,INK);s.text(1280,722,520,116,'No SSE id fields.\nVersion is a state revision.',19,MUTED)
s.text(100,903,1710,54,'JSON is visually wrapped here; the server emits one data line. Unknown jobs return 404 before streaming.',15,MUTED)
s.note(50,'Show the request and response headers in DevTools. The response is UTF-8 event-stream with cache control and buffering disabled where supported. Each frame contains event: job-update, data containing the complete current JSON representation, and a blank line. The illustration wraps JSON only for readability; the real server serializes one data line. Flush makes buffered bytes available without ending the response. The JSON version is a snapshot revision; no SSE id fields or Last-Event-ID history replay are emitted. Idle heartbeat comments do not change version or count as job updates. An unknown public job ID must return ordinary 404 before the stream begins.','cmd/api/events.go: jobEventsHandler and streamJobSnapshots; Version 3 requirements, section 3.')

# 05 — broadcast
s=Slide('Commit first. Notify every observer. Reread state.',subtitle='A notification is a wake-up signal, never the authoritative payload.')
for xx,yy,w,title,body in [(96,340,405,'Worker commit','Save state + version\nCOMMIT'),(630,340,405,'Notification','One buffered signal\nper subscriber'),(1205,272,619,'SSE handler → tab A','Read PostgreSQL\nSend a newer snapshot'),(1205,578,619,'SSE handler → tab B','Read PostgreSQL\nSend a newer snapshot')]:
 s.shape(xx,yy,w,220,WHITE,kind='roundRect');s.text(xx+26,yy+27,w-52,70,title,23,INK,True);s.text(xx+26,yy+115,w-52,95,body,19,MUTED)
s.text(530,420,70,90,'→',29,TEAL,True);s.line(1057,450,1135,450,TEAL,4);s.line(1135,382,1135,688,TEAL,4);s.line(1135,382,1184,382,TEAL,4);s.line(1135,688,1184,688,TEAL,4)
banner(s,'Subscribe → read → wait: a change around subscription remains observable.')
s.note(55,'The worker increments the persisted version in the same transaction as a visible state or progress change. Notifications happen only after commit. Each observer has a buffered channel, so both tabs can be woken rather than one tab consuming a shared message. A handler subscribes before reading PostgreSQL. If a commit happens around subscription, either the read sees it or the buffered signal causes another read. Signals may coalesce and the handler sends only a newer version. Mutexes protect bookkeeping, not database queries or network writes. Every exit releases the subscriber and timer.','internal/data/jobs.go: committed and Milestone; internal/data/job_changes.go; cmd/api/events.go; SYNC-01 to SYNC-07.')

# 06 — lifecycle
s=Slide('Connection state is separate from job state.',subtitle='An interrupted observer does not turn a processing job into a failed job.')
for x,num,title,body,col in [(96,'01','Connect','Create one EventSource.\nReceive current snapshot.',TEAL),(538,'02','Interrupt','Keep the same object.\nLet the browser reconnect.',PURPLE),(980,'03','Recover','New GET, latest snapshot.\nNo event-history replay.',TEAL),(1422,'04','Finish','Render completed or failed.\nCall close(); end the stream.',INK)]:s.card(x,316,402,430,num,title,body,col)
banner(s,'Stop observing closes the stream. Observe again opens a new stream for the same job.')
s.note(45,'The EventSource object handles temporary disconnection itself. Its error handler reports reconnecting without marking the job failed or constructing duplicate EventSource objects. A new GET gets the latest authoritative snapshot. Explicit stop is different: it closes the source, and explicit resume creates a fresh source for the same accepted job. Completed and failed are terminal: render once and close the source so it does not reconnect. Firefox Offline can leave an existing stream intact or permanently close a failed initial source. Our controlled interruption demonstrates a recoverable server-stream closure; it does not establish behavior for every real network outage.','web/assets/app.js: startSSE, stopObservation, startObservation; UI-01 to UI-08; native Firefox demo verification.')

# 07 — demonstration
s=Slide('Live demo: one job, independent observers.',section='LIVE DEMONSTRATION',subtitle='Keep Firefox on No Throttling. Demo controls are explicitly enabled.')
s.shape(96,282,1728,88,INK,kind='roundRect');s.text(122,308,1678,55,'make run DEMO_CONTROLS=true WORKER_DELAY=5s SIMULATION_INTERVAL=200ms',16,WHITE,mono=True)
for i,(title,detail) in enumerate([('Inspect','202 upload → pending /events → named snapshots'),('Observe twice','Open observer tab; confirm matching job IDs'),('Stop and resume','Worker finishes; resume receives current state'),('Interrupt','Same EventSource reconnects without a second upload'),('Fail deliberately','Missing input → safe failed snapshot → stream closes')]):
 yy=415+i*100;s.text(100,yy,55,60,str(i+1).zfill(2),19,TEAL,True);s.text(182,yy,460,60,title,23,INK,True);s.text(680,yy+5,1110,65,detail,20,MUTED)
s.note(155,'Prepare a server with the displayed command before presenting. These are artificial demonstration settings: a five-second delay and ten seconds of labelled simulated updates. Keep the paired experiment separate and demo controls disabled there. Open Firefox DevTools before upload. Show POST /v1/images returning 202 and the single /events GET. Inspect its headers and Response entries; explain zero real variants during simulation and real milestones afterward. Use Open observer tab for the same job in a second tab. Show stop/resume without a new upload. For reconnection, start another active job and click Interrupt SSE streams; do not click Observe again. Watch reconnecting and a new GET from the same EventSource. For failure, click Create failed demo job. It creates a deliberately absent input rather than deleting an uploaded original. The real worker records failure and the client closes the terminal stream. A demonstration job finishes in around fifteen seconds plus real processing. Reuse the preparation delay to keep the live sequence under three minutes; if necessary demonstrate stop/resume on an already accepted job while preparing the next job. Save DevTools evidence after each case.','README.md: Two remaining classroom checks; cmd/api/demo.go; recent native Firefox verification. This slide is a cue for a LIVE DevTools trace, not a claim that a recorded trace is embedded.')

# 08 — paired method
s=Slide('18 measured runs across three controlled workloads.',section='EXPERIMENT',subtitle='Three repetitions per method per condition; pairs alternate SSE/long and long/SSE.',source='Recorded suite: 8 Nov 2026  •  Headless Firefox  •  Same image, loopback network')
s.table(96,300,1728,['Condition','Controlled workload','Prediction'],[
 ['A · Quiet','30 seconds active, no progress; then real work','SSE holds one stream; long polling may expire.'],
 ['B · Real','Store thumbnail, preview and display milestones','Both methods should deliver progress promptly.'],
 ['C · Frequent','10 simulated seconds, 200 ms updates; then real work','SSE carries many updates; long polling sends more GETs.']],widths=[.16,.40,.44],rowh=145,pt=18)
banner(s,'Same image + settings   •   Empty queue   •   One observer   •   Predictions saved before runs',y=905)
s.note(50,'The experiment matrix is three conditions times two methods times three repetitions, eighteen runs in total. Predictions were saved before measurements. A keeps the processing job quiet for thirty seconds before real work. B reports progress only after each real output and its metadata are stored. C uses fifty labelled simulated updates at two hundred milliseconds, then runs the normal transformations. The simulation field is separate from variants_completed and a timer never completes the job. Every selected run used the same input image, one observer and an empty queue, and paired method order alternated. The retained browser was headless, so these records do not establish the explicit foreground-tab condition.','assessment3/results/measured-suite/predictions.json, method.json, browser.json and runs.csv; MEAS-01 to MEAS-03.')

# 09 — measurement
s=Slide('Measure processing and delivery separately.',section='EXPERIMENT',subtitle='All detection delays are in milliseconds; uploads are excluded from observation GET counts.')
s.card(96,303,820,385,'WORKER','Processing duration','Persisted terminal timestamp\nminus worker started_at.',TEAL)
s.card(1004,303,820,385,'OBSERVER','Completion-detection delay','Browser receipt timestamp\nminus server post-commit timestamp.',PURPLE)
s.text(100,750,1710,112,'Also recorded: versions and gaps, observation reads, stream duration,\nevent / heartbeat counts, and peak active SSE handlers.',21,INK)
s.text(100,906,1710,64,'Recorded timing differs slightly: SSE stamps before JSON parsing; long polling stamps after decoding.',16,AMBER)
s.note(50,'Separate the work itself from noticing its completion. Processing uses PostgreSQL started_at and completed_at or failed_at. Detection delay subtracts the server timestamp recorded immediately after the terminal transaction commits from the browser receipt timestamp. Browser and server share one host, and integer-millisecond resolution includes scheduling and clock uncertainty. There is a small inconsistency in the retained build: SSE timestamps its event callback before parsing JSON while long polling records after response.json. The current code aligns both after JSON decoding, but the earlier recorded values have not been silently changed. Do not overinterpret differences of a few milliseconds. SSE stream GETs, named events and heartbeat comments are separate counts. Full version sequences are in raw client logs, with gaps summarized in CSV.','internal/data/jobs.go: committed; assessment3/experiment.py: summarize; runs.csv; historical source hashes; current web/assets/app.js.')

# Charts — native editable vector shapes, recomputed from source CSV.
# Each condition gets a full slide. Keep the visual comparison to two columns.
for metric in ['observation_gets','detection_ms']:
 for condition in 'ABC':
  is_get=metric=='observation_gets'
  workload={'A':'Quiet interval','B':'Real progress','C':'Frequent updates'}[condition]
  labels={('observation_gets','A'):'SSE used one observation GET; long polling used six.',
          ('observation_gets','B'):'SSE used one observation GET; long polling used five.',
          ('observation_gets','C'):'Median observation GETs: 1 with SSE, 55 with long polling.',
          ('detection_ms','A'):'Median detection: 9 ms with SSE, 10 ms with long polling.',
          ('detection_ms','B'):'Long polling had the lower recorded median: 10 ms versus 13 ms.',
          ('detection_ms','C'):'Long polling ranged from 12–45 ms; SSE ranged from 8–20 ms.'}
  title=workload+(': observation GETs' if is_get else ': completion-detection delay')
  s=Slide(title,section='MEASURED RESULTS / CONDITION '+condition,clean=True)
  # Compact graphical legend; explanations and provenance live in speaker notes.
  s.shape(1070,267,32,22,INK);s.text(1117,258,160,44,'Median',16,MUTED)
  s.shape(1301,264,25,25,WHITE,outline=INK,kind='ellipse',stroke=2);s.text(1341,258,110,44,'Run',16,MUTED)
  s.line(1479,277,1539,277,INK,3);s.line(1479,266,1479,288,INK,2);s.line(1539,266,1539,288,INK,2)
  s.text(1558,258,180,44,'Range',16,MUTED)
  limit=(6 if condition in 'AB' else 60) if is_get else 50
  ticks=([0,1,2,3,4,5,6] if condition in 'AB' else [0,10,20,30,40,50,60]) if is_get else [0,10,20,30,40,50]
  top=340;bottom=760;Y=lambda v:bottom-float(v)/limit*(bottom-top)
  s.vertical_text(57,550,600,56,'Observation GETs (count)' if is_get else 'Completion-detection delay (ms)',19)
  s.line(205,top,205,bottom,MUTED,2)
  s.line(205,bottom,1780,bottom,MUTED,2)
  s.text(205,950,1575,49,'Observation method',19,MUTED,align='center')
  for tick in ticks:
   yy=Y(tick);s.line(205,yy,1780,yy,LINE,1)
   s.text(100,yy-19,78,49,str(tick),20,MUTED,align='right')
  for mode,center,col in [('sse',650,TEAL),('long',1390,PURPLE)]:
   vals=[float(r[metric]) for r in ROWS if r['condition']==condition and r['mode']==mode]
   med=statistics.median(vals);lo=min(vals);hi=max(vals)
   s.shape(center-160,Y(med),320,bottom-Y(med),col)
   s.line(center,Y(lo),center,Y(hi),INK,5)
   s.line(center-60,Y(lo),center+60,Y(lo),INK,4)
   s.line(center-60,Y(hi),center+60,Y(hi),INK,4)
   for rep,value in enumerate(vals):
    xx=center+(rep-1)*58
    s.shape(xx-13,Y(value)-13,26,26,WHITE,outline=INK,kind='ellipse',stroke=3)
   s.text(center-320,797,640,67,'SSE' if mode=='sse' else 'Long polling',26,col,True,align='center')
   value=n(med)+(' GET' if is_get and med==1 else ' GETs' if is_get else ' ms')
   s.text(center-320,861,640,82,value,34,INK,True,align='center')
  s.note(20,'Condition '+condition+': '+workload+'. '+labels[metric,condition]+   ' The vertical axis is explicitly labelled with count or milliseconds and the horizontal axis is Observation method. The compact legend denotes median columns, individual runs and min–max ranges. Slide subtitles and source footers are intentionally omitted; recorded source, build caveats and interpretation remain here in the notes. The coloured column height is the median. The three white circles are all individual repetitions, placed side by side when values repeat. The black whisker spans minimum to maximum. Exact values are in the run tables in appendix slides 20–22. '+   ('Observation GETs exclude the upload POST and count HTTP requests, not TCP connections. A and B use a zero-to-six GET axis and C uses zero-to-sixty, so compare numerical values rather than column heights across those slides. Fewer GETs do not establish lower total resource use.' if is_get else    'All three detection slides share the zero-to-fifty millisecond scale. These are local measurements with three repetitions and timing uncertainty. They do not establish a universal speed advantage. Processing duration is separate. The historical build used slightly different receipt-timestamp placement between the modes; see slide 9.'),   'assessment3/results/measured-suite/runs.csv and summary.csv; mandatory graph '+('1' if is_get else '2')+'.')

# 12 — summary table
s=Slide('The summary table anchors both graphs.',section='MEASURED RESULTS',subtitle='Medians; brackets show minimum–maximum ranges. Every repetition is in the appendix.',source='Source: measured-suite/summary.csv  •  Full underlying records: runs.csv + per-run client.json/server.log')
data=[]
for c in 'ABC':
 for mode in ['sse','long']:
  q=summary(c,mode);data.append([c,'SSE' if mode=='sse' else 'Long',f"{n(q['observation_gets_median'])} [{n(q['observation_gets_min'])}–{n(q['observation_gets_max'])}]",f"{n(q['detection_ms_median'])} [{n(q['detection_ms_min'])}–{n(q['detection_ms_max'])}]",f"{n(q['observation_db_reads_median'])} [{n(q['observation_db_reads_min'])}–{n(q['observation_db_reads_max'])}]"])
s.table(96,296,1728,['Condition','Method','Observation GETs','Detection delay (ms)','Observation DB reads'],data,widths=[.12,.13,.23,.26,.26],rowh=83,pt=19)
s.text(100,921,1710,50,'A: quiet interval     B: real progress     C: frequent simulated updates',18,MUTED)
s.note(40,'Use this table to connect each graph back to the numerical summary. A shows a median of one SSE GET against six long-poll GETs, with nine versus ten milliseconds detection. B shows one against five and thirteen versus ten milliseconds. C shows one against fifty-five and nine versus twelve milliseconds. Observation database reads are also lower for SSE in this small sample, but request count is not itself a resource measurement. The appendix retains the eighteen rows including processing durations, version counts and stream durations, while the raw CSV retains all metrics.','summary.csv; RESULTS.md; MEAS-06 to MEAS-09.')

# 13 — gaps/resources
s=Slide('Fewer GETs do not remove observer work.',section='INTERPRETATION',subtitle='Snapshot delivery permits version gaps; stream resources still matter.')
s.card(96,310,540,482,'VERSION COVERAGE','Current snapshots','C–SSE–1 received 54 distinct versions from 1 to 56.\n\nVersions 15 and 16 were skipped; terminal 56 arrived.',TEAL)
s.card(690,310,540,482,'DATABASE READS','Measured separately','Condition C median reads:\nSSE 56\nLong polling 110\n\nQueries still serve observers.',PURPLE)
s.card(1284,310,540,482,'HELD STREAM','A live subscriber','Condition C SSE median:\n10.709 seconds open\n1 heartbeat\nPeak active handlers: 1',TEAL)
banner(s,'These runs did not measure CPU, memory, TCP connection counts or production-scale capacity.')
s.note(45,'Use C–SSE–1 as a concrete snapshot-coalescing example. The first and terminal revisions were one and fifty-six, fifty-four distinct versions arrived, and fifteen and sixteen were absent. That does not mean lost event history, because neither API promises event replay. PostgreSQL remains authoritative and the completed snapshot contains the full result. Condition C median observation reads were fifty-six for SSE and one hundred ten for long polling. SSE still held a subscriber and handler, with a median stream duration of ten point seven zero nine seconds, one heartbeat and peak one active handler. Peak one reflects the controlled one-observer run, not a scaling limit. Do not infer lower total memory or CPU cost.','C-sse-1/client.json; runs.csv; summary.csv; MEAS-05 and MEAS-10; snapshot semantics in both briefs.')

# 14 — recommendation
s=Slide('Use SSE for progress; keep long polling available.',section='RECOMMENDATION',subtitle='The evidence supports a workload-specific choice, not a universal winner.')
s.shape(96,300,820,360,PALE,kind='roundRect');s.text(128,333,756,70,'SSE for continuous progress',25,TEAL,True);s.text(128,433,756,160,'One response carries updates.\nFewer GETs with frequent updates.\nEvidence is workload-specific.',22,INK)
s.shape(1004,300,820,360,LAV,kind='roundRect');s.text(1036,333,756,70,'Long polling remains suitable',25,PURPLE,True);s.text(1036,433,756,160,'Simple request/response deployment.\nCompetitive local completion delay.\nSame durable job contract.',22,INK)
s.text(100,713,1710,180,'Limits: 3 repetitions per group; loopback network; headless Firefox.\nRecorded runs precede recent format and timing fixes.\nForeground-browser rerun remains outstanding.',22,AMBER)
s.note(45,'My recommendation is SSE where continuous progress over a held response fits the deployment, especially when updates are frequent. Long polling remains reasonable when request/response infrastructure or infrequent changes matter. Its local completion delay was competitive and it was faster at the median in B. Limitations must be explicit: only three repetitions per group on loopback with one headless Firefox observer. The explicit foreground-tab requirement has not yet been demonstrated by a rerun. The retained run source hashes describe the earlier build, before removal of prohibited SSE id fields, explicit charset, aligned receipt timing and later demo controls. These records are genuine historical evidence, not a claim that the latest build was remeasured. The original C clock anomaly was excluded and all six C runs repeated, with an audit trail. WAN, proxies, memory, CPU and scale remain unmeasured.','run-selection.json; method.json; browser.json; assessment3/STATUS.md; both supplied briefs.')

# 15 — end
s=Slide('Questions',section=None,dark=True)
s.text(100,93,1600,50,'IMAGELAB  /  ASSESSMENT 3',14,PALE,True);s.text(96,254,1728,265,'Observe the job.\nDo not own the worker.',49,WHITE,True)
s.text(102,562,1650,230,'One authoritative state.\nIndependent observers.\nAn evidence-based comparison.',29,'C1DAD3')
s.text(102,858,1710,60,'Questions  •  Detailed run tables and reference answers follow.',19,WHITE)
s.note(10,'Invite approximately five minutes of questions. Return to the wire-contract, synchronization, chart or appendix slide as needed. Do not read the appendix during the timed main presentation unless asked.','Assessment 3 suggested allocation: 10–15 minutes presenting plus 5 minutes questions.')

# 16–18 — complete measured runs
for c in 'ABC':
 s=Slide('Condition '+c+' — all six measured runs',section='APPENDIX / RUN TABLE',subtitle={'A':'30-second quiet interval followed by real image processing.','B':'Real thumbnail, preview and display processing.','C':'Ten seconds of labelled simulation at 200 ms, followed by real processing.'}[c],source='Source: measured-suite/runs.csv  •  Full job IDs, gaps, event counts and heartbeats remain in CSV/raw logs')
 data=[]
 for row in [r for r in ROWS if r['condition']==c]:
  data.append([('SSE' if row['mode']=='sse' else 'Long')+' '+row['repetition'],row['observation_gets'],row['detection_ms'],f"{float(row['processing_ms']):.3f}",row['distinct_versions'],row['observation_db_reads'],f"{float(row['stream_duration_ms'])/1000:.3f}"])
 s.table(96,304,1728,['Method / rep.','GETs','Delay ms','Processing ms','Versions¹','DB reads','SSE seconds'],data,widths=[.19,.09,.13,.20,.13,.12,.14],rowh=82,pt=18)
 s.text(102,924,1710,55,'¹ Distinct received snapshots; baseline 1 → terminal '+('56' if c=='C' else '6')+'.  Zero SSE seconds denotes long polling.',17,MUTED)
 s.note(0,'Backup table only: this slide retains all six measured repetitions for condition '+c+'. GET count excludes upload. Delay is browser receipt minus server post-commit time. Processing time is persisted started-to-terminal time and is not delivery delay. Versions counts distinct received revisions. The source CSV also records explicit gaps, stream/event/heartbeat counts and peak handlers. See the appropriate per-run folder for full job identity and raw records.','assessment3/results/measured-suite/runs.csv; six '+c+' run folders.')

# 19 — verification and reproducibility
s=Slide('Reproduce the evidence; keep demonstrations separate.',section='APPENDIX / REPRODUCIBILITY',subtitle='One server and worker per database. PostgreSQL 18+ is required.')
s.shape(96,300,1728,285,INK,kind='roundRect');s.text(126,325,1665,220,'make test-go GOFLAGS=-race\nmake test-ui\nmake test-integration   # set IMAGELAB_TEST_DSN first\npython3 assessment3/graphs.py assessment3/results/measured-suite/runs.csv',16,WHITE,mono=True)
s.text(100,645,820,220,'Current checks\n22 frontend tests\nGo race + PostgreSQL integration\nNative Firefox reconnect + failure',23,INK)
s.text(1035,645,765,250,'Recorded evidence\n18 paired measurements\nRaw client and server logs\nTables + graphs + 3-page report',23,INK)
s.text(102,919,1700,52,'Experiment setup: assessment3/README.md  •  Run with demo controls disabled.',17,MUTED)
s.note(0,'For a new experiment follow assessment3/README.md and use a dedicated initialized PostgreSQL database, the retained fixture, one foreground browser observer and an empty queue. Do not run two application workers against the same database. The existing runner is headless and needs adaptation before claiming a foreground rerun. Keep demo controls disabled during performance measurements. Go checks require Go, frontend checks require Node 18+ (the current local verification used the bundled VS Code Node runtime), browser recording needs Firefox/geckodriver, and the database uses PostgreSQL 18 UUID functions. Current verification checks controlled stream closure with the same EventSource object and safe terminal failure, not every type of network outage.','README.md; Makefile; assessment3/README.md; assessment3/STATUS.md; recent demo verification.')

# 20 — required questions
s=Slide('Five questions to be ready for.',section='APPENDIX / DISCUSSION',subtitle='Short answers; expand with the code, trace or measurement table when asked.')
answers=[('What stays open?','The HTTP response and observer handler. Flush sends buffered frame bytes.'),('How does every tab get updates?','Commit → per-subscriber notification → PostgreSQL reread → snapshot.'),('What does disconnect change?','It ends observation. The worker continues; reconnect gets current state.'),('Why no replay?','A complete snapshot recovers state; intermediate versions may coalesce.'),('What do the graphs establish?','Request and delay patterns for these runs, not total resource cost or scale.')]
for i,(q,a) in enumerate(answers):
 yy=291+i*130;s.text(100,yy,600,112,q,22,TEAL,True);s.text(760,yy,1030,104,a,21,INK)
s.note(0,'These questions come directly from the two supplied documents. Explain Flush as delivery of buffered bytes, not as the mechanism that keeps a handler alive. Notifications are after commit and wake all registered observers. Disconnection cancels only the observer. Current snapshots avoid a promise of durable event history or Last-Event-ID replay. Graphs show spread and workload differences but cannot establish production resource savings. Other useful answers: queued-to-processing increments version even when real count stays zero; simulation uses a separate field and never completes the job; completed and failed close the source; no partial result cards before terminal completion.','ImageLab_Assessment_3_SSE_Brief.docx sections 7–9; ImageLab_Version_3_SSE_Requirements.docx.pdf sections 7–8.')

# Package the OOXML document, reusing only standard layout/theme/notes infrastructure.
TEMPLATE=ROOT/'assessment2-presentation/ImageLab_Assessment_2_Daryn_Forman.pptx'
files={}
with zipfile.ZipFile(TEMPLATE) as z:
 for name in z.namelist():
  if name.startswith(('ppt/slideMasters/','ppt/slideLayouts/','ppt/notesMasters/','ppt/theme/')):files[name]=z.read(name)
 notes_example=E.fromstring(z.read('ppt/notesSlides/notesSlide1.xml'))
 template_types=E.fromstring(z.read('[Content_Types].xml'))
# Verify that the reused layout is blank and update inherited font family to Arial.
assert E.fromstring(files['ppt/slideLayouts/slideLayout7.xml']).get('type')=='blank'
for name in list(files):
 if name.endswith('.xml'):
  files[name]=files[name].replace(b'typeface="Calibri"',b'typeface="Arial"').replace(b'typeface="Calibri Light"',b'typeface="Arial"')
def relationships(items):
 root=E.Element('Relationships',{'xmlns':REL})
 for rid,kind,target in items:E.SubElement(root,'Relationship',{'Id':rid,'Type':kind,'Target':target})
 return xml(root)
prs=E.Element(tag(P,'presentation'));el(el(prs,P,'sldMasterIdLst'),P,'sldMasterId',{'id':2147483648,tag(R,'id'):'rId1'});el(el(prs,P,'notesMasterIdLst'),P,'notesMasterId',{tag(R,'id'):'rId2'});lst=el(prs,P,'sldIdLst');prels=[('rId1',R+'/slideMaster','slideMasters/slideMaster1.xml'),('rId2',R+'/notesMaster','notesMasters/notesMaster1.xml'),('rId3',R+'/theme','theme/theme1.xml')]
for i,s in enumerate(SLIDES,1):
 rid='rId'+str(i+10);el(lst,P,'sldId',{'id':255+i,tag(R,'id'):rid});prels.append((rid,R+'/slide',f'slides/slide{i}.xml'))
 files[f'ppt/slides/slide{i}.xml']=xml(s.root)
 files[f'ppt/slides/_rels/slide{i}.xml.rels']=relationships([('rIdLayout',R+'/slideLayout','../slideLayouts/slideLayout7.xml'),('rIdNotes',R+'/notesSlide',f'../notesSlides/notesSlide{i}.xml')]+s.rels)
 notes=copy.deepcopy(notes_example)
 for shape in notes.findall('.//'+tag(P,'sp')):
  ph=shape.find('./'+tag(P,'nvSpPr')+'/'+tag(P,'nvPr')+'/'+tag(P,'ph'))
  if ph is not None and ph.get('type')=='body':
   body=shape.find(tag(P,'txBody'));body.clear();el(body,A,'bodyPr');el(body,A,'lstStyle')
   for para in s.notes.split('\n'):el(el(el(body,A,'p'),A,'r'),A,'t',text=para)
 files[f'ppt/notesSlides/notesSlide{i}.xml']=xml(notes)
 files[f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels']=relationships([('rId1',R+'/notesMaster','../notesMasters/notesMaster1.xml'),('rId2',R+'/slide',f'../slides/slide{i}.xml')])
 s.img.save(OUT/'previews'/f'slide-{i:02}.png')
el(prs,P,'sldSz',{'cx':12192000,'cy':6858000,'type':'screen16x9'});el(prs,P,'notesSz',{'cx':6858000,'cy':9144000});el(el(prs,P,'defaultTextStyle'),A,'defPPr')
files['ppt/presentation.xml']=xml(prs);files['ppt/_rels/presentation.xml.rels']=relationships(prels)
files['_rels/.rels']=relationships([('rId1',R+'/officeDocument','ppt/presentation.xml'),('rId2','http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties','docProps/core.xml'),('rId3',R+'/extended-properties','docProps/app.xml')])
CP='http://schemas.openxmlformats.org/package/2006/metadata/core-properties';DC='http://purl.org/dc/elements/1.1/';core=E.Element(tag(CP,'coreProperties'));el(core,DC,'title',text='ImageLab Assessment 3 — Server-Sent Events');el(core,DC,'creator',text='Daryn Forman');el(core,DC,'subject',text='SSE implementation, lifecycle and 18-run comparison');files['docProps/core.xml']=xml(core)
EP='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties';app=E.Element(tag(EP,'Properties'));el(app,EP,'Application',text='ImageLab presentation builder');el(app,EP,'PresentationFormat',text='On-screen Show (16:9)');el(app,EP,'Slides',text=str(len(SLIDES)));el(app,EP,'Notes',text=str(len(SLIDES)));files['docProps/app.xml']=xml(app)
for name,blob in MEDIA.items():files['ppt/media/'+name]=blob
ctype=E.Element('Types',{'xmlns':CT})
for ext,kind in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml'),('png','image/png')]:E.SubElement(ctype,'Default',{'Extension':ext,'ContentType':kind})
known={x.get('PartName').lstrip('/'):x.get('ContentType') for x in template_types if x.tag.endswith('Override')}
for name in files:
 kind=known.get(name)
 if name.startswith('ppt/slides/slide') and name.endswith('.xml'):kind='application/vnd.openxmlformats-officedocument.presentationml.slide+xml'
 if name.startswith('ppt/notesSlides/notesSlide') and name.endswith('.xml'):kind='application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml'
 if name=='ppt/presentation.xml':kind='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'
 if kind:E.SubElement(ctype,'Override',{'PartName':'/'+name,'ContentType':kind})
files['[Content_Types].xml']=xml(ctype)
name=OUT/'ImageLab_Assessment_3_Daryn_Forman.pptx'
with zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED) as z:
 for k,v in files.items():z.writestr(k,v)
# Self-contained PDF preview: rasterized at 144 dpi from identical design primitives.
SLIDES[0].img.save(OUT/'ImageLab_Assessment_3_Slide_Preview.pdf',save_all=True,append_images=[s.img for s in SLIDES[1:]],resolution=144)
contact=Image.new('RGB',(1920,math.ceil(len(SLIDES)/4)*300),(228,234,230));d=ImageDraw.Draw(contact)
for idx,s in enumerate(SLIDES):
 thumb=s.img.resize((456,257),Image.Resampling.LANCZOS);x=(idx%4)*480+12;y=(idx//4)*300+8;contact.paste(thumb,(x,y));d.text((x,y+261),str(idx+1).zfill(2)+'  '+s.title[:48],font=font(6),fill='#'+INK)
contact.save(OUT/'slide-overview.png')
notes=['# ImageLab Assessment 3 — speaker notes','','19 main slides, approximately 13–15 minutes including the live demonstration, plus 5 minutes for questions. Slides 20–24 are backup material. Spend about 20 seconds on each chart slide.','The recorded experiment is historical; foreground-browser rerun remains outstanding.','']
for i,s in enumerate(SLIDES,1):notes.extend([f'## Slide {i}: {s.title}','',s.notes,''])
(OUT/'SPEAKER_NOTES.md').write_text('\n'.join(notes))
# Requirements mapping and source provenance are supplied without cluttering slides.
(OUT/'REQUIREMENTS_COVERAGE.md').write_text('''# Requirements coverage

Source documents: ImageLab_Assessment_3_SSE_Brief.docx and ImageLab_Version_3_SSE_Requirements.docx.pdf.

| Required presentation content | Slides |
| --- | --- |
| Existing pipeline, acceptance, variants and worker independence | 2, 6–7 |
| SSE request, headers, named frames, flush and no id fields | 4; live DevTools demo on 7 |
| Committed versions, notifications, multiple observers | 5–7 |
| Reconnect, stop/resume, completed and failed lifecycle | 6–7 |
| Long-poll comparison | 3, 8, 10–18 |
| Predictions, controls and experiment matrix | 8 |
| Measurement definitions and timestamp method | 9 |
| GET graphs: repetitions, median, min–max, axes and legend | 10–12 |
| Detection-delay graphs with the same visual requirements | 13–15 |
| Summary measurement table | 16 |
| Every measured repetition in tables | 20–22 |
| Version gaps and resource trade-offs | 17 |
| Recommendation and limitations | 18 |
| Reproducibility and tests | 23 |
| Required questions and answers | 24 + speaker notes |

The live DevTools demonstration is a presentation activity, not an embedded recording.
Historical measurements used headless Firefox, prior to recent compliance and timing fixes.
Do not call the foreground-browser measurement requirement complete. Do not describe the
controlled server-stream interruption as proof of every real network-outage behavior.
''')
manifest={'slides':len(SLIDES),'main_slides':19,'appendix_slides':5,'measured_runs':len(ROWS),'source_csv_sha256':hashlib.sha256((DATA/'runs.csv').read_bytes()).hexdigest(),'source_documents':[str(ROOT.parent/'ImageLab_Assessment_3_SSE_Brief.docx'),str(ROOT.parent/'ImageLab_Version_3_SSE_Requirements.docx.pdf')],'layout_warnings':WARNINGS,'pdf_preview':'Raster slide preview generated from the same layout primitives; not a PowerPoint application export.'}
(OUT/'build-validation.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2));print(name)
