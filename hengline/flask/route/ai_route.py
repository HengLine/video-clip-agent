"""
@FileName: ai_route.py
@Description: Flask AI路由模块，提供需求理解和裁剪策略生成API
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import json
from flask import Blueprint, request, jsonify
from hengline.tool.requirement_analyzer_tool import RequirementAnalyzer
from hengline.logger import info, error, debug

app = Blueprint('ai_route', __name__)

# 初始化需求分析器
requirement_analyzer = RequirementAnalyzer()


@app.route('/api/ai/analyze-requirement', methods=['POST'])
def analyze_requirement():
    """
    智能分析用户视频处理需求并生成结构化理解结果
    
    请求体格式:
    {
        "user_input": "用户输入的需求描述",
        "video_info": {
            "duration": 60,          # 视频时长（秒）- 可选
            "resolution": "1920x1080", # 视频分辨率 - 可选
            "file_count": 1          # 文件数量 - 可选
        },
        "requirement_template": {
            "task_type": "",         # 任务类型：剪辑/合并/特效/转场/调色等 - 可选
            "target_effect": "",     # 目标效果描述 - 可选
            "key_focus": "",         # 重点关注区域/内容 - 可选
            "avoid_content": ""      # 需要避开的内容 - 可选
        }
    }
    
    响应格式:
    {
        "success": true,
        "summary": "AI理解的需求摘要",
        "structured_requirement": {
            "task_type": "剪辑",
            "main_operations": ["裁剪", "添加特效"],
            "key_content": ["保留人物面部", "突出关键动作"],
            "video_settings": {
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "duration": "00:01:00"
            },
            "priority_focus": "视频中的主要人物",
            "avoid": ["空白画面", "模糊片段"]
        },
        "suggestions": ["建议使用特写镜头突出主体", "考虑添加转场效果增强连贯性"],
        "confidence_score": 0.95,
        "raw_analysis": "详细的AI分析过程和结果"
    }
    或
    {
        "success": false,
        "error": "错误信息",
        "validation_result": {"valid": false, "reason": "需求描述不完整"},
        "suggested_template": {
            "task_type": "请指定您的主要任务类型",
            "target_effect": "请描述您期望的最终效果",
            "key_focus": "请说明需要重点保留的内容",
            "avoid_content": "请列出需要避开的内容"
        }
    }
    """
    try:
        data = request.get_json()
        
        # 1. 验证请求参数
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        if 'user_input' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要user_input字段'
            }), 400
        
        user_input = data['user_input'].strip()
        if not user_input:
            return jsonify({
                'success': False,
                'error': '用户输入不能为空'
            }), 400
        
        # 2. 获取可选的视频信息和需求模板
        video_info = data.get('video_info', {})
        requirement_template = data.get('requirement_template', {})
        
        # 3. 首先验证需求的有效性
        validation_result = requirement_analyzer.validate_requirement(user_input)
        if not validation_result.get('valid'):
            # 如果需求无效，提供建议的需求模板
            suggested_template = {
                "task_type": "请指定您的主要任务类型（如：剪辑、合并、特效、转场、调色等）",
                "target_effect": "请描述您期望的最终效果",
                "key_focus": "请说明需要重点保留的内容",
                "avoid_content": "请列出需要避开的内容"
            }
            
            return jsonify({
                'success': False,
                'error': validation_result.get('reason', '需求描述不符合要求'),
                'validation_result': validation_result,
                'suggested_template': suggested_template
            }), 400
        
        # 4. 记录分析信息
        log_info = f"开始分析用户需求: {user_input[:100]}..."
        if video_info:
            log_info += f"，视频信息: {video_info}"
        info(log_info)
        
        # 5. 调用需求分析器进行深度分析
        analysis_result = requirement_analyzer.analyze(user_input)
        
        if analysis_result.get('success'):
            # 6. 构建结构化的响应
            # 合并AI分析结果和用户提供的模板信息
            structured_requirement = {
                "task_type": requirement_template.get('task_type', ''),
                "main_operations": [],
                "key_content": [],
                "video_settings": {
                    "aspect_ratio": "16:9",  # 默认值
                    "resolution": video_info.get('resolution', '1920x1080'),
                    "duration": f"{video_info.get('duration', 0):02d}:{video_info.get('duration', 0)//60:02d}:{(video_info.get('duration', 0)%60):02d}"
                },
                "priority_focus": requirement_template.get('key_focus', ''),
                "avoid": []
            }
            
            # 从AI分析结果中提取信息填充结构化需求
            analysis_data = analysis_result.get('analysis', {})
            if isinstance(analysis_data, str):
                # 尝试解析JSON格式的分析结果
                try:
                    analysis_json = json.loads(analysis_data)
                    # 从JSON中提取结构化信息
                    if 'task_type' in analysis_json:
                        structured_requirement['task_type'] = analysis_json['task_type']
                    if 'operations' in analysis_json:
                        structured_requirement['main_operations'] = analysis_json['operations']
                    if 'key_content' in analysis_json:
                        structured_requirement['key_content'] = analysis_json['key_content']
                    if 'avoid' in analysis_json:
                        structured_requirement['avoid'] = analysis_json['avoid']
                    # 提取摘要
                    summary = analysis_json.get('summary', analysis_data)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，使用整个分析结果作为摘要
                    summary = analysis_data
            else:
                summary = str(analysis_data)
            
            # 生成建议
            suggestions = generate_suggestions(structured_requirement)
            
            # 构建最终响应
            return jsonify({
                'success': True,
                'summary': summary,
                'structured_requirement': structured_requirement,
                'suggestions': suggestions,
                'confidence_score': 0.95,  # 可以根据实际分析结果计算置信度
                'raw_analysis': analysis_data,
                'validation_warnings': validation_result.get('warning')
            })
        else:
            error(f"需求分析失败: {analysis_result.get('error', '未知错误')}")
            return jsonify({
                'success': False,
                'error': analysis_result.get('error', '需求分析失败')
            }), 500
            
    except Exception as e:
        error(f"分析需求时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


def generate_suggestions(structured_requirement):
    """
    根据结构化需求生成建议
    
    Args:
        structured_requirement: 结构化的需求对象
        
    Returns:
        建议列表
    """
    suggestions = []
    
    # 根据任务类型提供建议
    task_type = structured_requirement.get('task_type', '').lower()
    if '剪辑' in task_type or '裁剪' in task_type:
        suggestions.append("建议使用精确的时间点进行剪辑，确保视频流畅过渡")
    elif '特效' in task_type:
        suggestions.append("特效不宜过度使用，应与内容风格保持一致")
    elif '合并' in task_type:
        suggestions.append("考虑在视频连接处添加转场效果，增强连贯性")
    
    # 根据焦点内容提供建议
    priority_focus = structured_requirement.get('priority_focus', '')
    if priority_focus:
        suggestions.append(f"建议确保重点关注 '{priority_focus}' 的画面质量和清晰度")
    
    # 根据视频设置提供建议
    video_settings = structured_requirement.get('video_settings', {})
    if video_settings.get('resolution') == '1920x1080':
        suggestions.append("高清分辨率下建议注意细节处理，确保画面质量")
    
    # 默认建议
    if not suggestions:
        suggestions.append("请确保最终视频符合您的预期效果")
    
    return suggestions


@app.route('/api/ai/generate-crop-strategy', methods=['POST'])
def generate_crop_strategy():
    """
    基于用户需求生成裁剪分镜策略
    
    请求体格式:
    {
        "user_input": "用户输入的需求描述",
        "video_info": {
            "duration": 60,  # 视频时长（秒）
            "resolution": "1920x1080"  # 视频分辨率
        }
    }
    
    响应格式:
    {
        "success": true,
        "crop_strategy": {
            "segments": [
                {
                    "start_time": 0,
                    "end_time": 10,
                    "crop_area": "0,0,1920,1080",  # x,y,width,height
                    "focus_point": "960,540",    # 焦点坐标
                    "reason": "保留关键内容"
                }
            ],
            "global_settings": {
                "aspect_ratio": "16:9",
                "maintain_focus": true
            }
        }
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    try:
        data = request.get_json()
        if not data or 'user_input' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要user_input字段'
            }), 400
        
        user_input = data['user_input'].strip()
        if not user_input:
            return jsonify({
                'success': False,
                'error': '用户输入不能为空'
            }), 400
        
        # 获取视频信息（可选）
        video_info = data.get('video_info', {})
        
        # 记录请求信息
        info(f"开始生成裁剪策略，视频信息: {video_info}")
        
        # 调用AI模型生成视频配置（包含裁剪策略）
        from hengline.ai.ai_client import global_ai_client
        video_config = global_ai_client.generate_video_config(user_input)
        
        if video_config:
            # 提取裁剪策略部分，如果不存在则生成默认策略
            crop_strategy = video_config.get('crop_strategy', {})
            
            # 如果裁剪策略为空，生成基本的默认策略
            if not crop_strategy or 'segments' not in crop_strategy:
                duration = video_info.get('duration', 60)
                resolution = video_info.get('resolution', '1920x1080').split('x')
                width = int(resolution[0]) if len(resolution) > 0 else 1920
                height = int(resolution[1]) if len(resolution) > 1 else 1080
                
                crop_strategy = {
                    'segments': [
                        {
                            'start_time': 0,
                            'end_time': duration,
                            'crop_area': f"0,0,{width},{height}",
                            'focus_point': f"{width//2},{height//2}",
                            'reason': "基于用户需求的默认裁剪区域"
                        }
                    ],
                    'global_settings': {
                        'aspect_ratio': "16:9",
                        'maintain_focus': True
                    }
                }
            
            debug(f"成功生成裁剪策略: {json.dumps(crop_strategy, ensure_ascii=False, indent=2)}")
            
            return jsonify({
                'success': True,
                'crop_strategy': crop_strategy
            })
        else:
            error("生成裁剪策略失败，AI模型返回空结果")
            return jsonify({
                'success': False,
                'error': '生成裁剪策略失败'
            }), 500
            
    except Exception as e:
        error(f"生成裁剪策略时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


# 注意：应用裁剪API端点已弃用，裁剪策略现在通过表单提交处理
# 保留此端点以保持向后兼容性
@app.route('/api/ai/apply-crop', methods=['POST'])
def apply_crop():
    """
    应用裁剪策略到视频处理任务（已弃用）
    现在裁剪策略通过表单提交直接处理
    
    请求体格式:
    {
        "task_id": "任务ID",
        "crop_strategy": {
            "segments": [...],
            "global_settings": {}
        },
        "files": ["file1.mp4", "file2.mp4"]
    }
    
    响应格式:
    {
        "success": true,
        "message": "裁剪策略已应用",
        "task_info": {
            "task_id": "任务ID",
            "status": "pending"
        }
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        if 'crop_strategy' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要crop_strategy字段'
            }), 400
        
        # 获取任务信息
        task_id = data.get('task_id', '')
        crop_strategy = data['crop_strategy']
        files = data.get('files', [])
        
        # 验证裁剪策略格式
        if not isinstance(crop_strategy, dict) or 'segments' not in crop_strategy:
            return jsonify({
                'success': False,
                'error': '裁剪策略格式错误'
            }), 400
        
        info(f"应用裁剪策略，任务ID: {task_id}, 文件数: {len(files)}")
        debug(f"裁剪策略详情: {json.dumps(crop_strategy, ensure_ascii=False, indent=2)}")
        
        # 返回成功响应（实际裁剪策略处理现在通过表单提交完成）
        return jsonify({
            'success': True,
            'message': '裁剪策略已成功应用',
            'task_info': {
                'task_id': task_id,
                'status': 'pending',
                'files_count': len(files),
                'segments_count': len(crop_strategy.get('segments', []))
            }
        })
        
    except Exception as e:
        error(f"应用裁剪策略时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


@app.route('/api/ai/providers', methods=['GET'])
def get_ai_providers():
    """
    获取支持的AI模型提供商列表
    
    响应格式:
    {
        "success": true,
        "providers": ["openai", "qwen", "deepseek"],
        "current": "qwen"
    }
    """
    try:
        providers = requirement_analyzer.get_supported_providers()
        current = requirement_analyzer.get_current_provider()
        
        return jsonify({
            'success': True,
            'providers': providers,
            'current': current
        })
    except Exception as e:
        error(f"获取AI提供商列表时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


@app.route('/api/ai/switch-provider', methods=['POST'])
def switch_ai_provider():
    """
    切换AI模型提供商
    
    请求体格式:
    {
        "provider": "qwen"
    }
    
    响应格式:
    {
        "success": true,
        "message": "切换成功",
        "current": "qwen"
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    try:
        data = request.get_json()
        if not data or 'provider' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要provider字段'
            }), 400
        
        provider = data['provider'].strip()
        if not provider:
            return jsonify({
                'success': False,
                'error': '提供商名称不能为空'
            }), 400
        
        success = requirement_analyzer.switch_provider(provider)
        if success:
            info(f"成功切换AI提供商为: {provider}")
            return jsonify({
                'success': True,
                'message': '切换成功',
                'current': provider
            })
        else:
            error(f"切换AI提供商失败: {provider}")
            return jsonify({
                'success': False,
                'error': '切换失败，不支持的提供商'
            }), 400
            
    except Exception as e:
        error(f"切换AI提供商时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500


@app.route('/api/ai/adjust-crop-strategy', methods=['POST'])
def adjust_crop_strategy():
    """
    根据用户反馈调整裁剪分镜策略
    
    请求体格式:
    {
        "original_strategy": {
            "segments": [...],
            "global_settings": {}
        },
        "adjustments": {
            "aspect_ratio": "16:9",  # 可选：调整宽高比
            "maintain_focus": true,   # 可选：是否保持焦点
            "segments": [            # 可选：现有分镜段调整
                {
                    "segment_index": 0,  # 段索引
                    "start_time": 0,     # 可选：调整开始时间
                    "end_time": 10,      # 可选：调整结束时间
                    "crop_area": "0,0,1920,1080",  # 可选：调整裁剪区域
                    "focus_point": "960,540",    # 可选：调整焦点
                    "reason": "新的裁剪原因"  # 可选：调整原因
                }
            ],
            "new_segments": [         # 可选：新增分镜段
                {
                    "start_time": 60,    # 开始时间
                    "end_time": 120,     # 结束时间
                    "crop_area": "0,0,1920,1080",  # 裁剪区域
                    "focus_point": "960,540",    # 焦点位置
                    "reason": "新增分镜段"  # 裁剪原因
                }
            ]
        },
        "user_input": "用户对调整的描述或反馈"
    }
    
    响应格式:
    {
        "success": true,
        "adjusted_strategy": {
            "segments": [...],
            "global_settings": {}
        },
        "adjustment_summary": "策略调整摘要"
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        if 'original_strategy' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要original_strategy字段'
            }), 400
        
        if 'adjustments' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数不完整，需要adjustments字段'
            }), 400
        
        # 获取原始策略和调整信息
        original_strategy = data['original_strategy']
        adjustments = data['adjustments']
        user_input = data.get('user_input', '')
        
        # 验证策略格式
        if not isinstance(original_strategy, dict) or 'segments' not in original_strategy:
            return jsonify({
                'success': False,
                'error': '原始策略格式错误'
            }), 400
        
        info(f"开始调整裁剪策略，调整段数: {len(adjustments.get('segments', []))}")
        debug(f"原始策略: {json.dumps(original_strategy, ensure_ascii=False, indent=2)}")
        debug(f"调整信息: {json.dumps(adjustments, ensure_ascii=False, indent=2)}")
        
        # 创建调整后的策略（深拷贝原始策略）
        import copy
        adjusted_strategy = copy.deepcopy(original_strategy)
        
        # 应用全局设置调整
        if 'global_settings' not in adjusted_strategy:
            adjusted_strategy['global_settings'] = {}
        
        if 'aspect_ratio' in adjustments:
            adjusted_strategy['global_settings']['aspect_ratio'] = adjustments['aspect_ratio']
            
        if 'maintain_focus' in adjustments:
            adjusted_strategy['global_settings']['maintain_focus'] = adjustments['maintain_focus']
        
        # 应用分段调整
        if 'segments' in adjustments and isinstance(adjustments['segments'], list):
            for adjustment in adjustments['segments']:
                segment_index = adjustment.get('segment_index')
                if isinstance(segment_index, int) and 0 <= segment_index < len(adjusted_strategy['segments']):
                    # 应用各种调整
                    for key, value in adjustment.items():
                        if key != 'segment_index':  # 跳过索引本身
                            adjusted_strategy['segments'][segment_index][key] = value
        
        # 处理新增分镜段
        new_segments_count = 0
        if 'new_segments' in adjustments and isinstance(adjustments['new_segments'], list):
            for new_segment in adjustments['new_segments']:
                # 移除segment_index字段（如果存在），因为这是新增的
                if 'segment_index' in new_segment:
                    new_segment = {k: v for k, v in new_segment.items() if k != 'segment_index'}
                
                # 移除is_new标记（如果存在）
                if 'is_new' in new_segment:
                    new_segment = {k: v for k, v in new_segment.items() if k != 'is_new'}
                
                # 添加到策略中
                adjusted_strategy['segments'].append(new_segment)
                new_segments_count += 1
        
        # 生成调整摘要
        adjustment_summary = f"裁剪策略已根据您的要求调整。"
        if adjustments.get('aspect_ratio'):
            adjustment_summary += f" 宽高比已调整为 {adjustments['aspect_ratio']}。"
        if adjustments.get('segments') and len(adjustments['segments']) > 0:
            adjustment_summary += f" 共调整了 {len(adjustments['segments'])} 个分镜段。"
        if new_segments_count > 0:
            adjustment_summary += f" 新增了 {new_segments_count} 个分镜段。"
        
        debug(f"调整后的策略: {json.dumps(adjusted_strategy, ensure_ascii=False, indent=2)}")
        
        return jsonify({
            'success': True,
            'adjusted_strategy': adjusted_strategy,
            'adjustment_summary': adjustment_summary
        })
        
    except Exception as e:
        error(f"调整裁剪策略时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500



