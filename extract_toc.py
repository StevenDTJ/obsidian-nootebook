# -*- coding: utf-8 -*-
import pdfplumber
import re

pdf_path = "E:\\obsidian\\document\\公务员考试辅导用书·决战行测5000题（判断推理）（上册）2025版.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}")

    # 查找目录页 - 通常在前20页
    print("\n=== 查找目录页 ===")
    for i in range(min(30, len(pdf.pages))):
        text = pdf.pages[i].extract_text()
        if text and ('目录' in text or '章' in text):
            print(f"\n--- 第 {i+1} 页 ---")
            print(text[:3000])
            print("\n" + "="*50)
