# Typosquatting / 恶意包名特征库使用规则

## 定位（最重要）

本特征库是**信号增强器，不是安全闸门**：

- 命中黑名单 → 可以直接定 Critical
- 相似度命中 → "待人工核实"信号，标 Medium
- **无命中 = 无信息，不是安全结论。** 报告结论中禁止出现"不在黑名单/基线表中，因此安全"这类表述
- 特征库结果在报告中单独成节；无论结果如何，checklist 维度 2/3 的行为分析都必须执行

## 文件

- `top_packages.txt`：PyPI/npm 各 Top 300 高下载量包（ecosyste.ms 按下载量排序）。被仿冒的目标几乎都在此列
- `malicious_known.md`：历史真实投毒事件包名，命中即 Critical
- `../scripts/check_names.py`：自动初筛，提取依赖名 → 归一化 → 编辑距离/combosquat 比对

## 更新基线表

```bash
for eco in pypi.org npmjs.org; do
  short=${eco%%.*}
  for p in 1 2 3; do
    curl -s "https://packages.ecosyste.ms/api/v1/registries/$eco/packages?sort=downloads&order=desc&per_page=100&page=$p" \
      | python3 -c "import json,sys; [print(x['name']) for x in json.load(sys.stdin)]"
  done > /tmp/top_$short.txt
done
# 然后按现有格式重写 references/top_packages.txt
```

## 判定规则（check_names.py 已实现）

1. **编辑距离 ≤ 2**：`requets` → `requests`
2. **分隔符变换**：`-`/`_`/`.` 增删互换后相同：`python_dateutil` → `python-dateutil`
3. **同形字符归一**：`0↔o`、`1↔l`、`5↔s`、`3↔e`、`rn↔m`：`jeIlyfish` → `jellyfish`
4. **combosquatting**：知名包名 + 通用前后缀：`requests-security`、`lodash2`

## 相似度命中后的人工核实步骤

1. 打开官方 registry 页面（pypi.org/project/<名> / npmjs.com/package/<名>）
2. 看周下载量（<1000 且名字像知名包 → 高度可疑）、首次发布时间（近期新建 → 可疑）、维护者历史
3. 拉取包内容做 checklist 维度 2/3 的静态分析
4. 仍不确定 → 报告标 Medium 并写"待人工确认"

## 本库覆盖不到的情形（必须在报告中如实承认）

- 全新注册的原创恶意包（名字不碰瓷任何人）
- 合法包维护者账号被接管后的投毒版本（名字完全正常）
- 依赖混淆（dependency confusion）：公网包名与内网私有包同名 → 检查是否有同名包同时存在于公网 registry 且版本号异常高
- Go/Rust/Java 等生态（基线表目前只有 pypi/npm，可按同样方法扩展）
