"""Independently inspect actual delivery artifacts; never replace failed media."""
import argparse,json,subprocess,sys,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from backend.app.subtitles import manifest_to_srt


def check_artifact(info):
    manifest=json.loads(Path(info['manifest_path']).read_text(encoding='utf-8'))
    path=Path(info['export']['output_path'])
    details=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    video=next(s for s in details['streams'] if s['codec_type']=='video')
    audio=next(s for s in details['streams'] if s['codec_type']=='audio')
    assert (video['codec_name'],video['width'],video['height'],audio['codec_name'])==('h264',1280,720,'aac')
    duration=float(details['format']['duration']);expected=manifest['total_seconds']
    assert 30<=duration<=90 and abs(duration-expected)<=.25
    drift=abs(float(video['duration'])-float(audio['duration']))
    assert drift<=.25
    srt=path.with_suffix('.srt').read_text(encoding='utf-8')
    assert srt==manifest_to_srt(manifest)
    root=ROOT/'backend/cache'/('lessons' if manifest['language']=='en' else 'localized')/manifest['lesson_id']
    with wave.open(str(root/'combined.wav')) as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2
        rate=w.getframerate();pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
        assert abs(len(pcm)/rate-expected)<2/rate
    decoded=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar',str(rate),'-f','f32le','pipe:1']),dtype='<f4')
    # MP4 priming metadata should keep the decoded signal aligned. Report the
    # actual zero-offset correlation; it is not a human speech-quality score.
    n=min(len(pcm),len(decoded));correlation=float(np.corrcoef(pcm[:n],decoded[:n])[0,1])
    return {'path':str(path),'ffprobe':details,'srt_equal_to_pcm_cues':True,
            'subtitle_cues':srt.count('-->'),'wav_seconds':len(pcm)/rate,
            'av_stream_drift_seconds':drift,'aac_zero_offset_correlation':correlation,
            'bytes':path.stat().st_size}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();results=[];seen=set()
    for file in args.media:
        for row in json.loads(file.read_text(encoding='utf-8')):
            for language,info in row.get('languages',{}).items():
                if not info.get('export'):continue
                key=info['export']['output_path']
                if key in seen:continue
                seen.add(key);result={'case':row['case'],'language':language}
                try:result.update(check_artifact(info),status='PASS')
                except Exception as exc:result.update(status='FAIL',error=str(exc))
                results.append(result)
                print(json.dumps({k:result.get(k) for k in ('case','language','status','wav_seconds','av_stream_drift_seconds','aac_zero_offset_correlation','error')}),flush=True)
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if not results or any(r['status']=='FAIL' for r in results):raise SystemExit(1)


if __name__=='__main__':main()
