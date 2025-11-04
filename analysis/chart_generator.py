"""
图表生成模块
提供数据可视化功能
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from typing import List, Dict, Optional, Tuple
import pandas as pd
from utils.logger import Logger

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class ChartGenerator:
    """图表生成类"""
    
    def __init__(self, data: List[Dict] = None, figsize: Tuple[int, int] = (10, 6)):
        """
        初始化图表生成器
        
        Args:
            data: 数据列表
            figsize: 图表大小 (width, height)
        """
        self.data = data or []
        self.figsize = figsize
        self.df: Optional[pd.DataFrame] = None
        
        if self.data:
            self.df = pd.DataFrame(self.data)
            Logger.info(f"图表生成器初始化: {len(self.data)}条记录")
        
        # 设置样式
        sns.set_style("whitegrid")
    
    def load_data(self, data: List[Dict]):
        """
        加载数据
        
        Args:
            data: 数据列表
        """
        self.data = data
        self.df = pd.DataFrame(data)
        Logger.info(f"加载数据: {len(data)}条记录")
    
    def create_bar_chart(self, x_column: str, y_column: str, title: str = "柱状图") -> Optional[Figure]:
        """
        创建柱状图
        
        Args:
            x_column: X轴列名
            y_column: Y轴列名
            title: 图表标题
        
        Returns:
            Figure: matplotlib图表对象
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法创建图表")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            
            # 绘制柱状图
            self.df.plot(x=x_column, y=y_column, kind='bar', ax=ax, color='skyblue')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel(y_column, fontsize=12)
            ax.legend([y_column])
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            Logger.info(f"创建柱状图: {title}")
            return fig
            
        except Exception as e:
            Logger.error(f"创建柱状图失败: {e}")
            return None
    
    def create_line_chart(self, x_column: str, y_columns: List[str], title: str = "折线图") -> Optional[Figure]:
        """
        创建折线图
        
        Args:
            x_column: X轴列名
            y_columns: Y轴列名列表（可以多条线）
            title: 图表标题
        
        Returns:
            Figure: matplotlib图表对象
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法创建图表")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            
            # 绘制折线图
            for y_col in y_columns:
                if y_col in self.df.columns:
                    ax.plot(self.df[x_column], self.df[y_col], marker='o', label=y_col, linewidth=2)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel('值', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            Logger.info(f"创建折线图: {title}")
            return fig
            
        except Exception as e:
            Logger.error(f"创建折线图失败: {e}")
            return None
    
    def create_pie_chart(self, column: str, title: str = "饼图", top_n: int = None) -> Optional[Figure]:
        """
        创建饼图
        
        Args:
            column: 分类列名
            title: 图表标题
            top_n: 只显示前N项（其他合并为"其他"）
        
        Returns:
            Figure: matplotlib图表对象
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法创建图表")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            
            # 统计各类别数量
            value_counts = self.df[column].value_counts()
            
            # 如果指定了top_n，合并其他项
            if top_n and len(value_counts) > top_n:
                top_values = value_counts.head(top_n)
                other_sum = value_counts[top_n:].sum()
                if other_sum > 0:
                    top_values['其他'] = other_sum
                value_counts = top_values
            
            # 绘制饼图
            colors = plt.cm.Set3(range(len(value_counts)))
            wedges, texts, autotexts = ax.pie(
                value_counts.values,
                labels=value_counts.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            
            # 设置字体大小
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_weight('bold')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            Logger.info(f"创建饼图: {title}")
            return fig
            
        except Exception as e:
            Logger.error(f"创建饼图失败: {e}")
            return None
    
    def create_scatter_plot(self, x_column: str, y_column: str, 
                           color_column: str = None, title: str = "散点图") -> Optional[Figure]:
        """
        创建散点图
        
        Args:
            x_column: X轴列名
            y_column: Y轴列名
            color_column: 颜色分类列名（可选）
            title: 图表标题
        
        Returns:
            Figure: matplotlib图表对象
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法创建图表")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            
            if color_column and color_column in self.df.columns:
                # 按类别着色
                for category in self.df[color_column].unique():
                    mask = self.df[color_column] == category
                    ax.scatter(
                        self.df[mask][x_column],
                        self.df[mask][y_column],
                        label=category,
                        alpha=0.6,
                        s=100
                    )
                ax.legend()
            else:
                # 单一颜色
                ax.scatter(
                    self.df[x_column],
                    self.df[y_column],
                    alpha=0.6,
                    s=100,
                    color='skyblue'
                )
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel(y_column, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            Logger.info(f"创建散点图: {title}")
            return fig
            
        except Exception as e:
            Logger.error(f"创建散点图失败: {e}")
            return None
    
    def create_histogram(self, column: str, bins: int = 10, title: str = "直方图") -> Optional[Figure]:
        """
        创建直方图（频数分布）
        
        Args:
            column: 列名
            bins: 分组数量
            title: 图表标题
        
        Returns:
            Figure: matplotlib图表对象
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法创建图表")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            
            # 绘制直方图
            ax.hist(self.df[column].dropna(), bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel('频数', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            Logger.info(f"创建直方图: {title}")
            return fig
            
        except Exception as e:
            Logger.error(f"创建直方图失败: {e}")
            return None
    
    def save_chart(self, fig: Figure, file_path: str, dpi: int = 100) -> bool:
        """
        保存图表到文件
        
        Args:
            fig: matplotlib图表对象
            file_path: 保存路径
            dpi: 分辨率
        
        Returns:
            bool: 是否成功
        """
        try:
            fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
            Logger.info(f"图表已保存到: {file_path}")
            plt.close(fig)
            return True
        except Exception as e:
            Logger.error(f"保存图表失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 示例数据
    data = [
        {'category': '科技', 'views': 1500, 'likes': 120},
        {'category': '体育', 'views': 2000, 'likes': 180},
        {'category': '科技', 'views': 1200, 'likes': 90},
        {'category': '娱乐', 'views': 3000, 'likes': 250},
        {'category': '科技', 'views': 1800, 'likes': 150},
        {'category': '体育', 'views': 2200, 'likes': 200},
        {'category': '娱乐', 'views': 2800, 'likes': 230},
    ]
    
    # 创建图表生成器
    chart_gen = ChartGenerator(data)
    
    # 创建饼图
    fig = chart_gen.create_pie_chart('category', title='分类分布')
    if fig:
        chart_gen.save_chart(fig, 'exports/category_pie.png')
    
    # 创建散点图
    fig = chart_gen.create_scatter_plot('views', 'likes', color_column='category', title='浏览量与点赞数关系')
    if fig:
        chart_gen.save_chart(fig, 'exports/views_likes_scatter.png')
    
    print("图表生成完成！")

