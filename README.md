# PDD Holdings (拼多多) 财务分析报告

一份基于 SEC 官方财报数据、覆盖 2018 年上市以来全部季度的可视化财务分析报告。

**在线查看：** https://lvjiang1024.github.io/pdd-financial-report/

## 内容

- 📈 总览、📊 收入结构、💰 利润分析、🏦 现金与资产负债、💎 股东回报与效率、
  📅 年度汇总、📋 季度明细表、💬 管理层观点（中文，含历任高管季度业绩发言翻译）
- 数据覆盖 2018 Q2 – 至今 全部季度
- 数据来源：[SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001737806&type=6-K) PDD Holdings Inc. 6-K 备案（CIK 0001737806）

## 目录结构

- `docs/index.html` — GitHub Pages 发布的报告（即上方在线链接指向的文件）
- `reports/` — 报告的本地留存版本（文件名含中文，双击可直接在浏览器打开）
- `pipeline/` — 完整的数据提取、翻译、报告生成流水线，详见 [pipeline/README.md](pipeline/README.md)。
  新一季财报发布后，凭这套流水线可以增量更新报告，不需要重新处理历史数据。

## 免责声明

本报告仅供研究学习使用，不构成任何投资建议。财务数据提取自公司公开披露的 SEC 备案文件，
Non-GAAP 指标为公司自行定义口径，ROE/ROA 为本报告基于期末资产负债表估算，并非官方披露数值。
