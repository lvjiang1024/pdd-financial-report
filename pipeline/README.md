# PDD Holdings 财报分析 — 数据流水线

本目录固化了生成 `../reports/PDD_Holdings_财务分析报告.html` 的完整流程和中间数据，
这样以后每次 PDD 发布新一季财报时，不需要重新做一遍全部提取和翻译工作。

## 目录结构

```
pipeline/
  raw_filings/          原始 SEC 6-K 财报公告 HTML（Exhibit 99.1），文件名 = SEC accession number
  data/
    quarters.json        季度 -> accession number 的映射表（新增季度只需要改这个文件）
    quarterly_raw.json    从各季度公告提取出的原始财务数据
    annual_raw.json       从 Q4 公告中提取的年度（Fiscal Year）数据
    mgmt_raw.json          每季度管理层讨论段落的原始文本（未分类）
    mgmt_structured.json  从原始文本中解析出的英文 bullets + quotes
    mgmt_cn.json           翻译成中文、清理过的管理层评论（最终使用）
    final_data.json        供 HTML 报告消费的最终合并数据（可读版）
    final_data_min.json    同上，压缩版，直接内嵌进报告 HTML
  extract.py             第1步：从 raw_filings/*.htm 提取财务数字 -> quarterly_raw.json / annual_raw.json / mgmt_raw.json
  extract_mgmt.py         第2步：从 mgmt_raw.json 解析出英文 bullets/quotes -> mgmt_structured.json
  build_mgmt_cn.py        第3步：清理垃圾片段、翻译成中文 -> mgmt_cn.json（用到 translations.py 里的翻译词典）
  translations.py         人工维护的英文原文 -> 中文翻译对照表（职务、发言人姓名、语录）
  build_report_data.py    第4步：汇总所有数据、计算 ROE/ROA 等衍生指标，写出 final_data.json 并渲染最终 HTML 报告
  report_template.html    报告的 HTML/CSS/JS 模板（图表、Tab、时间轴），用 __DATA_JSON__ 占位符注入数据
  add_quarter.py          辅助脚本：给定季度和 SEC accession number，自动下载财报并注册到 quarters.json
```

## 数据来源

不是从 investor.pddholdings.com（有反爬保护，无法直接抓取），而是从 **SEC EDGAR**
（PDD Holdings CIK: `0001737806`）拉取公司提交的 6-K 表格所附的 Exhibit 99.1
（即季度业绩新闻稿原文），这是 SEC 官方存档，权威且稳定可访问。

## 新一季财报发布后，如何更新报告

### 方式一：直接让 Claude 处理（推荐）

新财报发布后（PDD 通常在每季度末后 1-2 个月内发布，即 3月/5月/8月/11月），
直接跟 Claude 说类似：

> "PDD 发布了 2026 年 Q2 财报，帮我更新一下 `PDD/pipeline` 里的分析报告"

Claude 会：
1. 去 SEC EDGAR 查该季度最新的 6-K 备案（CIK 0001737806），找到 Exhibit 99.1 财报新闻稿
2. 下载到 `raw_filings/`，并在 `data/quarters.json` 里登记新的 季度->accession 映射
3. 依次运行 `extract.py` → `extract_mgmt.py` → `build_mgmt_cn.py`（翻译新一季的管理层发言）→ `build_report_data.py`
4. 重新生成 `../reports/PDD_Holdings_财务分析报告.html`

这个目录的存在意味着 Claude 不需要重新下载全部 32 个历史季度、不需要重新翻译历史管理层评论，
只需要处理新增的这一季，速度快很多。

### 方式二：手动运行流水线

如果你已经知道新一季 6-K 的 accession number（在 SEC EDGAR 上查
`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001737806&type=6-K&count=10`）：

```bash
cd pipeline
python3 add_quarter.py 2026Q2 0001104659-26-XXXXXX   # 下载财报 + 注册到 quarters.json
python3 extract.py          # 提取全部季度的财务数字（含新一季）
python3 extract_mgmt.py     # 解析管理层评论原文
python3 build_mgmt_cn.py    # 翻译新一季的管理层评论（如果 translations.py 里没有对应译文，会原样保留英文并打印 WARNING）
python3 build_report_data.py  # 汇总数据、生成最终 HTML 报告
```

### 注意事项

- **`build_mgmt_cn.py` 依赖 `translations.py` 里手工维护的翻译词典**。新一季的管理层
  语录是全新的英文文本，词典里不会有现成翻译，脚本会打印 `WARNING: N quotes missing
  translation` 并原样保留英文——这时需要 Claude（或你自己）把新增的语录翻译好，
  追加到 `translations.py` 的 `QUOTE_TR` 字典里，再重新运行 `build_mgmt_cn.py`。
- 财报正文的度量单位在 2026 年后从"百万元"变成了"十亿元"表述（见 `extract.py` 里
  `to_million()` 的换算逻辑），如果未来又变了新的表述方式，提取正则可能需要相应调整。
- 年度（Fiscal Year）数据只在 Q4 财报里出现，所以只有当新增的季度是 Q4 时，
  `annual_raw.json` 才会新增一年的数据。
