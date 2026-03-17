import pandas as pd
import numpy as np
import logging
from typing import Optional
import io

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_data(excel_data: bytes, debug: bool = False) -> pd.DataFrame:
    """
    处理 Excel 数据
    
    Args:
        excel_data: Excel 文件的字节数据
        debug: 是否启用调试模式
    
    Returns:
        处理后的 DataFrame
    """
    if debug:
        logger.info(f"开始处理数据，数据大小: {len(excel_data)} 字节")
    
    try:
        # 读取 Excel 文件
        df = pd.read_excel(io.BytesIO(excel_data))
        
        if debug:
            logger.info(f"成功读取数据，形状: {df.shape}")
            logger.info(f"列名: {list(df.columns)}")
            logger.info(f"数据类型:\n{df.dtypes}")
            logger.info(f"前5行数据:\n{df.head()}")
        
        # 检查数据是否为空
        if df.empty:
            logger.warning("读取的数据为空")
            return df
        
        # 这里添加你的数据处理逻辑
        # 示例：添加一些计算列
        
        # 示例处理：如果有数值列，计算统计信息
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if debug and len(numeric_cols) > 0:
            logger.info(f"数值列: {list(numeric_cols)}")
            for col in numeric_cols:
                logger.info(f"{col} - 平均值: {df[col].mean():.2f}, "
                          f"最小值: {df[col].min():.2f}, "
                          f"最大值: {df[col].max():.2f}")
        
        # 示例：添加处理标记
        df['处理时间'] = pd.Timestamp.now()
        df['数据源'] = 'processed'
        
        if debug:
            logger.info(f"处理完成，最终形状: {df.shape}")
            logger.info(f"最终列名: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"处理数据时发生错误: {str(e)}", exc_info=True)
        raise

def generate_test_data(rows: int = 50) -> pd.DataFrame:
    """
    生成测试数据
    
    Args:
        rows: 生成的行数
    
    Returns:
        包含随机测试数据的 DataFrame
    """
    np.random.seed(42)
    
    data = {
        '员工ID': range(1, rows + 1),
        '姓名': [f'员工{i}' for i in range(1, rows + 1)],
        '部门': np.random.choice(['研发部', '市场部', '销售部', '人事部', '财务部'], rows),
        '基本工资': np.random.randint(5000, 20000, rows),
        '绩效奖金': np.random.randint(1000, 10000, rows),
        '考勤得分': np.random.uniform(80, 100, rows).round(1),
        '入职月份': np.random.randint(1, 13, rows),
        '是否全职': np.random.choice([True, False], rows, p=[0.8, 0.2])
    }
    
    df = pd.DataFrame(data)
    
    # 计算总工资
    df['总工资'] = df['基本工资'] + df['绩效奖金']
    
    # 添加绩效评级
    conditions = [
        df['考勤得分'] >= 95,
        df['考勤得分'] >= 85,
        df['考勤得分'] >= 75
    ]
    choices = ['A', 'B', 'C']
    df['绩效评级'] = np.select(conditions, choices, default='D')
    
    return df

if __name__ == "__main__":
    # 当直接运行此文件时，执行测试
    print("运行 excel_writer.py 的测试...")
    
    # 生成测试数据
    test_df = generate_test_data(20)
    print(f"生成的测试数据形状: {test_df.shape}")
    print(f"测试数据列名: {list(test_df.columns)}")
    print("\n测试数据预览:")
    print(test_df.head())
    
    # 保存为 Excel 并测试处理函数
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        test_df.to_excel(writer, index=False)
    excel_data = output.getvalue()
    
    print(f"\n生成的 Excel 文件大小: {len(excel_data)} 字节")
    
    # 测试处理函数（启用调试模式）
    try:
        result = process_data(excel_data, debug=True)
        print(f"\n✅ 处理成功！结果形状: {result.shape}")
        print("\n处理结果预览:")
        print(result.head())
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")