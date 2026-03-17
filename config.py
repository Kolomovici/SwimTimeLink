"""
Excel数据处理应用配置文件
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

class Config:
    """配置管理类"""
    
    # 应用配置
    APP_CONFIG = {
        "app_title": "Excel数据处理工具",
        "app_description": "上传Excel文件，选择需要处理的列，配置处理规则，下载处理后的文件",
        "page_icon": "📊",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "max_upload_size_mb": 200,
        "supported_file_types": [".xlsx", ".xls"],
    }
    
    # 数据处理配置
    PROCESSING_CONFIG = {
        "default_sheet_name": None,  # 默认处理第一个工作表
        "default_processing_mode": "keyword",  # 默认处理模式：keyword/replace/transform
        "default_output_suffix": "_processed",
        "preserve_original_formatting": True,
        "auto_adjust_column_width": True,
        "create_backup": True,
    }
    
    # 关键词处理配置
    KEYWORD_CONFIG = {
        "case_sensitive": False,
        "match_whole_word": False,
        "highlight_color": "FFFF00",  # 黄色高亮
        "add_comment": True,
        "comment_text": "关键词匹配",
    }
    
    # 替换处理配置
    REPLACE_CONFIG = {
        "preserve_case": True,
        "regex_enabled": False,
        "match_entire_cell": False,
    }
    
    # 转换处理配置
    TRANSFORM_CONFIG = {
        "trim_whitespace": True,
        "remove_duplicates": False,
        "sort_ascending": True,
    }
    
    # 列配置
    COLUMN_CONFIG = {
        "default_columns_to_process": [],  # 空列表表示处理所有列
        "exclude_columns": ["序号", "ID", "编号"],  # 默认排除的列
        "date_columns": ["日期", "时间", "创建时间", "更新时间"],  # 日期列识别
        "numeric_columns": ["数量", "金额", "价格", "分数"],  # 数值列识别
    }
    
    # 输出配置
    OUTPUT_CONFIG = {
        "output_format": "xlsx",
        "encoding": "utf-8",
        "include_metadata": True,
        "metadata_fields": ["处理时间", "处理规则", "操作人员"],
    }
    
    # UI配置
    UI_CONFIG = {
        "theme": {
            "primary_color": "#1E88E5",
            "background_color": "#FFFFFF",
            "secondary_background_color": "#F0F2F6",
            "text_color": "#262730",
            "font": "sans serif",
        },
        "sidebar": {
            "collapsible": True,
            "default_collapsed": False,
        },
        "notifications": {
            "show_success": True,
            "show_warnings": True,
            "show_errors": True,
            "auto_close_delay": 3,  # 秒
        },
    }
    
    # 性能配置
    PERFORMANCE_CONFIG = {
        "chunk_size": 1000,  # 分块处理大小
        "max_workers": 4,  # 最大工作线程数
        "cache_ttl": 300,  # 缓存时间（秒）
        "enable_progress_bar": True,
    }
    
    # 安全配置
    SECURITY_CONFIG = {
        "allowed_file_extensions": [".xlsx", ".xls"],
        "max_file_size": 200 * 1024 * 1024,  # 200MB
        "sanitize_filenames": True,
        "validate_input": True,
    }
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "app": cls.APP_CONFIG,
            "processing": cls.PROCESSING_CONFIG,
            "keyword": cls.KEYWORD_CONFIG,
            "replace": cls.REPLACE_CONFIG,
            "transform": cls.TRANSFORM_CONFIG,
            "column": cls.COLUMN_CONFIG,
            "output": cls.OUTPUT_CONFIG,
            "ui": cls.UI_CONFIG,
            "performance": cls.PERFORMANCE_CONFIG,
            "security": cls.SECURITY_CONFIG,
        }
    
    @classmethod
    def save_to_yaml(cls, filepath: str = "config.yaml"):
        """保存配置到YAML文件"""
        config_data = cls.get_all_config()
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def load_from_yaml(cls, filepath: str = "config.yaml"):
        """从YAML文件加载配置"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                # 更新配置
                for section, values in config_data.items():
                    if hasattr(cls, f"{section.upper()}_CONFIG"):
                        getattr(cls, f"{section.upper()}_CONFIG").update(values)


# 创建配置实例
config = Config()

# 尝试加载外部配置文件
try:
    config.load_from_yaml()
except Exception as e:
    print(f"加载配置文件失败，使用默认配置: {e}")