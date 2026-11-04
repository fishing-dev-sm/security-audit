# 安全审核完整清单（七个维度）

## 1. 依赖与供应链
- [ ] 已知漏洞扫描：对照 CVE/GHSA/OSV（pip-audit / npm audit / osv-scanner / trivy）
- [ ] 依赖名与知名包相似（typosquatting）：跑 `scripts/check_names.py`，规则与基线表见 `references/typosquatting.md`、`references/malicious_known.md`；**无命中 ≠ 安全，剩余各项照常执行**
- [ ] 可疑包特征：发布时间极短、下载量异常低、维护者近期变更、无仓库链接
- [ ] 锁文件与清单文件一致性；锁文件中是否混入不在清单里的包
- [ ] 传递依赖中的深层可疑包
- [ ] 依赖源是否被改指向非官方 registry/镜像

## 2. 安装与构建流程（投毒重灾区）
- [ ] `package.json`：`preinstall` / `install` / `postinstall` 脚本内容
- [ ] `setup.py` / `pyproject.toml`：`cmdclass`、自定义 build 命令
- [ ] `Makefile`、`Dockerfile`、`docker-compose.yml`：`curl | sh`、下载执行、外传数据
- [ ] CI 配置（`.github/workflows/`、`.gitlab-ci.yml`）：可疑 action、密钥外传、拉取外部脚本
- [ ] 无源码对应的预编译二进制（.so/.dll/.exe/.bin）；加壳/加UPX特征
- [ ] git hooks 目录（`.githooks/`、husky 配置）

## 3. 代码级恶意行为模式
- [ ] 网络外联：硬编码 IP/可疑域名、向非官方端点 POST 数据、DNS 请求携带数据
- [ ] 敏感信息窃取：读 `~/.ssh`、浏览器 cookie/密码库、`.env`、环境变量、加密钱包文件路径
- [ ] 混淆：base64/hex/zlib 解码后 exec/eval、动态 `__import__`/`require(变量)`、单字母变量长函数
- [ ] 持久化：写 crontab、systemd unit、shell rc（.bashrc/.zshrc）、启动项、IDE 配置
- [ ] 反分析：检测 VM/调试器/沙箱后改变行为、延时触发
- [ ] 键盘记录、截屏、剪贴板读取 API 的可疑使用

## 4. 凭据与敏感信息泄露
- [ ] 硬编码 API key / token / 私钥 / 密码（gitleaks / trufflehog 模式）
- [ ] git 历史中已删除但仍存在的密钥：`git log -p` 抽查、扫描全历史
- [ ] 误提交：`.env`、数据库 dump、证书文件（.pem/.key/.p12）、IDE 配置中的 token

## 5. 代码质量型漏洞（SAST）
- [ ] 注入：命令注入（shell=True、字符串拼命令）、SQL 拼接、模板注入、XPath/LDAP
- [ ] 不安全反序列化：`pickle.loads`、`yaml.load`（非 SafeLoader）、`ObjectInputStream`
- [ ] 路径穿越：`os.path.join` 拼用户输入、解压未校验路径（zip slip）
- [ ] SSRF：服务端请求用户可控 URL 且无白名单
- [ ] 弱加密：MD5/SHA1 用于口令、ECB 模式、硬编码密钥、`random` 用于安全用途
- [ ] 其他：开放重定向、CORS 通配、调试模式硬编码开启、绑定 0.0.0.0 的敏感服务

## 6. 项目健康度与人为风险
- [ ] 维护者数量与活跃度；是否单人维护且长期断更后突然发版（账号接管信号）
- [ ] star/fork 与项目质量是否匹配（刷量信号）
- [ ] issue/PR 中是否有被无视或删除的安全报告
- [ ] 仓库是否从原地址迁移/改名；作者历史项目记录
- [ ] 许可证：是否存在、是否与宣称一致（合规项，顺带报告）

## 7. AI 攻击面（详见 ai-attacks.md）
- [ ] AI 工具配置文件中的注入指令
- [ ] README/文档/注释中的隐藏指令（零宽字符、白字、ANSI 转义、超长行尾部）
- [ ] MCP 配置指向的服务器与权限范围
- [ ] 恶意模型文件（pickle 系 .pkl/.pt）、恶意 .ipynb
- [ ] 项目集成 LLM 时的 OWASP LLM Top 10 检查
