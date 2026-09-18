"""Render the score as an audio-synchronised, voice-coloured piano roll."""
from pathlib import Path
import json,base64,subprocess,sys,math
from PIL import Image,ImageDraw,ImageFont
SOURCE=Path(sys.argv[1]).resolve();OUT=SOURCE.parent
source=json.loads(SOURCE.read_text());d=source['playback'];ev=d['events'];cfg=source['render']['video']
fontpath=next((p for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),None)
serif=next((p for p in ['/System/Library/Fonts/Supplemental/Georgia.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'] if Path(p).exists()),fontpath)
def font(n,head=False):return ImageFont.truetype(serif if head else fontpath,n)
W,H=cfg['width'],cfg['height']
assert (W,H)==(1440,900), 'Video layout currently supports 1440x900'
BG='#10171f';GRID='#26333d';TEXT='#edf1f1';MUTED='#97a9b7'
LOW,HIGH=38,79
LEFT,RIGHT,TOP,BOTTOM=85,1395,246,732
SPAN=cfg['windowSeconds']

def render(t):
 im=Image.new('RGB',(W,H),BG);dr=ImageDraw.Draw(im)
 dr.text((46,27),d['title'].upper(),font=font(35,True),fill=TEXT)
 dr.text((48,79),d['subtitle']+' / '+source['version'],font=font(19),fill=MUTED)
 # persistent legend, explicit carrier and intervals
 for v,name in enumerate(d['voices']):
  x=49+v*345
  dr.rounded_rectangle((x,122,x+13,135),radius=3,fill=d['colors'][v])
  dr.text((x+23,115),name,font=font(20),fill=TEXT)
  label=['Cantus firmus: mm. 8.3–28.2','Countervoice','Cantus firmus: mm. 36.3–44.2','Foundation'][v]
  dr.text((x,146),label,font=font(15),fill=MUTED)
 sec=next(s for s in reversed(d['sections']) if s['time']<=t)
 dr.text((49,193),sec['name'],font=font(20),fill=TEXT)
 dr.text((815,196),'White outline = cantus firmus  ·  Pitch rises upward',font=font(16),fill=MUTED)
 start=t-3.6;scale=(RIGHT-LEFT)/SPAN
 def yy(p):return BOTTOM-(p-LOW+1)*(BOTTOM-TOP)/(HIGH-LOW+1)
 for p in range(LOW,HIGH+1):
  y=yy(p);row=(BOTTOM-TOP)/(HIGH-LOW+1)
  if p%12 in [1,3,6,8,10]:dr.rectangle((LEFT,y,RIGHT,y+row),fill='#141f29')
  if p%12==0:
   dr.line((LEFT,y+row/2,RIGHT,y+row/2),fill='#33414c')
   dr.text((42,y-2),'C'+str(p//12-1),font=font(14),fill=MUTED)
 for i,bt in enumerate(d['barTimes']):
  x=LEFT+(bt-start)*scale
  if LEFT<=x<=RIGHT:
   dr.line((x,TOP,x,BOTTOM),fill=GRID,width=1)
   dr.text((x+5,TOP-21),str(i+1),font=font(13),fill=MUTED)
 for e in ev:
  x=LEFT+(e['time']-start)*scale;xe=x+e['seconds']*scale
  if min(RIGHT,xe-1.5)<=max(LEFT,x):continue
  y=yy(e['pitch'])+1;h=(BOTTOM-TOP)/(HIGH-LOW+1)-2
  col=d['colors'][e['voice']]
  dr.rounded_rectangle((max(LEFT,x),y,min(RIGHT,xe-1.5),y+h),radius=2,fill=col,outline=TEXT if e['cf'] else None,width=1)
  if e['time']<=t<e['time']+e['seconds']:
   dr.rectangle((max(LEFT,x),y,min(RIGHT,xe-1.5),y+h),outline=TEXT if e['cf'] else col,width=2)
 play=LEFT+3.6*scale
 dr.line((play,TOP-7,play,BOTTOM+9),fill='#f6f1d8',width=2)
 dr.polygon([(play-5,TOP-9),(play+5,TOP-9),(play,TOP-2)],fill='#f6f1d8')
 dr.text((49,767),f'{int(t)//60}:{int(t)%60:02}  /  {int(d["duration"]+3)//60}:{int(d["duration"]+3)%60:02}',font=font(20),fill=TEXT)
 dr.text((297,770),'G major   ·   3/4   ·   Andante, con moto',font=font(17),fill=MUTED)
 barno=min(48,sum(bt<=t for bt in d['barTimes']))
 dr.text((1220,770),f'Measure {barno:02}',font=font(17),fill=MUTED)
 for e in ev:
  x=49+e['time']/d['duration']*1344;y=829+(78-e['pitch'])*.85
  dr.rectangle((x,y,x+max(2,e['seconds']/d['duration']*1344),y+2),fill=d['colors'][e['voice']])
 dr.line((49+t/d['duration']*1344,819,49+t/d['duration']*1344,876),fill=TEXT,width=2)
 return im
render(28).save(OUT/'composition.png')
if '--video' in sys.argv:
 fps=cfg['fps'];length=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(OUT/'composition.mp3')]))
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-i',str(OUT/'composition.mp3'),'-c:v','libx264','-preset','fast','-crf',str(cfg['crf']),'-pix_fmt','yuv420p','-c:a','aac','-b:a',cfg['audioBitrate'],'-t',str(length),'-movflags','+faststart',str(OUT/'composition.mp4')]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(math.ceil(length*fps)):
  p.stdin.write(render(i/fps).tobytes())
  if i%(fps*20)==0:print('Video seconds',i//fps,flush=True)
 p.stdin.close();assert p.wait()==0
print('Visualization built.')
