"""Read-only preflight for an ad run. See PIPELINE_INPUT_FORMAT.md."""
import json
import re
from pathlib import Path

DEVICES = {'open_palm', 'eye_level_turn', 'cheek_match', 'mirror_reflection',
           'fabric_comparison', 'size_comparison', 'unbox_reveal', 'table_flourish',
           'fan_or_stack', 'collarbone_cradle'}
FORBIDDEN_CAMERA = re.compile(r'\b(?:zoom\s*(?:in|out)|pull[ -]?back|orbit|macro|extreme close[ -]?up|rapid|fast|whip|puls(?:e|ing)|dolly|pan)\b', re.I)

def validate_run(run_dir):
    root = Path(run_dir).resolve()
    errors = []
    manifest = root / 'pipeline_products.json'
    if not manifest.is_file():
        return ['Missing pipeline_products.json; see PIPELINE_INPUT_FORMAT.md']
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        products = data['products']
        if not isinstance(products, list) or not products:
            raise ValueError('products must be a nonempty list')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f'Invalid product manifest: {exc}']
    ids, devices = set(), set()
    for p in products:
        if not isinstance(p, dict):
            errors.append('Each product must be an object'); continue
        pid = p.get('id')
        if not isinstance(pid, str) or not pid.strip() or pid in ids:
            errors.append(f'Missing or duplicate product id: {pid!r}'); continue
        ids.add(pid)
        device = p.get('show_device')
        if device not in DEVICES or device in devices:
            errors.append(f'{pid}: show_device must be a unique approved device')
        devices.add(device)
        if not isinstance(p.get('opens'), bool):
            errors.append(f'{pid}: opens must be true or false')
        if p.get('opens') is True:
            for key in ('opening_action', 'closed_spec', 'open_spec'):
                if not isinstance(p.get(key), str) or not p[key].strip():
                    errors.append(f'{pid}: missing {key}')
            for key in ('closed_reference', 'open_reference'):
                value = p.get(key)
                if not isinstance(value, str) or not value.strip() or not (root / value).is_file():
                    errors.append(f'{pid}: {key} must point to an existing reference file')
            if p.get('references_approved') is not True:
                errors.append(f'{pid}: closed and open references require approval')
    paths = sorted((root / '04_actions').glob('*.json'))
    if not paths: errors.append('No action files found')
    covered, application_count = set(), 0
    for path in paths:
        try:
            action = json.loads(path.read_text(encoding='utf-8'))
            plan = action['plan']
            steps = plan['steps']
            if not isinstance(steps, list) or not steps: raise ValueError('steps must be a nonempty list')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path.name}: invalid action: {exc}'); continue
        pid = action.get('product_id')
        if pid is not None:
            if pid not in ids: errors.append(f'{path.name}: unknown product_id {pid!r}')
            else: covered.add(pid)
        beat = action.get('beat_type')
        if beat == 'apply': application_count += 1
        if beat in ('show', 'apply') and pid is not None and pid in ids:
            product = next(p for p in products if isinstance(p, dict) and p.get('id') == pid)
            if action.get('show_device') != product.get('show_device'):
                errors.append(f'{path.name}: show_device must match product manifest')
            if product.get('opens') and action.get('opens_on_camera') is not True:
                errors.append(f'{path.name}: opening product must open on camera')
            if product.get('opens') and not any(isinstance(s, dict) and s.get('opening_step') is True and isinstance(s.get('what_happens'), str) and s['what_happens'].strip() for s in steps):
                errors.append(f'{path.name}: missing opening_step with an action')
        elif beat == 'apply':
            errors.append(f'{path.name}: apply beat requires product_id')
        elif beat == 'show' and pid is None and action.get('product_showcase') is not False:
            errors.append(f'{path.name}: show beat requires product_id or product_showcase=false')
        for step in steps:
            if not isinstance(step, dict):
                errors.append(f'{path.name}: invalid step'); continue
            cam = str(step.get('camera', '')).lower()
            if cam != 'locked_off' and not ('locked off' in cam and '10 percent' in cam):
                errors.append(f'{path.name}: every step camera must be locked_off or nearly locked off with at most a 10 percent push-in')
        # Prevent conflicting camera instructions anywhere in the free-text plan.
        for text in _strings(plan):
            if FORBIDDEN_CAMERA.search(text):
                errors.append(f'{path.name}: conflicting camera/motion wording: {text[:120]}'); break
    for pid in sorted(ids - covered): errors.append(f'{pid}: no action covers this product')
    if application_count != 1: errors.append(f'Exactly one apply beat required; found {application_count}')
    return errors

def _strings(value):
    if isinstance(value, str): yield value
    elif isinstance(value, dict):
        for v in value.values(): yield from _strings(v)
    elif isinstance(value, list):
        for v in value: yield from _strings(v)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2: sys.exit('Usage: python3 pipeline_preflight.py RUN_FOLDER')
    problems = validate_run(sys.argv[1])
    print('\n'.join(problems) if problems else 'Preflight passed; visual review is still required.')
    sys.exit(bool(problems))
