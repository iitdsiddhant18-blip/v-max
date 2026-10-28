"""Deterministic source-known browser fixtures; not real model or voice evidence."""
import copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from backend.tests.test_visual_schema import teaching_lesson,scene_for,family_specs
from backend.app.visual_schema import VisualPlan
from backend.app.visual_planner import generic_visual
from backend.app.visual_validate import validate_plan,computed_data
from backend.app.visual_localize import validate_overlay
from backend.app.live import lesson_id
from backend.app.schema import Lesson
from backend.app.subtitles import manifest_to_srt

E=ROOT/'outputs/phase4-evidence/frames';E.mkdir(parents=True,exist_ok=True)
TIMES={'en':[(0,1),(1,2),(2,3)],'hi':[(0,1.5),(1.5,3.5),(3.5,5)],'kn':[(0,2),(2,4.5),(4.5,6)]}
WORDS={
 'hi':{'a':'प्रारंभिक अवस्था','b':'बदलाव की प्रक्रिया','c':'परिणाम','relation':'अगला संबंध','x_axis':'इनपुट मान','y_axis':'आउटपुट मान','curve':'वर्ग का संबंध','equation':'2x + 3 = 11','note':'शैक्षिक चित्रण'},
 'kn':{'a':'ಆರಂಭಿಕ ಸ್ಥಿತಿ','b':'ಬದಲಾವಣೆಯ ಪ್ರಕ್ರಿಯೆ','c':'ಫಲಿತಾಂಶ','relation':'ಮುಂದಿನ ಸಂಬಂಧ','x_axis':'ಒಳಹರಿವಿನ ಮೌಲ್ಯ','y_axis':'ಹೊರಹರಿವಿನ ಮೌಲ್ಯ','curve':'ವರ್ಗದ ಸಂಬಂಧ','equation':'2x + 3 = 11','note':'ಶೈಕ್ಷಣಿಕ ವಿವರಣೆ'},
}


def fixture(family,language):
    lesson=teaching_lesson();data=lesson.model_dump();spec=scene_for(family)
    if family=='function_plot':data['scenes'][1]['heading']='y = x² · synthetic numeric fixture'
    if family=='algorithm_state':data['scenes'][1]['heading']='Tower of Hanoi, 3 disks · synthetic algorithm fixture'
    if family=='code_trace':
        data['scenes'][1].update(type='code_walkthrough',code=spec['data']['code'])
        spec['beat_actions']=[{'beat_index':i,'op':'set_state','target_ids':['one'],'state_index':s} for i,s in enumerate((0,3,7))]
    if family=='lab_process':spec['beat_actions'][1]={'beat_index':1,'op':'pour','target_ids':['one','two']}
    lesson=Lesson.model_validate(data);identifier=lesson_id(lesson);plan=generic_visual(lesson,identifier).model_dump(mode='json')
    plan['scenes'][1]=spec;plan=validate_plan(VisualPlan.model_validate(plan),lesson,identifier)
    labels=[dict(s.display_text_en) for s in plan.scenes]
    if language!='en':
        for i,scene in enumerate(plan.scenes):
            labels[i]={key:WORDS[language].get(key,'संबंध का विवरण' if language=='hi' else 'ಸಂಬಂಧದ ವಿವರಣೆ') for key in scene.display_text_en}
        if family=='algorithm_state':labels[1].update(a='A',b='B',c='C')
    validate_overlay(plan,language,labels)
    local=lesson.model_dump();local['language']=language
    if language!='en':
        for s in local['scenes']:
            s['heading']='संबंध को समझें' if language=='hi' else 'ಸಂಬಂಧವನ್ನು ತಿಳಿಯಿರಿ'
    entries=[];cursor=0
    for i,scene in enumerate(local['scenes']):
        intervals=TIMES[language] if i==1 else [(0,1)]
        texts=([item.partition(' :: ')[2] for item in scene['items']] if i==1 else [scene['narration']])
        if language!='en':texts=[('यह पहला तथ्य है।','यह दूसरा तथ्य है।','यह तीसरा तथ्य है।')[j] if language=='hi' else ('ಇದು ಮೊದಲ ವಿವರಣೆ.','ಇದು ಎರಡನೆಯ ವಿವರಣೆ.','ಇದು ಮೂರನೆಯ ವಿವರಣೆ.')[j] for j in range(len(intervals))]
        cues=[{'text':texts[j],'label':None,'item_index':j,'item_indices':[j],'highlight_lines':[],
               'start_seconds':a,'end_seconds':b} for j,(a,b) in enumerate(intervals)]
        duration=intervals[-1][1]
        entries.append({'index':i,'start_seconds':cursor,'audio_seconds':duration,'duration_seconds':duration+.5,'cues':cues})
        cursor+=duration+.5
    result={'kind':'generated','language':language,'lesson_id':identifier,'source_lesson_id':identifier,
        'voice':'synthetic-fixture','sample_rate':8000,'pause_seconds':.5,'total_seconds':cursor,
        'audio_url':'/test-only.wav','lesson':local,'semantic_lesson':lesson.model_dump(),
        'scenes':entries,'visual_plan':plan.model_dump(mode='json'),'visual_labels':labels,
        'visual_computed':[computed_data(s) for s in plan.scenes]}
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--family');parser.add_argument('--language');args=parser.parse_args()
    results=[];external=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            for family in family_specs():
                if args.family and family!=args.family:continue
                for language in TIMES:
                    if args.language and language!=args.language:continue
                    m=fixture(family,language);entry=m['scenes'][1]
                    page=browser.new_page(viewport={'width':1280,'height':720})
                    def route(r,request):
                        from urllib.parse import urlparse
                        if '/api/lesson/timeline/' in request.url:r.fulfill(json=m)
                        elif urlparse(request.url).hostname in ('localhost','127.0.0.1'):r.continue_()
                        else:external.append(request.url);r.abort()
                    page.route('**/*',route)
                    page.goto('http://127.0.0.1:5173/render-lesson?id='+m['lesson_id'])
                    page.wait_for_function('window.__BLU_READY__===true')
                    stage=page.locator('#lesson-stage');hashes={};errors=[];timings=[];doms={};pngs={};raster=[]
                    # Deliberately out of order, no sleeps or autonomous animation waits.
                    for beat in (2,0,1,2):
                        cue=entry['cues'][beat];stamp=entry['start_seconds']+(cue['start_seconds']+cue['end_seconds'])/2
                        start=time.perf_counter();page.evaluate('(t)=>window.__BLU_SET_TIME__(t)',stamp)
                        page.wait_for_function('(t)=>Math.abs(Number(document.querySelector("#lesson-stage").dataset.time)-t)<.000002',arg=stamp)
                        group=page.locator(f'[data-visual-family="{family}"]').first
                        assert int(group.get_attribute('data-beat'))==beat
                        assert ' '.join(page.locator('[data-caption=true]').all_text_contents())==cue['text']
                        ids=group.get_attribute('data-active-ids')
                        expected=','.join(sorted({t for a in m['visual_plan']['scenes'][1]['beat_actions'] if a['beat_index']==beat for t in a['target_ids']}))
                        assert ids==expected,(family,language,beat,ids,expected)
                        png=stage.screenshot(animations='disabled');digest=hashlib.sha256(png).hexdigest()
                        dom=stage.evaluate('(e)=>e.outerHTML')
                        if beat in hashes and hashes[beat]!=digest:
                            (E/f'{family}-{language}-mismatch.png').write_bytes(png)
                            (E/'mismatch-before.svg').write_text(doms[beat],encoding='utf-8')
                            (E/'mismatch-after.svg').write_text(dom,encoding='utf-8')
                            import subprocess,numpy as np
                            def decode(data):
                                return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i','pipe:0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],input=data),dtype=np.uint8).astype(float)
                            difference=np.abs(decode(pngs[beat])-decode(png))
                            stats={'dom_identical':doms[beat]==dom,'mean_channel_error':float(difference.mean()),
                                   'maximum_channel_error':float(difference.max()),'changed_channels':int(np.count_nonzero(difference))}
                            raster.append(stats)
                            # Chromium clip-path rasterization can change edge antialiasing.
                            # Semantic DOM must be exact, with <0.005/255 mean error,
                            # <32/255 maximum error and <0.1% changed RGB channels.
                            assert stats['dom_identical'] and stats['mean_channel_error']<.005 and stats['maximum_channel_error']<32 and stats['changed_channels']<2765,(family,language,stats)
                        doms[beat]=dom
                        pngs[beat]=png
                        hashes[beat]=digest;(E/f'{family}-{language}-beat-{beat}.png').write_bytes(png)
                        outside=page.locator('#lesson-stage text').evaluate_all('''ns=>ns.map(n=>({text:n.textContent,r:n.getBoundingClientRect()})).filter(({r})=>r.left<0||r.top<0||r.right>1280.5||r.bottom>720.5)''')
                        errors.extend(outside);timings.append(time.perf_counter()-start)
                    # Cue switch never happens before its localized boundary.
                    for beat in (1,2):
                        stamp=entry['start_seconds']+entry['cues'][beat]['start_seconds']-.001
                        page.evaluate('(t)=>window.__BLU_SET_TIME__(t)',stamp)
                        page.wait_for_function('(b)=>Number(document.querySelector("[data-visual-family][data-beat]").dataset.beat)===b',arg=beat-1)
                    # Silence retains complete content, only global progress bar advances.
                    values=[]
                    for offset in (.05,.4):
                        stamp=entry['start_seconds']+entry['audio_seconds']+offset
                        page.evaluate('(t)=>window.__BLU_SET_TIME__(t)',stamp)
                        page.wait_for_function('(t)=>Math.abs(Number(document.querySelector("#lesson-stage").dataset.time)-t)<.000002',arg=stamp)
                        values.append(page.locator('[data-visual-family][data-beat]').first.evaluate('(e)=>e.outerHTML'))
                    assert values[0]==values[1],(family,language,'silence state changed')
                    srt=manifest_to_srt(m);assert '-->' in srt
                    (E/f'{family}-{language}.srt').write_text(srt,encoding='utf-8')
                    row={'family':family,'language':language,'hashes':hashes,'raster_tolerance':raster,'overflow':errors,'mean_capture_seconds':sum(timings)/len(timings)}
                    results.append(row);page.close();print(json.dumps(row,ensure_ascii=False),flush=True)
            # Narrow real player scales canonical SVG; readable local captions stay outside.
            page=browser.new_page(viewport={'width':390,'height':844});m=fixture('concept_map','kn')
            page.route('**/api/lesson/timeline/*',lambda r:r.fulfill(json=m))
            page.goto('http://127.0.0.1:5173/lesson?id='+m['lesson_id'])
            page.locator('#lesson-stage').wait_for();page.screenshot(path=str(E/'narrow-390.png'),full_page=True)
            width=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');assert width['scroll']<=width['width']
            print('NARROW',width,flush=True)
        finally:browser.close()
    (E/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    failures=[r for r in results if r['overflow']]
    print('EXTERNAL REQUESTS',external,'OVERFLOW CASES',len(failures),flush=True)
    assert not external and not failures,failures
    print('51 family/language synthetic render fixtures: PASS',flush=True)


if __name__=='__main__':main()
