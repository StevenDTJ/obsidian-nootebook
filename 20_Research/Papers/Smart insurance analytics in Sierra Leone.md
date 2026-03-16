---
title: "Smart insurance analytics: A novel ensemble feature selection approach to unlock health insurance coverage predictions in Sierra Leone"
authors: ["David B Olawade", "Augustus Osborne", "Afeez A Soladoye", "Olaitan E Oluwadare", "Emmanuel O Awogbindin", "Ojima Z Wada"]
journal: "International journal of medical informatics"
pub_date: "2026-05-01"
doi: "10.1016/j.ijmedinf.2026.106313"
pmid: "41633286"
source: "PubMed"
url: "https://pubmed.ncbi.nlm.nih.gov/41633286/"
domains: ["卫生政策", "卫生经济学"]
keywords: ["health insurance", "health insurance policy", "universal health coverage", "machine learning", "卫生政策", "卫生经济学"]
score: 2.04
---

# Smart insurance analytics: Health insurance coverage predictions in Sierra Leone

## 基本信息

- **作者**: David B Olawade, Augustus Osborne, Afeez A Soladoye 等（6位作者）
- **期刊**: International journal of medical informatics
- **发表日期**: 2026-05-01
- **DOI**: [10.1016/j.ijmedinf.2026.106313](https://doi.org/10.1016/j.ijmedinf.2026.106313)
- **PubMed**: [PMID:41633286](https://pubmed.ncbi.nlm.nih.gov/41633286/)

## 摘要

Predicting health insurance uptake remains a critical challenge for policymakers and insurance providers seeking to optimise coverage strategies and resource allocation. In Sierra Leone, health insurance uptake remains extremely low, and understanding determinants is vital for universal health coverage goals. This study developed and evaluated an innovative ensemble feature selection methodology for health insurance uptake prediction using data from the 2019 Sierra Leone Demographic and Health Survey (15,574 women).

## 研究背景与动机

预测健康保险覆盖率仍然是决策者和保险提供者寻求优化覆盖策略和资源分配的关键挑战。在塞拉利昂，健康保险覆盖率极低，理解其决定因素对实现全民健康覆盖目标至关重要。传统方法在识别关键预测因素方面存在局限，机器学习方法可能提供新的突破。

## 方法概述

- **数据源**: 2019年塞拉利昂人口与健康调查（SLDHS），15,574名女性
- **集成特征选择**: 自适应蚁群优化 + 递归特征消除 + 后向消除（三种方法共识）
- **比较算法**: 逻辑回归、SVM、KNN、随机森林、梯度提升、XGBoost、LightGBM（共7种）
- **类别不平衡处理**: SMOTE
- **验证策略**: 嵌套5折交叉验证 + 10折交叉验证 + 留出测试集（防止信息泄露）

## 主要发现

- **随机森林**表现最优：准确率0.9973、精确率0.9973、召回率0.9973、F1 0.9973、ROC AUC 1.0000
- **XGBoost**表现可比：所有指标0.9914，ROC AUC 0.9998
- 后向特征消除在集成方法中一致产生最优结果
- 近乎完美的性能需要谨慎解读，外部验证对确认泛化性至关重要

## 研究价值

本研究建立了健康保险预测的新性能基准，显著超越现有文献，对塞拉利昂的健康保险政策和实践有直接影响。创新的集成特征选择方法为提高医疗保健应用中的预测准确性提供了稳健框架。对于类似低收入国家的健康保险推广具有方法论参考价值。

## 优势与局限

**优势**: 创新的集成特征选择方法；全面的算法比较；多种验证策略防止过拟合；大样本量

**局限**: 单一国家数据；近乎完美的性能可能暗示过拟合风险；缺乏外部验证；横截面数据限制

## 相关论文

- [[Financial protection in Austria - catastrophic health expenditure]]
- [[Tracking health expenditures in Tajikistan toward UHC]]

## 笔记链接

- [[卫生政策]]
- [[卫生经济学]]
- [[全民健康覆盖]]
