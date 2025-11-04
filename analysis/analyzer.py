"""
数据分析模块
提供数据统计和分析功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import Logger


class DataAnalyzer:
    """数据分析类"""
    
    def __init__(self, data: List[Dict] = None):
        """
        初始化数据分析器
        
        Args:
            data: 数据列表（字典列表）
        """
        self.data = data or []
        self.df: Optional[pd.DataFrame] = None
        
        if self.data:
            self.df = pd.DataFrame(self.data)
            Logger.info(f"数据分析器初始化: {len(self.data)}条记录")
    
    def load_data(self, data: List[Dict]):
        """
        加载数据
        
        Args:
            data: 数据列表
        """
        self.data = data
        self.df = pd.DataFrame(data)
        Logger.info(f"加载数据: {len(data)}条记录")
    
    def get_statistics(self) -> Dict:
        """
        获取基本统计信息
        
        Returns:
            dict: 统计信息字典
        """
        if self.df is None or self.df.empty:
            return {'error': '数据为空'}
        
        try:
            stats = {
                'total_count': len(self.df),
                'columns': list(self.df.columns),
                'dtypes': {col: str(dtype) for col, dtype in self.df.dtypes.items()},
                'missing_values': self.df.isnull().sum().to_dict(),
                'numeric_stats': {}
            }
            
            # 数值列的统计信息
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                stats['numeric_stats'][col] = {
                    'mean': float(self.df[col].mean()),
                    'median': float(self.df[col].median()),
                    'std': float(self.df[col].std()),
                    'min': float(self.df[col].min()),
                    'max': float(self.df[col].max()),
                    'sum': float(self.df[col].sum())
                }
            
            Logger.info("统计分析完成")
            return stats
            
        except Exception as e:
            Logger.error(f"统计分析失败: {e}")
            return {'error': str(e)}
    
    def group_by(self, column: str) -> Dict:
        """
        按列分组统计
        
        Args:
            column: 分组列名
        
        Returns:
            dict: 分组统计结果
        """
        if self.df is None or self.df.empty:
            return {'error': '数据为空'}
        
        if column not in self.df.columns:
            return {'error': f'列不存在: {column}'}
        
        try:
            # 按列分组并计数
            grouped = self.df.groupby(column).size().to_dict()
            
            result = {
                'column': column,
                'groups': [
                    {'name': str(k), 'count': int(v)}
                    for k, v in grouped.items()
                ],
                'total': len(grouped)
            }
            
            Logger.info(f"分组分析完成: {column}")
            return result
            
        except Exception as e:
            Logger.error(f"分组分析失败: {e}")
            return {'error': str(e)}
    
    def calculate_trend(self, value_column: str, date_column: str = None) -> Dict:
        """
        计算趋势（时间序列分析）
        
        Args:
            value_column: 数值列名
            date_column: 日期列名（可选）
        
        Returns:
            dict: 趋势分析结果
        """
        if self.df is None or self.df.empty:
            return {'error': '数据为空'}
        
        try:
            if value_column not in self.df.columns:
                return {'error': f'列不存在: {value_column}'}
            
            # 如果提供了日期列，按日期排序
            df = self.df.copy()
            if date_column and date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column])
                df = df.sort_values(date_column)
            
            values = df[value_column].dropna().values
            
            if len(values) < 2:
                return {'error': '数据点太少，无法计算趋势'}
            
            # 计算移动平均
            window = min(7, len(values) // 2)
            if window >= 2:
                moving_avg = pd.Series(values).rolling(window=window).mean().tolist()
            else:
                moving_avg = values.tolist()
            
            # 计算趋势方向（简单线性回归）
            x = np.arange(len(values))
            y = values
            coefficients = np.polyfit(x, y, 1)
            slope = coefficients[0]
            
            trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            
            result = {
                'values': values.tolist(),
                'moving_average': moving_avg,
                'trend_direction': trend_direction,
                'slope': float(slope),
                'data_points': len(values)
            }
            
            Logger.info(f"趋势分析完成: {value_column}")
            return result
            
        except Exception as e:
            Logger.error(f"趋势分析失败: {e}")
            return {'error': str(e)}
    
    def correlation_analysis(self, columns: List[str] = None) -> Dict:
        """
        相关性分析
        
        Args:
            columns: 要分析的列名列表（默认所有数值列）
        
        Returns:
            dict: 相关性矩阵
        """
        if self.df is None or self.df.empty:
            return {'error': '数据为空'}
        
        try:
            # 选择数值列
            if columns:
                numeric_df = self.df[columns].select_dtypes(include=[np.number])
            else:
                numeric_df = self.df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                return {'error': '没有数值列可供分析'}
            
            # 计算相关性矩阵
            corr_matrix = numeric_df.corr()
            
            result = {
                'columns': list(corr_matrix.columns),
                'matrix': corr_matrix.values.tolist()
            }
            
            Logger.info("相关性分析完成")
            return result
            
        except Exception as e:
            Logger.error(f"相关性分析失败: {e}")
            return {'error': str(e)}
    
    def get_top_n(self, column: str, n: int = 10, ascending: bool = False) -> List[Dict]:
        """
        获取Top N记录
        
        Args:
            column: 排序列名
            n: 返回记录数
            ascending: 是否升序（False为降序）
        
        Returns:
            list: Top N记录列表
        """
        if self.df is None or self.df.empty:
            return []
        
        try:
            if column not in self.df.columns:
                Logger.warning(f"列不存在: {column}")
                return []
            
            top_df = self.df.nlargest(n, column) if not ascending else self.df.nsmallest(n, column)
            result = top_df.to_dict('records')
            
            Logger.info(f"获取Top{n}: {column}")
            return result
            
        except Exception as e:
            Logger.error(f"获取TopN失败: {e}")
            return []
    
    def filter_data(self, conditions: Dict) -> List[Dict]:
        """
        过滤数据
        
        Args:
            conditions: 过滤条件字典，如 {'category': '科技', 'views__gt': 1000}
                        支持后缀: __gt (>), __lt (<), __gte (>=), __lte (<=), __ne (!=)
        
        Returns:
            list: 过滤后的记录列表
        """
        if self.df is None or self.df.empty:
            return []
        
        try:
            df = self.df.copy()
            
            for key, value in conditions.items():
                # 解析条件
                if '__' in key:
                    column, operator = key.rsplit('__', 1)
                    
                    if column not in df.columns:
                        continue
                    
                    if operator == 'gt':
                        df = df[df[column] > value]
                    elif operator == 'lt':
                        df = df[df[column] < value]
                    elif operator == 'gte':
                        df = df[df[column] >= value]
                    elif operator == 'lte':
                        df = df[df[column] <= value]
                    elif operator == 'ne':
                        df = df[df[column] != value]
                else:
                    # 等于条件
                    if key in df.columns:
                        df = df[df[key] == value]
            
            result = df.to_dict('records')
            Logger.info(f"数据过滤完成: {len(result)}条记录")
            return result
            
        except Exception as e:
            Logger.error(f"数据过滤失败: {e}")
            return []
    
    def export_to_excel(self, file_path: str) -> bool:
        """
        导出到Excel
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 是否成功
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法导出")
            return False
        
        try:
            self.df.to_excel(file_path, index=False)
            Logger.info(f"数据已导出到: {file_path}")
            return True
        except Exception as e:
            Logger.error(f"导出Excel失败: {e}")
            return False
    
    def export_to_csv(self, file_path: str) -> bool:
        """
        导出到CSV
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 是否成功
        """
        if self.df is None or self.df.empty:
            Logger.warning("数据为空，无法导出")
            return False
        
        try:
            self.df.to_csv(file_path, index=False, encoding='utf-8-sig')
            Logger.info(f"数据已导出到: {file_path}")
            return True
        except Exception as e:
            Logger.error(f"导出CSV失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 示例数据
    data = [
        {'title': '新闻1', 'category': '科技', 'views': 1500, 'date': '2025-10-01'},
        {'title': '新闻2', 'category': '体育', 'views': 2000, 'date': '2025-10-02'},
        {'title': '新闻3', 'category': '科技', 'views': 1200, 'date': '2025-10-03'},
        {'title': '新闻4', 'category': '娱乐', 'views': 3000, 'date': '2025-10-04'},
        {'title': '新闻5', 'category': '科技', 'views': 1800, 'date': '2025-10-05'},
    ]
    
    # 创建分析器
    analyzer = DataAnalyzer(data)
    
    # 基本统计
    stats = analyzer.get_statistics()
    print("基本统计:")
    print(stats)
    
    # 分组统计
    print("\n分类统计:")
    group_stats = analyzer.group_by('category')
    print(group_stats)
    
    # TopN
    print("\n浏览量Top3:")
    top_records = analyzer.get_top_n('views', n=3)
    for record in top_records:
        print(record)

