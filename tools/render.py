"""Regenerate the readable monthly archive from data/posts.json (Python 3.9+)."""
import hashlib
import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8', newline='\n')


def quote_text(text):
    # Escape Markdown and HTML presentation only; JSON retains the exact source.
    text = html.escape(text, quote=False)
    text = re.sub(r'([\\`*_{}\[\]()#+.!|~\-])', r'\\\1', text)
    return '\n'.join('> ' + line.rstrip() + '<br>' if line else '>' for line in text.split('\n'))


def main():
    data = json.loads((ROOT / 'data/posts.json').read_text(encoding='utf-8'))
    posts = data['posts']
    assert len({p['id'] for p in posts}) == len(posts)
    months = defaultdict(list)
    for p in posts:
        assert hashlib.sha256(p['text'].encode('utf-8')).hexdigest() == p['text_sha256']
        months[p['published_at_local'][:7]].append(p)
    manifest = {}
    for month in sorted(months, reverse=True):
        entries = sorted(months[month], key=lambda p: (p['published_at_local'], p['id']), reverse=True)
        path = ROOT / 'archive' / month[:4] / (month[5:] + '.md')
        text = f'# {month} · 李志即刻文字档案\n\n[返回总目录](../../README.md) · {len(entries)} 条 · 北京时间（UTC+8）\n\n'
        for p in entries:
            stamp = p['published_at_local'][:19].replace('T', ' ')
            kind = '原创动态' if p['type'] == 'ORIGINAL_POST' else '转发附言'
            text += f'## {stamp}\n\n[原帖]({p["url"]}) · {kind} · `{p["id"]}`\n\n'
            if p.get('edited_at'):
                text += f'原帖编辑时间：`{p["edited_at"]}`\n\n'
            text += quote_text(p['text']) + '\n\n---\n\n'
        write(path, text)
        manifest[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    newest = max(p['published_at_local'] for p in posts)[:10]
    oldest = min(p['published_at_local'] for p in posts)[:10]
    original = sum(p['type'] == 'ORIGINAL_POST' for p in posts)
    snapshot = data['snapshot']
    text = f'''# 李志即刻文字档案

散落在时间线里的文字，集中存放于此。

李志在即刻发布的动态正文存档，按时间整理，保留原文与来源链接。非官方整理项目。

本次快照共 **{len(posts)} 条**（原创动态 {original} 条、转发附言 {len(posts) - original} 条），发布时间覆盖 **{oldest} 至 {newest}**。目录与正文时间均为北京时间（UTC+8），按时间倒序排列。

## 按月阅读

| 月份 | 动态数 |
| --- | ---: |
'''
    for month in sorted(months, reverse=True):
        text += f'| [{month}](archive/{month[:4]}/{month[5:]}.md) | {len(months[month])} |\n'
    text += f'''
## 来源与收录范围

- 平台：[即刻]({data['source']['profile_url']})。
- 账号名称：`{data['source']['account_name']}`。
- 账号标识：`{data['source']['account_id']}`。
- 动态快照读取区间：`{snapshot['posts_captured_from']}` 至 `{snapshot['posts_captured_through']}`。
- 收录该次读取返回的动态正文，包括转发附言；正文内原有的引用照录，不额外展开被转发内容。
- 不收录图片、视频、评论、回复、互动统计或其他用户资料。
- 原文不改写、不转换繁简、不另拟观点标题；按动态 ID 去重，保留原有换行和表情。
- 该次动态分页已读至末页。本项目是时间点快照，不代表已删除、不可见或快照之后的新动态也已收录；原帖内容及可见性可能变化。

## 数据与校验

[data/posts.json](data/posts.json) 保存未经 Markdown 排版的正文及发布时间、原帖 ID、类型、来源链接、接口提供的编辑时间。`published_at` 与 `edited_at` 保留接口时间；`published_at_local` 使用北京时间。`edited_at` 为空表示该次响应未提供编辑时间，不据此判断是否从未编辑。

每条记录的 `text_sha256` 是原始正文 UTF-8 字节的 SHA-256，用于核对文字是否改变。月度 Markdown 仅做显示所需的转义；精确文本以 JSON 中的 `text` 字段为准。[manifest.json](manifest.json) 记录月度文件及数据文件的 SHA-256。

如需重新生成阅读目录和月度文件，安装 Python 3.9 或更新版本，在项目目录运行：

```sh
python tools/render.py
```

## 维护与权利

新增或更正应附原帖链接和可核对的来源；更正保留 Git 提交记录。请通过本仓库 Issues 提交遗漏、勘误或权利相关请求。

原文著作权归相应权利人所有。本项目用于文字记录与查阅；仓库公开不构成对收录原文的再许可。
'''
    write(ROOT / 'README.md', text)
    manifest['data/posts.json'] = hashlib.sha256((ROOT / 'data/posts.json').read_bytes()).hexdigest()
    write(ROOT / 'manifest.json', json.dumps({'algorithm': 'SHA-256', 'post_count': len(posts), 'files': manifest}, ensure_ascii=False, indent=2) + '\n')
    print(f'Rendered {len(posts)} posts across {len(months)} months')


if __name__ == '__main__':
    main()
