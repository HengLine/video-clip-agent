import json
import os
from typing import Dict, Any, List

import yaml
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from hengline.logger import error


def get_config_path():
    """获取配置文件路径（优先使用YAML格式）"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_config_path = os.path.join(current_dir, 'prompt.yaml')

    # 优先使用YAML配置文件
    if os.path.exists(yaml_config_path):
        return yaml_config_path

    # 如果YAML不存在，返回YAML路径（应该存在）
    return yaml_config_path


global_prompt_config = None


class PromptManager:
    """使用LangChain管理提示词模板的类"""

    def __init__(self):
        self.video_processing_template = None
        self.video_config_generation_template = None
        self.config = self._load_yaml_config()  # 先加载配置
        self._initialize_templates()  # 再初始化模板

    def _initialize_templates(self):
        """初始化LangChain提示词模板"""
        try:
            # 尝试从YAML配置文件加载模板

            langchain_templates = self.config.get('langchain_templates', {})

            # 视频处理需求分析的提示词模板
            video_processing_config = langchain_templates.get('video_processing', {})
            if video_processing_config:
                self.video_processing_template = ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template(video_processing_config.get('system_template', '')),
                    HumanMessagePromptTemplate.from_template(video_processing_config.get('human_template', ''))
                ])
            else:
                self._create_default_video_processing_template()

            # 视频配置生成的提示词模板
            video_config_config = langchain_templates.get('video_config_generation', {})
            if video_config_config:
                self.video_config_generation_template = ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template(video_config_config.get('system_template', '')),
                    HumanMessagePromptTemplate.from_template(video_config_config.get('human_template', ''))
                ])
            else:
                self._create_default_video_config_template()

        except Exception as e:
            error(f"从YAML配置加载模板失败，使用默认模板: {str(e)}")
            self._create_default_templates()

    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, 'prompt.yaml')

        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                error(f"加载YAML配置文件失败: {str(e)}")

        return {}

    def _create_default_templates(self):
        """创建默认的LangChain提示词模板"""
        self._create_default_video_processing_template()
        self._create_default_video_config_template()

    def _create_default_video_processing_template(self):
        """创建默认的视频处理模板"""
        self.video_processing_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """你是一个专业的视频截取助手，负责精确分析用户的视频片段截取需求。用户的视频来自本地上传，主要需要从视频中提取精彩、重要或特定内容的片段。请根据用户的描述，识别需要截取的视频片段特征和关键信息，为后续的精确截取提供支持。

当用户描述需要截取的内容时，请识别以下关键信息：
1. 片段的内容特征（对话、动作、场景变化、关键事件等）
2. 可能的时间范围线索（如视频开头、中间、结尾等相对位置）
3. 可用于定位的关键词、短语或视觉元素
4. 用户关注的视频类型（如会议、演讲、教程、娱乐等）
5. 用户的核心需求（如获取精彩集锦、关键信息提取等）"""
            ),
            HumanMessagePromptTemplate.from_template(
                """我需要截取视频中的特定片段，请根据以下需求进行分析：

{user_input}

请详细分析我的需求，识别出：
1. 需要截取的片段内容特征
2. 可能的时间范围线索
3. 关键识别元素
4. 视频类型判断
5. 核心需求理解

请提供清晰的分析结果，帮助系统准确执行视频截取操作。"""
            )
        ])

    def _create_default_video_config_template(self):
        """创建默认的视频配置生成模板"""
        self.video_config_generation_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """你是一个专业的视频截取配置生成助手。请根据用户的视频截取需求分析结果，生成符合标准JSON格式的视频截取配置信息。确保输出严格是标准的JSON格式，不要包含任何JSON之外的文本，包括解释、说明或其他辅助文字。配置必须包含每个片段的准确时间点和详细信息，以确保截取操作的精确执行。"""
            ),
            HumanMessagePromptTemplate.from_template(
                """基于以下视频需求分析结果，请生成视频截取的详细配置：

{user_requirement}

字段说明：
- video_type: 视频的类型，如精彩集锦、会议视频、演讲视频、教程视频等
- segments: 需要截取的视频片段数组，每个片段必须包含名称、时间范围和理由
- segment_name: 片段的描述性名称，清晰表达片段内容和特征
- start_time: 片段开始的时间点（秒），必须使用数字值
- end_time: 片段结束的时间点（秒），必须使用数字值，且大于start_time
- reasoning: 选择该片段的详细理由或说明，阐述片段的重要性
- merge_segments: 是否将所有片段合并为一个视频，必须使用true或false
- output_format: 输出视频的格式，如mp4、mov等
- quality_settings: 视频质量设置，包含分辨率和比特率

请生成符合以下格式的标准JSON配置：
{output_format}

重要注意事项：
1. 严格按照要求的JSON格式输出，不要包含任何JSON之外的文本
2. segments数组中必须包含所有需要截取的片段
3. 每个片段必须有明确的数字类型的start_time和end_time（秒）
4. 确保end_time大于start_time
5. merge_segments必须设置为true或false
6. 为每个片段提供详细且有意义的reasoning字段
7. 请确保生成的JSON可以被标准JSON解析器正确解析"""
            )
        ])

    def get_video_processing_prompt(self, user_input: str) -> List[Dict[str, str]]:
        """获取视频处理需求分析的格式化消息"""
        try:
            messages = self.video_processing_template.format_messages(user_input=user_input)
            return [{"role": "system" if isinstance(msg, SystemMessage) else "user",
                     "content": msg.content} for msg in messages]
        except Exception as e:
            error(f"生成视频处理提示词失败: {str(e)}")
            return self._get_fallback_video_processing_prompt(user_input)

    def get_video_config_generation_prompt(self, user_requirement: str) -> List[Dict[str, str]]:
        """获取视频配置生成的格式化消息"""
        try:
            # 获取输出格式模板
            output_format = self._get_output_format_template()
            messages = self.video_config_generation_template.format_messages(
                user_requirement=user_requirement,
                output_format=output_format
            )
            return [{"role": "system" if isinstance(msg, SystemMessage) else "user",
                     "content": msg.content} for msg in messages]
        except Exception as e:
            error(f"生成视频配置提示词失败: {str(e)}")
            return self._get_fallback_config_generation_prompt(user_requirement)

    def _get_output_format_template(self) -> str:
        """获取输出格式模板的JSON字符串，优先从YAML配置加载"""
        try:
            # 尝试从YAML配置加载
            video_config = self.config.get('video_config_generation', {})
            output_format = video_config.get('output_format')

            if output_format:
                return json.dumps(output_format, ensure_ascii=False, indent=2)
        except Exception as e:
            error(f"从YAML配置加载输出格式失败: {str(e)}")

        # 回退到默认模板
        output_format_template = {
            "video_type": "精彩集锦",
            "segments": [
                {
                    "segment_name": "开场精彩瞬间",
                    "start_time": 0,
                    "end_time": 15,
                    "reasoning": "视频开头的精彩内容，吸引观众注意力"
                },
                {
                    "segment_name": "核心内容",
                    "start_time": 30,
                    "end_time": 60,
                    "reasoning": "包含主要信息或精彩动作的关键片段"
                },
                {
                    "segment_name": "结尾亮点",
                    "start_time": 90,
                    "end_time": 105,
                    "reasoning": "视频结尾部分的重要总结或精彩收束"
                }
            ],
            "merge_segments": True,
            "output_format": "mp4",
            "quality_settings": {
                "resolution": "原分辨率",
                "bitrate": "原比特率"
            }
        }
        return json.dumps(output_format_template, ensure_ascii=False, indent=2)

    def _get_fallback_video_processing_prompt(self, user_input: str) -> List[Dict[str, str]]:
        """获取备用的视频处理提示词（当LangChain失败时使用）"""
        return [
            {
                "role": "system",
                "content": "你是一个专业的视频截取助手，负责精确分析用户的视频片段截取需求。"
            },
            {
                "role": "user",
                "content": f"请分析以下视频截取需求：{user_input}"
            }
        ]

    def _get_fallback_config_generation_prompt(self, user_requirement: str) -> List[Dict[str, str]]:
        """获取备用的配置生成提示词（当LangChain失败时使用）"""
        return [
            {
                "role": "system",
                "content": "你是一个专业的视频截取配置生成助手。请生成标准JSON格式的配置。"
            },
            {
                "role": "user",
                "content": f"基于以下需求生成配置：{user_requirement}"
            }
        ]


# 全局提示词管理器实例
global_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """获取LangChain提示词管理器实例"""
    global global_prompt_manager
    if global_prompt_manager is None:
        global_prompt_manager = PromptManager()
    return global_prompt_manager


def get_prompt_config() -> dict:
    """
    获取提示词配置（仅支持YAML格式）
    
    Returns:
        dict: 提示词配置字典
    """
    config_path = get_config_path()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        error(f"加载提示词配置失败: {str(e)}")
        # 返回默认配置
        return {
            'video_processing': {
                'system_prompt': '你是一个专业的视频截取助手。',
                'segmentation_instructions': '请分析用户的视频截取需求。'
            },
            'video_config_generation': {
                'system_prompt': '你是一个专业的视频截取配置生成助手。',
                'output_format': {},
                'field_descriptions': {}
            }
        }


def get_user_requirement_prompt(user_input) -> list:
    """
    获取用户视频截取需求分析的提示词模板（使用LangChain管理）
    
    Args:
        user_input: 用户输入的视频截取需求描述
        
    Returns:
        格式化的消息列表，包含系统提示和用户提示
    """
    try:
        # 使用LangChain提示词管理器
        prompt_manager = get_prompt_manager()
        return prompt_manager.get_video_processing_prompt(user_input)
    except Exception as e:
        error(f"使用LangChain提示词管理器失败，回退到传统方式: {str(e)}")

        # 回退到原有的JSON配置方式
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
    获取视频截取配置生成的提示词模板（使用LangChain管理）
    
    Args:
        user_requirement: 用户的视频截取需求分析结果
        
    Returns:
        格式化的消息列表，包含系统提示和用户提示
    """
    try:
        # 使用LangChain提示词管理器
        prompt_manager = get_prompt_manager()
        return prompt_manager.get_video_config_generation_prompt(user_requirement)
    except Exception as e:
        error(f"使用LangChain提示词管理器失败，回退到传统方式: {str(e)}")

        # 回退到原有的JSON配置方式
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
