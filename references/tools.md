# 各生态扫描工具参考

原则：先 `command -v` 检测，有则用、无则跳过并在报告"未覆盖项"注明。**不要现场安装工具，不要执行被审项目的代码。**

## 已知漏洞 / 依赖扫描
| 生态 | 工具 | 命令示例 |
|---|---|---|
| 通用 | osv-scanner | `osv-scanner --lockfile=<锁文件>` 或 `osv-scanner -r <目录>` |
| 通用/容器 | trivy | `trivy fs --scanners vuln,secret <目录>` |
| Python | pip-audit | `pip-audit -r requirements.txt`（注意：不要先安装依赖） |
| Node | npm audit | `npm audit --package-lock-only` 或直接解析 package-lock 查 advisory |
| Go | govulncheck | 需要能编译，静态审核场景通常跳过 |
| Rust | cargo audit | `cargo audit --file Cargo.lock` |

无工具时的降级：从锁文件提取 包名@版本 列表，用 WebSearch/FetchURL 查 OSV（https://osv.dev）逐个核对可疑包。

## 凭据扫描
- `gitleaks detect --no-git -v <目录>`（加 `--no-git` 避免触发 hooks 风险；历史扫描需人工确认后去掉）
- `trufflehog filesystem <目录>`
- 降级：grep 模式 `AKIA[0-9A-Z]{16}`、`-----BEGIN.*PRIVATE KEY-----`、`ghp_`、`sk-`、`xox[bap]-`、`api[_-]?key\s*=`

## SAST
- `semgrep scan --config=auto <目录>`（`--config=p/security-audit` 更聚焦）
- `bandit -r <目录>`（Python）
- 降级：按 checklist 维度 5 的关键模式人工 grep

## 恶意包专项
- `guarddog pypi scan <包>` / `guarddog npm scan <包>`（检测包本身的恶意特征）
- 降级：对照维度 3 的模式 grep 全代码库

## 通用只读 grep 模式（任何环境可用）
```bash
# 网络外联与执行组合
grep -rInE '(curl|wget)[^|]*\|\s*(bash|sh)' --include='*' .
grep -rInE '(base64|b64decode|fromhex).*(exec|eval|system|popen)' .
# 敏感路径访问
grep -rInE '(\.ssh|\.aws|\.env|cookies|Login Data|wallet)' --include='*.py' --include='*.js' .
# 硬编码 IP（排除常见内网/文档段）
grep -rInoE '([0-9]{1,3}\.){3}[0-9]{1,3}' . | grep -vE '(127\.|0\.0\.0\.0|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)'
# 隐藏 Unicode
grep -rInP '[\x{200B}-\x{200D}\x{FEFF}]' .
# 超长行（>800 字符，混淆藏身处）
grep -rInE '.{800,}' --include='*.py' --include='*.js' --include='*.ts' .
# 安装钩子
grep -nE '"(pre|post)?install"' package.json
```
