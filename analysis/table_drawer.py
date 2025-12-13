"""
通用表格结构绘图工具

使用 Graphviz 生成数据表结构的示意图。
"""
from pathlib import Path
import pandas as pd
from utils.logger import Logger

def draw_table_structure(df: pd.DataFrame, table_name: str, pk_column: str, output_dir: Path, file_stem: str):
    """
    通用函数：为给定的 DataFrame 生成一个美化的表结构示意图。

    Args:
        df (pd.DataFrame): 需要可视化的数据表。
        table_name (str): 在图表中显示的表名（例如 "students (学生表)"）。
        pk_column (str): 主键列的名称。
        output_dir (Path): 图表输出目录。
        file_stem (str): 输出图片的文件名（不含扩展名）。
    """
    try:
        from graphviz import Digraph
    except ImportError:
        Logger.error("缺少 graphviz 库。请运行 'pip install graphviz' 并确保已安装 Graphviz 系统软件。")
        Logger.warning(f"跳过 {table_name} 表结构示意图生成。")
        return

    if df is None:
        Logger.warning(f"缺少数据，跳过 {table_name} 表结构示意图生成。")
        return

    # --- 美化配置 ---
    header_bg = "#003087"
    header_font_color = "white"
    subheader_bg = "#E6F0FA"
    row_bg_light = "#FFFFFF"
    row_bg_dark = "#F7F7F7"
    pk_color = "#E53935"

    dot = Digraph(file_stem, comment=f'{table_name} Structure')
    dot.attr('node', shape='none', fontname='SimHei')
    dot.attr(rankdir='LR')

    # --- 使用 HTML 标签构建美化的表格 ---
    html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="8" FIXEDSIZE="FALSE">'
    
    # 1. 表头
    html_label += f'<TR><TD BGCOLOR="{header_bg}" ALIGN="CENTER" COLSPAN="3"><FONT COLOR="{header_font_color}" POINT-SIZE="18"><B>{table_name}</B></FONT></TD></TR>'
    
    # 2. 列标题
    html_label += f'<TR><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>主键</B></TD><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>字段名 (Field)</B></TD><TD BGCOLOR="{subheader_bg}" POINT-SIZE="12"><B>数据类型 (Type)</B></TD></TR>'

    # 3. 遍历所有字段并生成表格行
    for i, (col, dtype) in enumerate(df.dtypes.items()):
        bg_color = row_bg_light if i % 2 == 0 else row_bg_dark
        
        pk_symbol = ''
        if col == pk_column:
            pk_symbol = f'<FONT COLOR="{pk_color}" POINT-SIZE="12"><B>PK</B></FONT>'

        html_label += f'<TR><TD ALIGN="CENTER" BGCOLOR="{bg_color}">{pk_symbol}</TD><TD ALIGN="LEFT" BGCOLOR="{bg_color}" POINT-SIZE="12">{col}</TD><TD ALIGN="LEFT" BGCOLOR="{bg_color}" POINT-SIZE="12">{str(dtype)}</TD></TR>'

    html_label += '</TABLE>>'
    
    dot.node('struct', label=html_label)

    try:
        output_path = output_dir / file_stem
        dot.render(output_path, format='png', cleanup=True)
        Logger.info(f"已生成图表：{output_path.name}.png")
    except Exception as e:
        Logger.error(f"生成 {table_name} 结构图失败，请确保 Graphviz 已正确安装并已添加到系统 PATH。错误: {e}")
