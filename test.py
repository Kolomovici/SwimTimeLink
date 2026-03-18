#!/usr/bin/env python3
"""
独立测试脚本 - 使用随机数据测试 excel_writer.py 的功能
无需运行 Streamlit 应用即可调试
"""

import pandas as pd
import numpy as np
import io
import sys
import os
import traceback
from datetime import datetime
import time
import app
import shared_functions


# 添加当前目录到 Python 路径，确保可以导入 excel_writer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from excel_writer import process_data
    print("✅ 成功导入 excel_writer 模块")
except ImportError as e:
    print(f"❌ 无法导入 excel_writer 模块: {e}")
    print("请确保 excel_writer.py 在同一目录下")
    sys.exit(1)

def generate_test_data_variants():
    """生成多种测试数据变体"""
    
    test_cases = {}
    
    # 1. 基础测试数据
    np.random.seed(42)
    basic_data = {
        '员工编号': [f'E{i:03d}' for i in range(1, 31)],
        '姓名': [f'员工{i}' for i in range(1, 31)],
        '部门': np.random.choice(['技术部', '市场部', '销售部', '人事部', '财务部'], 30),
        '基本工资': np.random.randint(5000, 20000, 30),
        '绩效奖金': np.random.randint(1000, 10000, 30),
        '考勤天数': np.random.randint(20, 26, 30),
        '入职日期': pd.date_range('2020-01-01', periods=30, freq='30D'),
        '是否全职': np.random.choice([True, False], 30, p=[0.8, 0.2])
    }
    test_cases['基础数据'] = pd.DataFrame(basic_data)
    
    # 2. 大量数据测试
    large_data = {
        'ID': range(1, 1001),
        '数值列1': np.random.randn(1000),
        '数值列2': np.random.randint(1, 100, 1000),
        '分类列': np.random.choice(['A', 'B', 'C', 'D'], 1000),
        '文本列': [f'文本内容_{i}' for i in range(1000)]
    }
    test_cases['大量数据'] = pd.DataFrame(large_data)
    
    # 3. 边界情况测试
    edge_cases = {
        '空值测试': pd.DataFrame({
            'A': [1, None, 3, None, 5],
            'B': ['a', 'b', None, 'd', None],
            'C': [10.5, None, 30.2, None, 50.1]
        }),
        '特殊字符': pd.DataFrame({
            '文本': ['正常文本', '包含,逗号', '包含"引号"', '包含\n换行', '包含&特殊@字符#'],
            '数值': [100, 200, 300, 400, 500]
        }),
        '单行数据': pd.DataFrame({
            '列1': ['唯一行'],
            '列2': [999]
        })
    }
    test_cases.update(edge_cases)
    
    return test_cases

def test_key_press(key):
    """模拟按键按下"""
    print(f"\n=== 测试按键 {key} ===")
    
    if key == 4:
        func = shared_functions.get_start_timing()
        if func:
            func()
        else:
            print("错误：开始计时函数未注册")
            
    elif key == 5:
        func = shared_functions.get_test_latency()
        if func:
            func()
        else:
            print("错误：测试延迟函数未注册")


def dataframe_to_excel_bytes(df):
    """将 DataFrame 转换为 Excel 字节流"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='测试数据')
    return output.getvalue()

def run_single_test(test_name, df, verbose=True):
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试用例: {test_name}")
    print(f"{'='*60}")
    
    if verbose:
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        print(f"数据类型:\n{df.dtypes}")
        if not df.empty:
            print(f"\n数据预览 (前3行):")
            print(df.head(3))
    
    if df.empty:
        print("⚠️  空数据框，跳过测试")
        return None
    
    try:
        # 转换为 Excel 字节流
        excel_data = dataframe_to_excel_bytes(df)
        print(f"生成的 Excel 文件大小: {len(excel_data):,} 字节")
        
        # 调用处理函数
        print("🔄 正在调用 process_data()...")
        start_time = datetime.now()
        result_df = process_data(excel_data)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ 处理成功! 耗时: {processing_time:.3f}秒")
        print(f"处理后的数据形状: {result_df.shape}")
        print(f"处理后的列名: {list(result_df.columns)}")
        
        if verbose and not result_df.empty:
            print(f"\n处理结果预览 (前3行):")
            print(result_df.head(3))
        
        # 保存测试结果 - 修改保存路径
        output_dir = r"E:\CS\Timer\test_result"
        os.makedirs(output_dir, exist_ok=True)  # 确保目录存在
        output_filename = os.path.join(output_dir, f"test_output_{test_name}.csv")
        result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"💾 结果已保存到: {output_filename}")
        
        return result_df
        
    except Exception as e:
        print(f"❌ 处理失败!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 保存错误日志 - 修改保存路径
        error_dir = r"E:\CS\Timer\test_result"
        os.makedirs(error_dir, exist_ok=True)  # 确保目录存在
        error_log = os.path.join(error_dir, f"error_log_{test_name}.txt")
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(f"测试用例: {test_name}\n")
            f.write(f"错误时间: {datetime.now()}\n")
            f.write(f"错误类型: {type(e).__name__}\n")
            f.write(f"错误信息: {str(e)}\n")
            f.write("\n详细追踪:\n")
            traceback.print_exc(file=f)
        
        print(f"📝 错误日志已保存到: {error_log}")
        return None

def run_comprehensive_test():
    """运行全面的测试"""
    print("🚀 开始全面测试 excel_writer.py")
    print(f"测试时间: {datetime.now()}")
    print(f"Python 版本: {sys.version}")
    print(f"Pandas 版本: {pd.__version__}")
    print(f"Numpy 版本: {np.__version__}")
    
    # 生成测试数据
    print("\n📊 生成测试数据...")
    test_cases = generate_test_data_variants()
    
    results = {}
    success_count = 0
    total_count = len(test_cases)
    
    # 运行所有测试用例
    for test_name, df in test_cases.items():
        result = run_single_test(test_name, df, verbose=True)
        results[test_name] = result
        if result is not None:
            success_count += 1
    
    # 生成测试报告 - 修改保存路径
    print(f"\n{'='*60}")
    print("📋 测试报告")
    print(f"{'='*60}")
    print(f"总测试用例: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    # 生成汇总报告
    report_dir = r"E:\CS\Timer\test_result"
    os.makedirs(report_dir, exist_ok=True)  # 确保目录存在
    report_filename = os.path.join(report_dir, "test_report.txt")
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("Excel Writer 测试报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"测试时间: {datetime.now()}\n")
        f.write(f"总测试用例: {total_count}\n")
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {total_count - success_count}\n")
        f.write(f"成功率: {success_count/total_count*100:.1f}%\n\n")
        f.write("详细结果:\n")
        for test_name, result in results.items():
            status = "✅ 成功" if result is not None else "❌ 失败"
            if result is not None:
                f.write(f"{test_name}: {status} - 输出形状: {result.shape}\n")
            else:
                f.write(f"{test_name}: {status}\n")
    
    print(f"\n📄 详细报告已保存到: {report_filename}")
    return results

def interactive_test():
    """交互式测试模式"""
    print("\n🎮 交互式测试模式")
    print("=" * 40)
    
    while True:
        print("\n选择测试选项:")
        print("1. 运行自定义行数的测试")
        print("2. 测试特定数据类型")
        print("3. 压力测试（大量数据）")
        print("4. 退出")
        
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == '1':
            try:
                rows = int(input("请输入数据行数 (1-10000): "))
                rows = max(1, min(rows, 10000))
                
                np.random.seed(42)
                data = {
                    'ID': range(1, rows + 1),
                    '数值': np.random.randn(rows),
                    '分类': np.random.choice(['A', 'B', 'C'], rows),
                    '金额': np.random.randint(100, 10000, rows)
                }
                df = pd.DataFrame(data)
                
                run_single_test(f"自定义_{rows}行", df, verbose=True)
                
            except ValueError:
                print("❌ 请输入有效的数字")
                
        elif choice == '2':
            print("\n选择数据类型:")
            print("1. 纯数值数据")
            print("2. 纯文本数据")
            print("3. 混合类型数据")
            print("4. 包含日期时间")
            
            data_choice = input("请选择 (1-4): ").strip()
            
            np.random.seed(42)
            if data_choice == '1':
                df = pd.DataFrame({
                    'A': np.random.rand(10),
                    'B': np.random.randint(1, 100, 10),
                    'C': np.random.randn(10)
                })
                run_single_test("纯数值数据", df, verbose=True)
                
            elif data_choice == '2':
                df = pd.DataFrame({
                    '文本1': [f'文本_{i}' for i in range(10)],
                    '文本2': [f'数据_{i}' for i in range(10)],
                    '文本3': [f'记录_{i}' for i in range(10)]
                })
                run_single_test("纯文本数据", df, verbose=True)
                
            elif data_choice == '3':
                df = pd.DataFrame({
                    'ID': range(1, 11),
                    '姓名': [f'用户{i}' for i in range(1, 11)],
                    '年龄': np.random.randint(18, 60, 10),
                    '城市': np.random.choice(['北京', '上海', '广州'], 10),
                    '收入': np.random.randint(3000, 20000, 10),
                    '活跃': np.random.choice([True, False], 10)
                })
                run_single_test("混合类型数据", df, verbose=True)
                
            elif data_choice == '4':
                df = pd.DataFrame({
                    '日期': pd.date_range('2023-01-01', periods=10),
                    '时间': pd.date_range('2023-01-01', periods=10, freq='H').time,
                    '数值': np.random.randn(10)
                })
                run_single_test("日期时间数据", df, verbose=True)
                
        elif choice == '3':
            print("🚀 运行压力测试...")
            # 生成 10 万行数据
            np.random.seed(42)
            large_df = pd.DataFrame({
                'ID': range(1, 100001),
                '数据': np.random.randn(100000),
                '标签': np.random.choice(['X', 'Y', 'Z'], 100000)
            })
            run_single_test("压力测试_10万行", large_df, verbose=False)
            
        elif choice == '4':
            print("👋 退出交互式测试")
            break
            
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    print("开始测试ESP按键功能...")
    
    # 测试按键4（开始计时）
    test_key_press(4)
    time.sleep(2)
    
    # 测试按键5（测试延迟）
    test_key_press(5)
    time.sleep(2)
    
    # 测试停止计时
    stop_func = shared_functions.get_stop_timing()
    if stop_func:
        stop_func()
    else:
        print("错误：停止计时函数未注册")
        
    print("🔧 Excel Writer 测试工具")
    print("=" * 40)
    
    # 检查依赖
    print("检查依赖库...")
    try:
        import openpyxl
        print(f"✅ openpyxl 版本: {openpyxl.__version__}")
    except ImportError:
        print("❌ 缺少 openpyxl 库，请安装: pip install openpyxl")
    
    # 选择测试模式
    print("\n选择测试模式:")
    print("1. 运行全面测试")
    print("2. 交互式测试")
    print("3. 只测试基础功能")
    
    mode = input("请输入模式 (1-3): ").strip()
    
    if mode == '1':
        run_comprehensive_test()
    elif mode == '2':
        interactive_test()
    elif mode == '3':
        # 只测试基础功能
        np.random.seed(42)
        basic_df = pd.DataFrame({
            '测试列1': [1, 2, 3, 4, 5],
            '测试列2': ['A', 'B', 'C', 'D', 'E'],
            '测试列3': [10.5, 20.3, 30.1, 40.8, 50.2]
        })
        run_single_test("基础功能测试", basic_df, verbose=True)
    else:
        print("❌ 无效模式，默认运行全面测试")
        run_comprehensive_test()
    
    print("\n✨ 测试完成!")
