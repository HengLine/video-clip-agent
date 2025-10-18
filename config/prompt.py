import json
import os
from typing import Dict, Any

from hengline.logger import error


def get_config_path() -> str:
    """
    获取配置文件路径
    """
    # 获取当前文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 配置文件路径
    config_path = os.path.join(current_dir, 'prompt.json')
    return config_path


global_prompt_config = None


# 加载提示词配置
def get_prompt_config() -> Dict[str, Any]:
    global global_prompt_config
    if global_prompt_config:
        return global_prompt_config

    """加载提示词配置文件"""
    config_path = get_config_path()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            global_prompt_config = json.load(f)
            return global_prompt_config
    except Exception as e:
        error(f"加载提示词配置失败: {str(e)}")
        # 返回默认配置
        return {
            'video_processing': {
                'system_prompt': '你是一个专业的视频处理助手，负责分析用户的视频处理需求。'
            },
            'video_config_generation': {
                'system_prompt': '你是一个专业的视频配置生成助手。'
            }
        }


def get_user_requirement_prompt(user_input) -> list:
    """
    获取用户视频截取需求分析的提示词模板
    
    Args:
        user_input: 用户输入的视频截取需求描述
        
    Returns:
        格式化的消息列表，包含系统提示和用户提示
    """
    prompt_config = get_prompt_config()
    # 从配置文件中获取系统提示词和分段指令
    system_prompt = prompt_config.get('video_processing', {}).get('system_prompt',
                                                                  '你是一个专业的视频处理助手，负责分析用户的视频截取需求。请仔细分析用户描述，识别需要截取的片段信息。')
    segmentation_instructions = prompt_config.get('video_processing', {}).get('segmentation_instructions', '')
    
    # 组合系统提示词，包含分段指令
    enhanced_system_prompt = f"{system_prompt}\n\n{segmentation_instructions}"
    
    # 使用用户的实际输入作为消息内容，优化提问方式
    user_message = f"我需要截取视频中的特定片段，请根据以下需求进行分析：\n{user_input}\n\n请详细分析我的需求，识别出：\n1. 需要截取的片段内容特征\n2. 可能的时间范围线索\n3. 关键识别元素\n4. 视频类型判断\n5. 核心需求理解\n\n请提供清晰的分析结果，帮助系统准确执行视频截取操作。" 

    return [
        {"role": "system", "content": enhanced_system_prompt},
        {"role": "user", "content": user_message}
    ]


def get_generate_video_prompt(user_requirement) -> list:
    """
    获取视频截取配置生成的提示词模板
    
    Args:
        user_requirement: 用户的视频截取需求分析结果
        
    Returns:
        格式化的消息列表，包含系统提示和用户提示
    """
    prompt_config = get_prompt_config()
    # 从配置文件中获取系统提示词
    system_prompt = prompt_config.get('video_config_generation', {}).get('system_prompt',
                                                                         '你是一个专业的视频截取配置生成助手。请根据用户的视频处理需求分析结果，生成符合标准JSON格式的视频截取配置信息。确保输出严格是标准的JSON格式，不要包含任何JSON之外的文本。')
    
    # 从配置文件中获取预定义的输出格式
    output_format_template = prompt_config.get('video_config_generation', {}).get('output_format', {
        "video_type": "精彩集锦",
        "segments": [
            {
                "segment_name": "片段名称",
                "start_time": 0,
                "end_time": 0,
                "reasoning": "选择理由"
            }
        ],
        "merge_segments": True,
        "output_format": "mp4",
        "quality_settings": {
            "resolution": "原分辨率",
            "bitrate": "原比特率"
        }
    })
    
    # 生成格式示例
    output_format = json.dumps(output_format_template, ensure_ascii=False, indent=2)
    
    # 获取字段描述作为额外提示
    field_descriptions = prompt_config.get('video_config_generation', {}).get('field_descriptions', {})
    descriptions_text = "字段说明：\n"
    for field, desc in field_descriptions.items():
        descriptions_text += f"- {field}: {desc}\n"

    user_prompt = f"基于以下视频需求分析结果，请生成视频截取的详细配置：\n\n{user_requirement}\n\n{descriptions_text}\n\n请生成符合以下格式的标准JSON配置：\n{output_format}\n\n重要注意事项：\n1. 严格按照要求的JSON格式输出，不要包含任何JSON之外的文本\n2. segments数组中必须包含所有需要截取的片段\n3. 每个片段必须有明确的数字类型的start_time和end_time（秒）\n4. 确保end_time大于start_time\n5. merge_segments必须设置为true或false\n6. 为每个片段提供详细且有意义的reasoning字段\n7. 请确保生成的JSON可以被标准JSON解析器正确解析"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
