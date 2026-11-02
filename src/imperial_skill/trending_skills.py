"""Original IMPERIAL Skill offline adapters; no network, OS control or Git mutation.
Copyright (c) 2026 Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
from __future__ import annotations
import hashlib
import ipaddress
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

class SkillBoundaryError(ValueError):
    """An input violates the least-privilege Skill boundary."""

def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def _limited_json(value: object, limit: int = 65536) -> None:
    try:
        size = len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode())
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise SkillBoundaryError('INVALID_INPUT') from exc
    if size > limit:
        raise SkillBoundaryError('INPUT_TOO_LARGE')

def desktop_ref_review(snapshot: dict, ref: str, action: str = 'observe') -> dict:
    """Inspect a snapshot-scoped accessibility ref, never perform an OS action."""
    _limited_json(snapshot)
    if not isinstance(snapshot, dict) or snapshot.get('ok') is not True:
        raise SkillBoundaryError('SNAPSHOT_NOT_TRUSTED')
    payload = snapshot.get('data')
    if not isinstance(payload, dict) or payload.get('complete') is not True:
        raise SkillBoundaryError('INCOMPLETE_SNAPSHOT')
    sid = payload.get('snapshot_id')
    if type(sid) is not str or not re.fullmatch(r'[a-zA-Z0-9]{4,32}', sid):
        raise SkillBoundaryError('INVALID_SNAPSHOT_ID')
    if type(ref) is not str or not re.fullmatch(re.escape('@' + sid) + r':e[1-9][0-9]{0,5}', ref):
        raise SkillBoundaryError('STALE_OR_INVALID_REF')
    if type(action) is not str or action not in ('observe', 'click', 'type'):
        raise SkillBoundaryError('ACTION_DENIED')
    matches = []
    visited = 0
    def walk(node: object, depth: int) -> None:
        nonlocal visited
        visited += 1
        if visited > 2048 or depth > 20 or not isinstance(node, dict):
            raise SkillBoundaryError('TREE_LIMIT_OR_SCHEMA')
        if node.get('ref_id') == ref:
            matches.append(node)
        children = node.get('children', [])
        if type(children) is not list:
            raise SkillBoundaryError('TREE_SCHEMA')
        for child in children:
            walk(child, depth+1)
    walk(payload.get('tree'), 0)
    if len(matches) != 1:
        raise SkillBoundaryError('AMBIGUOUS_OR_MISSING_REF')
    available = matches[0].get('available_actions', [])
    if type(available) is not list:
        raise SkillBoundaryError('INVALID_ACTIONS')
    if action != 'observe' and action.capitalize() not in available:
        raise SkillBoundaryError('ACTION_UNAVAILABLE')
    return {'skill':'desktop-accessibility', 'state':'LOCAL_EVALUATION',
            'ref_sha256':hashlib.sha256(ref.encode()).hexdigest(),
            'requested_action':action, 'action_executed':False,
            'execution_authorized':False, 'owner_approval_verified':False}

def model_dataset_review(training: list[dict], evaluation: list[dict]) -> dict:
    """Evaluate original-synthetic dataset provenance and split leakage, not train a model."""
    _limited_json({'train':training, 'eval':evaluation})
    if type(training) is not list or type(evaluation) is not list or not training or not evaluation:
        raise SkillBoundaryError('NONEMPTY_SPLITS_REQUIRED')
    if len(training)>1000 or len(evaluation)>1000:
        raise SkillBoundaryError('RECORD_LIMIT')
    seen=set()
    for row in training+evaluation:
        if (type(row) is not dict or set(row)!={'prompt','expected','origin'}
            or row.get('origin')!='original-synthetic'
            or any(type(row[k]) is not str or not 1<=len(row[k])<=2048
                   for k in ('prompt','expected'))):
            raise SkillBoundaryError('UNTRUSTED_OR_MALFORMED_DATASET')
        key=_digest({'prompt':row['prompt']})
        if key in seen:
            raise SkillBoundaryError('DUPLICATE_OR_SPLIT_LEAKAGE')
        seen.add(key)
    return {'skill':'model-training-lab', 'state':'LOCAL_EVALUATION',
            'training_cases':len(training),'evaluation_cases':len(evaluation),
            'dataset_sha256':_digest({'train':training,'eval':evaluation}),
            'model_trained':False,'evaluation_run':False,'gpu_required':False,
            'execution_authorized':False,'spending_usd':0}

class _PublicTextParser(HTMLParser):
    def __init__(self, tag: str):
        super().__init__(convert_charrefs=True)
        self.tag=tag
        self.depth=0
        self.results=[]
        self.buffer=[]
        self.skip_depth=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'):
            self.skip_depth+=1
        if self.skip_depth:
            return
        if tag==self.tag:
            self.depth+=1
            if self.depth==1:
                self.buffer=[]
    def handle_endtag(self, tag):
        if tag in ('script','style') and self.skip_depth:
            self.skip_depth-=1
            return
        if self.skip_depth:
            return
        if tag==self.tag and self.depth:
            self.depth-=1
            if self.depth==0:
                text=' '.join(' '.join(self.buffer).split())
                if text:
                    self.results.append(text[:512])
    def handle_data(self,data):
        if self.depth and not self.skip_depth:
            self.buffer.append(data)

def public_html_review(url: str, html: str, *, approved: bool, robots_allowed: bool,
                       tag: str='h1') -> dict:
    """Parse supplied public HTML offline; no HTTP requests or bypass techniques."""
    if approved is not True or robots_allowed is not True:
        raise SkillBoundaryError('PUBLIC_SOURCE_PERMISSION_REQUIRED')
    if type(url) is not str or type(html) is not str or len(html.encode())>65536:
        raise SkillBoundaryError('INVALID_HTML_INPUT')
    try:
        parts=urlsplit(url)
        ok=parts.scheme=='https' and bool(parts.hostname) and not parts.username and not parts.password and parts.port in (None,443)
    except ValueError as exc:
        raise SkillBoundaryError('URL_NOT_ALLOWED') from exc
    if not ok:
        raise SkillBoundaryError('URL_NOT_ALLOWED')
    host=parts.hostname
    if len(host)>253 or '.' not in host or host.endswith(('.local','.internal')):
        raise SkillBoundaryError('HOST_NOT_PUBLIC')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise SkillBoundaryError('IP_LITERAL_DENIED')
    if type(tag) is not str or tag not in ('h1','h2','p'):
        raise SkillBoundaryError('TAG_DENIED')
    parser=_PublicTextParser(tag)
    parser.feed(html)
    if len(parser.results)>100:
        raise SkillBoundaryError('RESULT_LIMIT')
    return {'skill':'authorized-web-extraction','state':'LOCAL_EVALUATION',
            'source_url':url,'source_sha256':hashlib.sha256(html.encode()).hexdigest(),
            'tag':tag,'texts':parser.results,'network_called':False,
            'browser_automation':False,'execution_authorized':False}

def worktree_status_review(porcelain: str) -> dict:
    """Parse supplied git worktree list --porcelain output, never invoke git."""
    if type(porcelain) is not str or len(porcelain.encode())>65536:
        raise SkillBoundaryError('WORKTREE_INPUT_LIMIT')
    entries=[]
    current=None
    for line in porcelain.splitlines()+['']:
        if not line:
            if current is not None:
                if 'worktree' not in current or not ('HEAD' in current or 'bare' in current):
                    raise SkillBoundaryError('WORKTREE_RECORD_INCOMPLETE')
                entries.append(current)
                current=None
            continue
        if line.startswith('worktree '):
            if current is not None:
                raise SkillBoundaryError('WORKTREE_RECORD_SEPARATOR_MISSING')
            current={'worktree':line[9:]}
        elif current is None:
            raise SkillBoundaryError('WORKTREE_RECORD_INVALID')
        elif line.startswith('HEAD ') and re.fullmatch(r'[a-f0-9]{40,64}',line[5:]):
            current['HEAD']=line[5:]
        elif line.startswith('branch refs/heads/'):
            current['branch']=line[18:]
        elif line in ('detached','bare','locked','prunable') or line.startswith(('locked ','prunable ')):
            current[line.split(' ',1)[0]]=True
        else:
            raise SkillBoundaryError('WORKTREE_UNRECOGNIZED_RECORD')
    if not entries or len(entries)>128:
        raise SkillBoundaryError('WORKTREE_COUNT_DENIED')
    if len({e['worktree'] for e in entries})!=len(entries):
        raise SkillBoundaryError('DUPLICATE_WORKTREE_PATH')
    branches=[e['branch'] for e in entries if 'branch' in e]
    if len(set(branches))!=len(branches):
        raise SkillBoundaryError('SHARED_BRANCH_DENIED')
    return {'skill':'parallel-git-worktrees','state':'LOCAL_EVALUATION',
            'worktree_count':len(entries),'branch_count':len(branches),
            'source_sha256':hashlib.sha256(porcelain.encode()).hexdigest(),
            'git_command_executed':False,'worktree_created':False,
            'execution_authorized':False}
