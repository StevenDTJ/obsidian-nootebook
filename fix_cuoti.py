import os
import re

def process_details_content(content):
    """处理 details 块内的内容"""
    lines = content.split('\n')
    result_lines = []

    for line in lines:
        processed_line = line

        # 处理 **文字：** 这种情况（文字后有冒号和空格）
        processed_line = re.sub(r'\*\*([^:]+)：\*\*\s*', r'<b>\1</b>：', processed_line)
        # 处理 **文字** 这种情况（没有冒号）
        processed_line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', processed_line)

        # 移除行末的多余空格
        processed_line = processed_line.rstrip()

        # 如果行不为空，且末尾没有 <br>，则添加 <br>
        if processed_line and not processed_line.endswith('<br>'):
            processed_line = processed_line + '<br>'

        result_lines.append(processed_line)

    # 处理段落之间的空行
    final_lines = []
    prev_empty = False

    for line in result_lines:
        is_empty = (line.strip() == '')

        if is_empty:
            # 如果当前行是空行
            if not prev_empty:
                # 如果前一行不是空行，添加 <br><br>
                final_lines.append('<br><br>')
            # 跳过连续的空行
        else:
            final_lines.append(line)

        prev_empty = is_empty

    return '\n'.join(final_lines)

# 主程序
folder_path = r"E:\obsidian\document\错题"

# 需要处理的文件列表（排除 1.md 和 23.md）
files_to_process = [
    "2.md", "3.md", "4.md", "5.md", "6.md", "7.md", "8.md", "9.md",
    "10.md", "11.md", "12.md", "13.md", "14.md", "15.md", "16.md", "17.md",
    "18.md", "19.md", "20.md", "21.md", "22.md", "24.md"
]

for filename in files_to_process:
    file_path = os.path.join(folder_path, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找 <details> 块，保留前面的所有内容（包括 frontmatter）
        # 匹配 <details> 开头到 </details> 结束的部分
        details_pattern = r'(<details>\n<summary>.*?</summary>)(\n.*?)(\n</details>)'
        match = re.search(details_pattern, content, re.DOTALL)

        if match:
            before_details = match.group(1)
            details_content = match.group(2)
            after_details = match.group(3)

            # 处理 details 块内的内容
            processed_content = process_details_content(details_content)

            # 重新组合
            new_content = before_details + processed_content + after_details

            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"已处理: {filename}")
        else:
            print(f"未找到 <details> 块: {filename}")
    else:
        print(f"文件不存在: {filename}")
