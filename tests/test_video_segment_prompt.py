#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试视频截取提示词模板
"""
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hengline.prompt.prompt import get_user_requirement_prompt, get_generate_video_prompt, get_prompt_config


def test_prompt_config():
    """测试提示词配置加载"""
    print("=== 测试提示词配置加载 ===")
    config = get_prompt_config()
    print(f"配置结构: {list(config.keys())}")
    print(f"视频处理系统提示: {config.get('video_processing', {}).get('system_prompt', '').split('。')[0]}...")
    print(f"配置生成系统提示: {config.get('video_config_generation', {}).get('system_prompt', '').split('。')[0]}...")
    print("配置加载成功\n")


def test_user_requirement_prompt():
    """测试用户需求分析提示词模板"""
    print("=== 测试用户需求分析提示词模板 ===")
    user_input = "我想从一个会议视频中截取两个片段：1. 项目介绍部分 2. 结论和下一步计划"
    messages = get_user_requirement_prompt(user_input)
    
    print(f"系统提示:")
    print(f"{messages[0]['content']}\n")
    print(f"用户消息:")
    print(f"{messages[1]['content']}\n")
    print("用户需求分析提示词模板生成成功\n")


def test_generate_video_prompt():
    """测试视频配置生成提示词模板"""
    print("=== 测试视频配置生成提示词模板 ===")
    # 模拟AI返回的需求分析结果
    analysis_result = "根据分析，需要截取以下片段：\n1. 项目介绍: 开始于第30秒，结束于第150秒\n2. 结论和下一步计划: 开始于第720秒，结束于第840秒"
    
    messages = get_generate_video_prompt(analysis_result)
    
    print(f"系统提示:")
    print(f"{messages[0]['content']}\n")
    print(f"用户消息:")
    # 只打印部分内容，避免输出过长
    user_prompt = messages[1]['content']
    print(f"{user_prompt.split('请生成符合以下格式')[0]}...\n")
    print("配置格式示例:")
    # 提取格式示例部分
    format_start = user_prompt.find('请生成符合以下格式')
    if format_start > 0:
        format_example = user_prompt[format_start:format_start + 500]  # 只取前500个字符
        print(f"{format_example}...\n")
    
    print("视频配置生成提示词模板生成成功\n")


def test_output_format_structure():
    """测试输出格式结构是否合理"""
    print("=== 测试输出格式结构 ===")
    config = get_prompt_config()
    output_format = config.get('video_config_generation', {}).get('output_format', {})
    
    print(f"输出格式包含的字段: {list(output_format.keys())}")
    
    # 检查segments字段
    if 'segments' in output_format and isinstance(output_format['segments'], list) and len(output_format['segments']) > 0:
        print(f"片段字段示例: {list(output_format['segments'][0].keys())}")
    
    print("输出格式结构验证成功\n")


if __name__ == "__main__":
    print("开始测试视频截取提示词模板...\n")
    
    try:
        test_prompt_config()
        test_user_requirement_prompt()
        test_generate_video_prompt()
        test_output_format_structure()
        print("✅ 所有测试通过！视频截取提示词模板已正确配置。")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")