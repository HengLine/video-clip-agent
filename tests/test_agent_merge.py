#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试video_editor_agent的视频合并功能
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hengline.agent.video_editor_agent import VideoEditorAgent, GraphState
from hengline.logger import debug, info, warning, error

# 配置日志
import logging
# 使用绝对路径确保日志文件保存在正确位置
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(project_root, 'logs', 'agent_merge_test.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger('agent_merge_test')

def test_agent_merge():
    """
    测试VideoEditorAgent的视频编辑功能
    """
    try:
        # 获取测试视频路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        video1 = os.path.join(project_root, "data", "temp", "clip_42aceb63.mp4")
        video2 = os.path.join(project_root, "data", "temp", "clip_f2ae744a.mp4")
        
        # 检查视频文件是否存在
        logger.info(f"检查视频1: {video1}")
        if not os.path.exists(video1):
            logger.error(f"错误: 找不到视频文件 {video1}")
            return False
        
        logger.info(f"检查视频2: {video2}")
        if not os.path.exists(video2):
            logger.error(f"错误: 找不到视频文件 {video2}")
            return False
        
        # 创建模拟的GraphState
        # 这里简化处理，直接创建一个包含clip_points和config的字典
        mock_state = {
            'clip_points': {
                video1: [(0, None)],  # None表示整个视频
                video2: [(0, None)]
            },
            'config': {
                'merge_mode': 'sequential',
                'use_transition': False,
                'temp_dir': os.path.join(project_root, 'data', 'temp'),
                'render_config': {
                    # 使用新格式的配置
                    'width': 1280,
                    'height': 720,
                    'resize_mode': 'fit',
                    'framerate': 30,
                    'codec': 'libx264',
                    'preset': 'fast',
                    'crf': 28
                }
            }
        }
        
        # 转换为GraphState（如果需要）
        # 如果GraphState只是简单的字典包装，可以直接使用mock_state
        state = GraphState(**mock_state)
        
        logger.info("初始化VideoEditorAgent...")
        agent = VideoEditorAgent()
        
        logger.info("开始执行视频编辑流程...")
        logger.info(f"配置信息: {json.dumps(mock_state['config'], ensure_ascii=False, indent=2)}")
        
        # 执行视频编辑
        result = agent.edit_videos(state)
        
        # 检查结果
        if 'error' in result:
            logger.error(f"视频编辑失败: {result['error']}")
            return False
        
        if 'final_video_path' in result:
            final_path = result['final_video_path']
            logger.info(f"✓ 视频编辑成功!")
            logger.info(f"最终视频路径: {final_path}")
            
            # 验证输出文件
            if os.path.exists(final_path):
                size = os.path.getsize(final_path) / (1024 * 1024)
                logger.info(f"✓ 输出文件验证成功，大小: {size:.2f} MB")
                return True
            else:
                logger.error("✗ 最终视频文件不存在")
                return False
        else:
            logger.error("✗ 视频编辑结果中没有final_video_path")
            logger.info(f"详细结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False
            
    except Exception as e:
        logger.error(f"执行测试时出错: {str(e)}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_agent_merge()
    if success:
        logger.info("测试成功完成!")
        sys.exit(0)
    else:
        logger.error("测试失败!")
        sys.exit(1)