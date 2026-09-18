"""Blind audio review through Vertex; credentials remain in memory only."""
import argparse, base64, datetime, hashlib, json, os, subprocess, tempfile
from pathlib import Path
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parents[1]
PROMPT = '''Analyze this audio recording independently, using only what you can hear. You have no title, composer, score, or description. Do not assume it is famous or identify a composer as fact.
Return a critical report covering:
1. Likely instruments, broad genre, historical style or period, and texture; express uncertainty and plausible alternatives.
2. What the music actually does over time, with approximate timestamps for distinctive changes, phrases and the ending.
3. Musical strengths and weaknesses: melodic development, independence of parts, harmony, dissonance, pacing, cadences, and performance naturalness. Do not invent exact pitches, intervals or rule violations that you cannot reliably hear.
4. Whether it sounds like a convincing stylistic composition, a generic exercise, or something else, and why. Be candid; neither praise nor criticism is required.
Distinguish audible observations from speculation. Acknowledge what cannot be assessed reliably from this audio.'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--credentials',required=True)
    ap.add_argument('--model',default='gemini-2.5-pro')
    ap.add_argument('--opening', action='store_true')
    a=ap.parse_args()
    try:
        creds=service_account.Credentials.from_service_account_file(a.credentials, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(Request())
        src=ROOT/'generated/v003/composition.mp3'
        audio=subprocess.run(['ffmpeg','-v','error','-i',str(src),'-map_metadata','-1','-c:a','copy','-f','mp3','pipe:1'],capture_output=True,check=True).stdout
        prompt = PROMPT
        mime = 'audio/mpeg'
        suffix = ''
        if a.opening:
            with tempfile.TemporaryDirectory() as td:
                wav=Path(td)/'clip.wav'
                subprocess.run(['ffmpeg','-v','error','-i',str(src),'-t','20','-map_metadata','-1','-ar','24000','-ac','1',str(wav)],capture_output=True,check=True)
                audio=wav.read_bytes()
            mime='audio/wav'
            suffix='-opening'
            prompt='This is a 20-second audio excerpt. Describe only what is audible: instrument, probable musical style with uncertainty, whether the opening starts with one melodic line or several simultaneous parts, and how the texture changes during these 20 seconds. Do not extrapolate beyond this excerpt. Keep the answer under 250 words. Separate observation from conjecture.'
        body={'contents':[{'role':'user','parts':[{'inlineData':{'mimeType':mime,'data':base64.b64encode(audio).decode()}},{'text':prompt}]}], 'generationConfig':{'temperature':0.2,'maxOutputTokens':8192}}
        url=f'https://aiplatform.googleapis.com/v1/projects/{creds.project_id}/locations/global/publishers/google/models/{a.model}:generateContent'
        r=requests.post(url,headers={'Authorization':f'Bearer {creds.token}'},json=body,timeout=240)
        if r.status_code!=200:
            try: status=r.json().get('error',{}).get('status','unknown')
            except Exception: status='unparsed'
            print(json.dumps({'http_status':r.status_code,'status':status,'model':a.model})); return
        result=r.json()
        parts=[p.get('text','') for c in result.get('candidates',[]) for p in c.get('content',{}).get('parts',[]) if not p.get('thought')]
        report='\n'.join(parts)
        # Never serialize credentials, headers, request body, or server errors.
        for secret in [creds.token,creds.service_account_email,creds.project_id]:
            if secret: report=report.replace(secret,'[REDACTED]')
        out=ROOT/'analysis/audio-reviews'; out.mkdir(exist_ok=True)
        data={'model_requested':a.model,'model_returned':result.get('modelVersion'),'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'submitted_audio_sha256':hashlib.sha256(audio).hexdigest(),'metadata_removed':True,'prompt':prompt,'report':report,'usage':result.get('usageMetadata'),'finish_reasons':[c.get('finishReason') for c in result.get('candidates',[])]}
        (out/f'{a.model}{suffix}.json').write_text(json.dumps(data,indent=2)+'\n')
        (out/f'{a.model}{suffix}.md').write_text(f'# Blind audio assessment: {a.model}\n\n'+report+'\n')
        print(json.dumps({'success':True,'model':a.model,'report':str(out/f'{a.model}{suffix}.md'),'finish_reasons':data['finish_reasons']}))
    except Exception as e:
        print(json.dumps({'success':False,'error_type':type(e).__name__}))

if __name__=='__main__': main()
