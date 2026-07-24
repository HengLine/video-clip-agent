#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试data/temp目录下的两个视频文件合并
"""

import os
import sys
import time
import logging
from utils.ffmpeg_utils import FFmpegUtils

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('merge_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('video_merge_test')

def test_specific_merge():
    """
    测试data/temp目录下的两个视频文件合并
    """
    # 获取当前目录和视频文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video1 = os.path.join(current_dir, "data", "temp", "clip_e382add3.mp4")
    video2 = os.path.join(current_dir, "data", "temp", "clip_f2ae744a.mp4")
    
    # 检查视频文件是否存在
    logger.info(f"检查视频文件: {video1}")
    if not os.path.exists(video1):
        logger.error(f"错误: 找不到视频文件 {video1}")
        return
    
    logger.info(f"检查视频文件: {video2}")
    if not os.path.exists(video2):
        logger.error(f"错误: 找不到视频文件 {video2}")
        return
    
    # 输出目录
    output_dir = os.path.join(current_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取视频信息
    try:
        info1 = FFmpegUtils.get_video_info(video1)
        info2 = FFmpegUtils.get_video_info(video2)
        logger.info(f"视频1信息: {info1}")
        logger.info(f"视频2信息: {info2}")
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
    
    # 生成输出文件名
    timestamp = int(time.time())
    output_file = os.path.join(output_dir, f"merged_test_{timestamp}.mp4")
    
    # 配置参数 - 尝试简化配置以减少变量
    config = {
        'width': 1280,  # 降低分辨率以加快处理速度
        'height': 720,
        'resize_mode': 'fit',
        'codec': 'libx264',
        'preset': 'fast',  # 使用更快的预设
        'crf': 28,  # 稍微降低质量以加快处理
        'framerate': 30
    }
    
    logger.info(f"开始合并测试...")
    logger.info(f"配置参数: {config}")
    logger.info(f"输出文件: {output_file}")
    
    try:
        # 执行合并
        start_time = time.time()
        result = FFmpegUtils.render_video([video1, video2], output_file, config)
        end_time = time.time()
        
        logger.info(f"✓ 合并成功! 耗时: {end_time - start_time:.2f} 秒")
        logger.info(f"结果文件: {result}")
        
        # 验证输出文件
        if os.path.exists(result):
            size = os.path.getsize(result) / (1024 * 1024)
            logger.info(f"✓ 输出文件验证成功，大小: {size:.2f} MB")
            
            # 验证结果文件信息
            try:
                result_info = FFmpegUtils.get_video_info(result)
                logger.info(f"合并后视频信息: {result_info}")
            except Exception as e:
                logger.error(f"获取合并结果信息失败: {str(e)}")
        else:
            logger.error("✗ 输出文件不存在")
            
    except Exception as e:
        logger.error(f"✗ 合并失败: {str(e)}")
        # 打印详细的异常信息
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")
    
    logger.info("测试完成! 请检查日志和输出文件。")

if __name__ == "__main__":
    test_specific_merge()