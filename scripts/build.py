"""Build a portable, offline-capable recipe site from YAML and MyST guides."""
from pathlib import Path
import html
import json
import re
import shutil
import markdown
import yaml
ROOT = Path(__file__).resolve().parents[1]

def convert_directives(source):
    lines = source.splitlines(); out=[]; i=0
    while i < len(lines):
        line=lines[i]
        m=re.match(r'^(\s*)(:{3,})\{([^}]+)\}\s*(.*)',line)
        if not m:
            out.append(line); i+=1; continue
        indent,fence,kind,title=m.groups(); body=[]; i+=1
        while i<len(lines) and lines[i].strip()!=fence:
            body.append(lines[i]); i+=1
        i+=1
        opts={}; content=[]; reading_options=True
        for b in body:
            opt=re.match(r'^:([\w-]+):\s*(.*)',b.strip())
            if opt and reading_options:opts[opt[1]]=opt[2]
            else:
                reading_options=False
                content.append(b)
        text=convert_directives('\n'.join(content))
        if kind=='figure':
            out.append(f'<figure><img loading="lazy" src="assets/{html.escape(title)}" alt="{html.escape(opts.get("alt",title))}"><figcaption>{markdown.markdown(text)}</figcaption></figure>')
        elif kind=='grid': out.append(text)
        elif kind=='grid-item-card':
            out.append(f'![{title}](assets/{opts["img-top"]})\n\n{text}' if 'img-top' in opts else text)
        else:
            label=title or {'warning':'注意','note':'说明','tip':'提示','important':'重点'}.get(kind,kind)
            inner=markdown.markdown(text,extensions=['extra','sane_lists'])
            if kind=='dropdown':out.append(f'<details class="callout"><summary>{html.escape(label)}</summary>{inner}</details>')
            else:out.append(f'<aside class="callout {kind}"><strong>{html.escape(label)}</strong>{inner}</aside>')
        out.append('')
    return '\n'.join(out)

def load_recipes():
    recipes=[]; ids=set()
    for p in sorted((ROOT/'recipes').rglob('*.yaml')):
        r=yaml.safe_load(p.read_text())
        for key in ['id','title','order','category','description','duration','guide','steps']:
            if key not in r:raise ValueError(f'{p}: missing {key}')
        if r['id'] in ids or not re.fullmatch('[a-z0-9-]+',r['id']):raise ValueError('Invalid/duplicate ID')
        ids.add(r['id'])
        if not r['steps']:raise ValueError('Recipe requires steps')
        for s in r['steps']:
            if not s.get('title') or not s.get('where'):raise ValueError('Step requires title and where')
            if set(s.get('modes',[]))-{'remote','local'}:raise ValueError('Invalid mode')
        guide=(ROOT/r['guide']).resolve()
        if not guide.is_relative_to(ROOT/'guides') or not guide.is_file():raise ValueError('Invalid guide path')
        source=guide.read_text()
        source=re.sub(r'^# .*\n','',source,count=1)
        source=re.sub(r'\]\(([\w-]+)\.md(#[^)]*)?\)',r'](#/course/\1)',source)
        r['html']=markdown.markdown(convert_directives(source),extensions=['extra','sane_lists','toc'])
        recipes.append(r)
    catalog={r['id']:r for r in recipes}
    for r in recipes:
        for field in ['prerequisite_courses','recommended_courses']:
            links=[]
            for target in r.get(field,[]):
                if target not in catalog or target==r['id']:
                    raise ValueError(f"{r['id']}: invalid course dependency {target}")
                other=catalog[target]
                links.append({'id':target,'title':other['title'],'order':other['order']})
            r[field]=links
    return sorted(recipes,key=lambda r:r['order'])

def build():
    recipes=load_recipes(); out=ROOT/'dist'; out.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'src',out,dirs_exist_ok=True)
    shutil.copytree(ROOT/'assets',out/'assets',dirs_exist_ok=True)
    shutil.copytree(ROOT/'guides',out/'guides',dirs_exist_ok=True)
    data=json.dumps(recipes,ensure_ascii=False)
    (out/'catalog.js').write_text('export default '+data+';\n')
    (out/'recipes.json').write_text(data)
    (out/'.nojekyll').touch()
    print(f'Built {len(recipes)} recipes → {out}')
if __name__=='__main__':build()
