#!/usr/bin/env python3
"""依赖名 typosquatting 初筛：把项目的依赖名与高下载量基线表比对，输出可疑项。

重要语义（写进报告时必须遵守）：
  - 命中 = "待人工核实" 信号，不是定罪
  - 无命中 = 无信息，绝不等于安全；行为分析仍须执行
  - 本工具只能上调风险，永远不能下调

用法: check_names.py <项目目录> [基线表路径]
"""
import json
import re
import sys
from pathlib import Path

TOP_LIST = Path(__file__).parent.parent / "references" / "top_packages.txt"

# npm 官方/可信命名空间白名单（这些 scope 下的包不做相似度报警，只核对是否拼错 scope 本身）
TRUSTED_SCOPES = {
    "@types", "@angular", "@babel", "@vue", "@react", "@nestjs", "@aws-sdk",
    "@microsoft", "@google-cloud", "@mui", "@emotion", "@testing-library",
    "@rollup", "@vitejs", "@webpack", "@eslint", "@typescript-eslint",
    "@storybook", "@next", "@nuxt", "@sveltejs", "@tanstack", "@trpc",
    "@prisma", "@supabase", "@firebase", "@grpc", "@npmcli", "@node",
}

HOMOGLYPH = str.maketrans({"0": "o", "1": "l", "5": "s", "3": "e", "@": "a"})


def normalize(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"[-_.]+", "", n)          # 分隔符归一
    n = n.translate(HOMOGLYPH)             # 同形字符归一
    n = n.replace("rn", "m")               # rn↔m 视觉混淆
    return n


def levenshtein(a: str, b: str, limit: int = 3) -> int:
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        row_min = i
        for j, cb in enumerate(b, 1):
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            cur.append(v)
            row_min = min(row_min, v)
        if row_min > limit:
            return limit + 1
        prev = cur
    return prev[-1]


def load_top_list(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    eco = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("# ====="):
            eco = line.strip("# =").strip()
            sections[eco] = []
        elif line and not line.startswith("#") and eco:
            sections[eco].append(line)
    return sections


def extract_deps(target: Path) -> list[tuple[str, str]]:
    """返回 (生态系统, 包名)。覆盖 requirements.txt 与 package.json。"""
    deps = []
    for req in target.rglob("requirements*.txt"):
        if any(p in req.parts for p in ("venv", ".venv", "node_modules", "site-packages")):
            continue
        for line in req.read_text(errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            m = re.match(r"^([A-Za-z0-9._-]+)\s*([=<>!~;\[ ].*)?$", line)
            if m and not line.startswith("-"):
                deps.append(("pypi", m.group(1)))
    for pkg in target.rglob("package.json"):
        if "node_modules" in pkg.parts:
            continue
        try:
            data = json.loads(pkg.read_text(errors="replace"))
        except json.JSONDecodeError:
            continue
        for key in ("dependencies", "devDependencies", "optionalDependencies"):
            for name in data.get(key, {}):
                deps.append(("npm", name))
    return deps


def check(eco: str, name: str, top_names: list[str]) -> list[str]:
    reasons = []
    bare = name.split("/", 1)[1] if name.startswith("@") and "/" in name else name
    if name.startswith("@") and name.split("/")[0] in TRUSTED_SCOPES:
        return []
    lower_names = {t.lower() for t in top_names}
    if name.lower() in lower_names or bare.lower() in lower_names:
        return []
    norm = normalize(bare)
    norm_map = {}
    for t in top_names:
        norm_map.setdefault(normalize(t), t)
    for nt, original in norm_map.items():
        if norm == nt:
            reasons.append(f"归一化后与知名包 {original} 相同（分隔符/同形字符变换）")
        elif abs(len(norm) - len(nt)) <= 2 and levenshtein(norm, nt, 2) <= 2:
            reasons.append(f"与知名包 {original} 编辑距离 ≤2")
        elif len(nt) >= 5 and (norm.startswith(nt) or norm.endswith(nt)):
            reasons.append(f"combosquatting：含知名包名 {original} + 前后缀")
        if reasons:
            break
    return reasons


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    top_path = Path(sys.argv[2]) if len(sys.argv) > 2 else TOP_LIST
    sections = load_top_list(top_path)
    deps = extract_deps(target)
    if not deps:
        print("未找到可识别的依赖清单（requirements*.txt / package.json）")
        return 0
    print(f"共提取 {len(deps)} 个依赖名，与基线表（pypi {len(sections.get('pypi', []))} / "
          f"npm {len(sections.get('npm', []))} 个知名包）比对\n")
    hits = 0
    for eco, name in deps:
        top_names = sections.get(eco, [])
        if not top_names:
            continue
        reasons = check(eco, name, top_names)
        if reasons:
            hits += 1
            print(f"[待人工核实] {eco}: {name}")
            for r in reasons:
                print(f"    - {r}")
    print()
    if hits:
        print(f"共 {hits} 个可疑依赖名。逐个人工核实：官方 registry 页面、下载量、"
              f"发布时间、维护者、代码内容（参照 checklist 维度 2/3）。")
    else:
        print("特征库无命中。注意：这不构成安全证据——全新原创恶意包、合法包被接管投毒"
              "都查不出来，checklist 维度 1~5 的行为与代码分析仍须照常执行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
