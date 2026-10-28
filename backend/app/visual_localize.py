"""Translate display overlays only. Immutable visual topology remains English canonical."""
import hashlib,json,re
from pathlib import Path
from .translated_lesson import has_script,clean_text


def protected_visual_text(text):
    if re.fullmatch(r'[ABCxyzntPFVm0-9+*/=²³() .−–_-]+|N|kg|m/s|m/s²|V|Ω|Alice|Bob|Python|DNA|RNA|ATP|ADP|pH',text):return True
    if text.startswith('y = '):
        from .algorithm_trace import bounded_math_value
        try:
            bounded_math_value(text[4:],.75)
            return True
        except (ValueError,TypeError):return False
    formula=text.translate(str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789'))
    if re.fullmatch(r'(?:[A-Z][a-z]?[0-9]{0,2}){1,8}',formula):
        from .visual_schema import ELEMENTS
        return all(atom in ELEMENTS for atom in re.findall(r'[A-Z][a-z]?',formula))
    return False


def validate_overlay(plan,language,overlay):
    if language not in ('en','hi','kn'):raise ValueError('Unsupported visual language')
    if len(overlay)!=len(plan.scenes):raise ValueError('Visual label scene count mismatch')
    for scene,labels in zip(plan.scenes,overlay):
        if set(labels)!=set(scene.display_text_en):raise ValueError('Missing/extra visual labels')
        for key,text in labels.items():
            if not isinstance(text,str) or not text.strip() or len(text)>240 or re.search('<|>|https?://',text):raise ValueError('Unsafe/empty localized visual text')
            original=scene.display_text_en[key]
            # Only symbols, units, proper code tokens are exempt. Words need script.
            protected=protected_visual_text(original)
            if language!='en' and not protected and not has_script(text,language):raise ValueError('English-only placeholder in localized visual: '+key)
    return overlay


def localize_visual(plan,language,*,translate_many=None,root=None):
    english=[dict(s.display_text_en) for s in plan.scenes]
    if language=='en':return validate_overlay(plan,language,english)
    from .visual_cache import visual_id,canonical,VISUAL_ROOT
    root=root or VISUAL_ROOT
    file=root/plan.source_lesson_id/(visual_id(plan)+'.'+language+'.json')
    if file.exists():
        try:
            stored=json.loads(file.read_text(encoding='utf-8'))
            overlay=validate_overlay(plan,language,stored['labels'])
            digest=hashlib.sha256(canonical(overlay).encode()).hexdigest()
            if stored['digest']==digest:return overlay
        except (ValueError,KeyError,TypeError):pass
    translator=None
    if translate_many is None:
        from .indic_translator import LocalIndicTranslator
        translator=LocalIndicTranslator();translate_many=translator.translate_many
    phrases=[]; positions=[]; overlay=[dict(s) for s in english]
    for i,labels in enumerate(english):
        for key,text in labels.items():
            if not protected_visual_text(text):
                # A prose label such as y-axis is not subtraction/code. The
                # legacy narration glossary protects identifier-identifier.
                phrase=re.sub(r'(?<=[A-Za-z])[-–](?=[A-Za-z])',' ',text)
                phrases.append(phrase);positions.append((i,key))
    try:
        translated=translate_many(phrases,language)
    finally:
        if translator is not None:translator.unload()
    if len(translated)!=len(phrases):raise ValueError('Visual translation count mismatch')
    for (i,key),text in zip(positions,translated):overlay[i][key]=clean_text(text)
    validate_overlay(plan,language,overlay)
    file.parent.mkdir(parents=True,exist_ok=True)
    from .visual_cache import canonical
    import os,tempfile
    fd,temp=tempfile.mkstemp(dir=file.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(canonical({'labels':overlay,'digest':hashlib.sha256(canonical(overlay).encode()).hexdigest()}))
        os.replace(temp,file)
    finally:
        if Path(temp).exists():Path(temp).unlink()
    return overlay
