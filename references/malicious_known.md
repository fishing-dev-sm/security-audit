# 已知恶意/投毒包（历史事件种子清单）

命中本清单 → 直接报 Critical。未命中 ≠ 安全。
本清单只是种子，审核中发现新的恶意包应补充进来；完整数据查 OSV 的 MAL- 条目
（https://osv.dev/list?q=&ecosystem= ）与 GitHub Advisory Database。

## npm

| 包名 | 事件 |
|---|---|
| event-stream（3.3.6）+ flatmap-stream | 2018，注入针对 copay 钱包的比特币窃取代码 |
| ua-parser-js（0.7.29/0.8.0/1.0.0） | 2021，维护者账号被劫持，植入挖矿+凭据窃取 |
| coa（2.0.3+）、rc（1.2.9/1.3.9/2.3.9） | 2021，同源劫持事件 |
| colors.js（>1.4.0）、faker.js | 2022，维护者自毁式 sabotage（protestware） |
| node-ipc（10.1.1/10.1.2） | 2022，protestware，按 IP 地理位置擦除文件 |
| ctx（此处为 npm 同名仿冒） | 见 PyPI ctx 事件衍生的跨生态仿冒 |

## PyPI

| 包名 | 事件 |
|---|---|
| ctx（0.1.2 之后被劫持版本） | 2022，维护者邮箱过期被接管，窃取 AWS 凭据 |
| phpass（仿冒） | 2022，同 ctx 事件同批被劫持 |
| colourama | 2018，typosquat of colorama，剪贴板加密货币地址劫持 |
| jeIlyfish（大写 i 仿 l） | 2022，typosquat of jellyfish，窃取 SSH 密钥 |
| python3-dateutil / jeIlyfish 同批 | 2022，typosquat of python-dateutil |
| torchtriton（公网 PyPI 版） | 2022，依赖混淆攻击 PyTorch nightly 用户，外传系统信息 |
| urllib3 的仿冒们（如 2017 年 PyPI 大量仿包事件） | 多起，注意一切与标准库/头部包同名的第三方包 |

## 通用规则（比清单更重要）

- 与 Python **标准库模块**同名的 PyPI 包（如 `urllib`、`ssl`、`sys` 出现在 requirements 里）→ 直接可疑
- 知名包的**同名公网包 + 异常高版本号** → 依赖混淆特征
- 事件时间线会过时：新投毒事件随时发生，审核时对一个高度可疑的包应现场搜一遍近期安全新闻
