"""Public GitHub profile metrics. Python 3.11+, no third-party dependencies."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
from html import escape
import json
import logging
import os
from pathlib import Path
from string import Template
import time
import tomllib
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)

class API:
    def __init__(self):
        self.token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    def request(self, path, body=None):
        url = path if path.startswith('https://api.github.com/') else 'https://api.github.com/' + path
        if not url.startswith('https://api.github.com/'):
            raise ValueError('Unexpected API host')
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Samir-profile', 'X-GitHub-Api-Version': '2022-11-28'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers, data=json.dumps(body).encode() if body else None)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code not in (500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f'GitHub API returned HTTP {exc.code}') from None
                time.sleep(2 ** attempt)
    def pages(self, path):
        result = []
        for page in range(1, 1001):
            batch = self.request(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
            result.extend(batch)
            if len(batch) < 100:
                return result
        raise RuntimeError('Pagination safety limit reached')

def collect(config):
    api = API()
    user = config['username']
    profile = api.request(f'users/{user}')
    repos = [r for r in api.pages(f'users/{user}/repos?type=owner') if not r['private']]
    originals = [r for r in repos if not r['fork']]
    languages = Counter()
    for repo in originals:
        languages.update(api.request(f'repos/{user}/{repo["name"]}/languages'))
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=365)
    commits = api.request(f'search/commits?q=author:{user}+is:public+committer-date:{since.date()}..{now.date()}&per_page=1')
    data = dict(username=user, updated=now.isoformat(), repositories=len(repos), stars=sum(r['stargazers_count'] for r in originals), followers=profile['followers'], commits=None if commits.get('incomplete_results') else commits['total_count'], languages=dict(languages.most_common(6)), popular=[dict(name=r['name'], stars=r['stargazers_count'], url=r['html_url']) for r in sorted(originals, key=lambda r:(-r['stargazers_count'], r['name'].lower()))[:3]], contributions=None, days=[])
    if api.token:
        try:
            query = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){restrictedContributionsCount contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
            response = api.request('graphql', {'query':query, 'variables':{'login':user,'from':since.isoformat(),'to':now.isoformat()}})
            if response.get('errors'):
                raise RuntimeError('GraphQL contributions unavailable')
            if response['data']['user']['contributionsCollection']['restrictedContributionsCount']:
                raise RuntimeError('Restricted contributions are excluded')
            days = [d for w in response['data']['user']['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']]
            # A public repository token must not expose restricted contribution counts.
            data['days'] = days
            data['contributions'] = sum(d['contributionCount'] for d in days)
        except (RuntimeError, KeyError, TypeError):
            LOG.warning('Contribution calendar unavailable; explicitly displaying N/A')
    return data

def text(x, y, value, css=''):
    return f'<text x="{x}" y="{y}" class="{css}">{escape(str(value))}</text>'

def render(config, data, theme, stale=False):
    palette = dict(background='#161b22',text='#c9d1d9',muted='#8492a5',accent='#7ee787',key='#ffa657',value='#a5d6ff') if theme=='dark' else dict(background='#f6f8fa',text='#24292f',muted='#57606a',accent='#116329',key='#953800',value='#0550ae')
    out=[]
    # Embedded local portrait keeps the SVG self-contained on GitHub.
    import base64
    portrait = base64.b64encode((ROOT/'assets/portrait.png').read_bytes()).decode('ascii')
    # Extract glyph luminance as alpha, then color it for the selected theme.
    out.append(f'<defs><filter id="portrait-ink" color-interpolation-filters="sRGB"><feColorMatrix in="SourceGraphic" type="matrix" result="mask" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  .4252 1.4304 .1444 0 -.22"/><feFlood flood-color="{palette["text"]}"/><feComposite operator="in" in2="mask"/></filter></defs>')
    out.append(f'<image href="data:image/png;base64,{portrait}" x="20" y="20" width="330" height="380" preserveAspectRatio="xMidYMid meet" filter="url(#portrait-ink)"/>')
    out += [text(48,420,'samir@github','accent'),text(48,442,'build • test • document • repeat','muted')]
    for i,color in enumerate(['#f85149','#ffa657','#e3b341','#7ee787','#79c0ff','#d2a8ff','#c9d1d9']):
        out.append(f'<rect x="{48+i*33}" y="462" width="33" height="17" fill="{color}"/>')
    if data['days']:
        for i,day in enumerate(data['days'][-84:]):
            opacity=.12 if day['contributionCount']==0 else min(1,.35+day['contributionCount']/15)
            out.append(f'<rect x="{48+(i//7)*19}" y="{505+(i%7)*9}" width="15" height="6" rx="1" fill="{palette["accent"]}" opacity="{opacity}"><title>{escape(day["date"])}: {day["contributionCount"]}</title></rect>')
        out.append(text(48,585,'public activity / last 12 weeks','muted'))
    def section(y,label):
        out.append(text(380,y,label,'heading'))
        out.append(text(380,y+17,'─'*65,'muted'))
    def row(y,label,value):
        out.append(f'<text x="380" y="{y}"><tspan class="muted">. </tspan><tspan class="key">{escape(label)}</tspan><tspan class="muted"> {"."*max(2,23-len(label))} </tspan><tspan class="value">{escape(str(value))}</tspan></text>')
    section(31,'samir@gedeon ~ / about')
    for y,label,value in [
        (76,'Name',config['name']),
        (98,'Focus','Web development / Junior full stack'),
        (120,'Education','Software Engineering student'),
        (142,'University','Universidade de Vassouras'),
        (164,'Work','IT / City of Miguel Pereira'),
        (186,'Location','Rio de Janeiro, Brazil'),
        (220,'Languages','Java, Python, JavaScript'),
        (242,'Web','HTML, CSS / Spring Boot, Django, FastAPI'),
        (264,'Tools','Git, Maven / automated tests'),
    ]: row(y,label,value)
    section(303,'Contact')
    row(346,'GitHub','github.com/'+config['username'])
    section(387,'GitHub stats / public data')
    row(430,'Repositories',f'{data["repositories"]} public / {data["stars"]} stars (non-forks)')
    row(452,'Commits / 365d','N/A' if data['commits'] is None else f'{data["commits"]:,} indexed public commits')
    row(474,'Followers',data['followers'])
    row(496,'Contributions / 365d',data['contributions'] if data['contributions'] is not None else 'N/A')
    total=sum(data['languages'].values())
    row(518,'Code / top bytes',' / '.join(f'{k} {v/total:.0%}' for k,v in list(data['languages'].items())[:3]) if total else 'N/A')
    row(540,'Lines added / removed','N/A / not measured')
    out += [text(380,581,'Metrics scope & project links: README / docs/SETUP.md','muted'),text(380,600,('CACHED · ' if stale else 'UPDATED · ')+data['updated'][:19].replace('T',' ')+' UTC','muted')]
    return Template((ROOT/'templates/card.svg').read_text()).substitute(**palette,title=escape(config['name']+' | GitHub metrics'),description='Terminal profile with a custom character-style portrait and real public GitHub metrics.',body='\n'.join(out))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    config=tomllib.loads((ROOT/'profile.toml').read_text())
    cache=ROOT/'cache/stats.json'
    stale=args.offline
    try:
        if args.offline:
            raise RuntimeError('Offline mode')
        data=collect(config)
        cache.write_text(json.dumps(data,indent=2)+'\n')
    except Exception:
        if not cache.exists():
            raise
        LOG.warning('Using last complete public snapshot',exc_info=True)
        data=json.loads(cache.read_text())
        if data['username'] != config['username']:
            raise RuntimeError('Cache belongs to another user')
        stale=True
    for theme in ('dark','light'):
        (ROOT/f'{theme}_mode.svg').write_text(render(config,data,theme,stale))
    LOG.info('Generated both themes (%s)', 'cached' if stale else 'fresh')

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s: %(message)s')
    main()
