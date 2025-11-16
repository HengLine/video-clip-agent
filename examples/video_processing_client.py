#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@FileName: video_processing_client.py
@Description: 视频处理客户端示例，展示如何使用AI分析技术处理视频
@Author: HengLine
@Time: 2025/11
"""

import os
import requests
import argparse
import json
from datetime import datetime

class VideoProcessingClient:
    """
    视频处理客户端，提供简单易用的接口来调用视频处理服务
    功能包括：
    1. AI分析用户需求
    2. 上传视频文件
    3. 执行视频处理
    4. 下载处理后的视频
    """
    
    def __init__(self, api_base_url="http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            api_base_url: API服务的基础URL
        """
        self.api_base_url = api_base_url
        self.analyze_requirement_url = f"{api_base_url}/api/ai/analyze-requirement"
        self.process_video_url = f"{api_base_url}/api/process-video"
        self.download_video_url = f"{api_base_url}/api/video/"
        
    def analyze_requirement(self, user_query, video_info=None):
        """
        分析用户需求
        
        Args:
            user_query: 用户的视频处理需求描述
            video_info: 视频信息（可选）
            
        Returns:
            分析结果字典
        """
        print(f"分析用户需求: {user_query}")
        
        payload = {
            "user_input": user_query
        }
        
        if video_info:
            payload["video_info"] = video_info
            
        try:
            response = requests.post(self.analyze_requirement_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                print(f"需求分析成功，置信度: {result.get('confidence_score', 'N/A')}")
                print(f"任务类型: {result.get('structured_requirement', {}).get('task_type', 'N/A')}")
                print(f"主要操作: {', '.join(result.get('structured_requirement', {}).get('main_operations', []))}")
                return result
            else:
                print(f"需求分析失败: {result.get('error', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"需求分析请求失败: {str(e)}")
            return None
    
    def process_video(self, user_query, video_paths):
        """
        处理视频
        
        Args:
            user_query: 用户的视频处理需求描述
            video_paths: 视频文件路径列表
            
        Returns:
            处理结果字典，包含输出视频URL或错误信息
        """
        print(f"开始处理视频，查询: {user_query}")
        print(f"输入视频: {', '.join(video_paths)}")
        
        # 准备文件数据
        files = []
        for path in video_paths:
            if not os.path.exists(path):
                print(f"错误: 视频文件不存在: {path}")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(path) / (1024 * 1024)  # MB
            print(f"添加文件: {os.path.basename(path)} ({file_size:.2f}MB)")
            
            # 打开文件并添加到上传列表
            try:
                files.append(('files[]', open(path, 'rb')))
            except Exception as e:
                print(f"无法打开文件 {path}: {str(e)}")
                # 关闭已打开的文件
                for _, file_obj in files:
                    file_obj.close()
                return None
        
        # 准备表单数据
        data = {'query': user_query}
        
        try:
            # 发送请求
            print("正在上传视频并处理...")
            response = requests.post(
                self.process_video_url, 
                files=files, 
                data=data, 
                stream=True  # 启用流式响应以处理大型文件
            )
            
            # 关闭所有文件
            for _, file_obj in files:
                file_obj.close()
            
            # 检查响应
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                video_url = result.get('video_url')
                report = result.get('report', {})
                print("视频处理成功!")
                print(f"视频URL: {video_url}")
                if report:
                    print("质量报告:", json.dumps(report, ensure_ascii=False, indent=2))
                return result
            else:
                print(f"视频处理失败: {result.get('message', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"视频处理请求失败: {str(e)}")
            # 确保关闭所有文件
            for _, file_obj in files:
                file_obj.close()
            return None
    
    def download_video(self, video_filename, output_dir="."):
        """
        下载处理后的视频
        
        Args:
            video_filename: 视频文件名
            output_dir: 输出目录
            
        Returns:
            下载的文件路径，或None（如果失败）
        """
        # 构建完整的下载URL
        download_url = f"{self.download_video_url}{video_filename}"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名（添加时间戳避免覆盖）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(video_filename)
        output_filename = f"{base_name}_{timestamp}{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"正在下载视频到: {output_path}")
        
        try:
            # 流式下载大文件
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 显示下载进度
                            if total_size > 0:
                                progress = downloaded_size / total_size * 100
                                print(f"下载进度: {progress:.1f}% ({downloaded_size/1024/1024:.2f}MB/{total_size/1024/1024:.2f}MB)", end="\r")
                
            print("\n视频下载完成!")
            return output_path
            
        except Exception as e:
            print(f"视频下载失败: {str(e)}")
            # 如果文件已部分下载，尝试删除
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return None

def main():
    """
    主函数，演示如何使用视频处理客户端
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='视频处理客户端')
    parser.add_argument('--videos', '-v', nargs='+', required=True, help='输入视频文件路径')
    parser.add_argument('--query', '-q', required=True, help='视频处理需求描述')
    parser.add_argument('--analyze-only', action='store_true', help='仅分析需求，不执行视频处理')
    parser.add_argument('--output-dir', '-o', default='output_videos', help='输出目录')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API服务URL')
    
    args = parser.parse_args()
    
    # 初始化客户端
    client = VideoProcessingClient(api_base_url=args.api_url)
    
    # 分析需求
    result = client.analyze_requirement(args.query)
    if not result or not result.get('success'):
        print("需求分析失败，退出程序")
        return 1
    
    # 如果只是分析模式，直接退出
    if args.analyze_only:
        print("需求分析完成，已启用--analyze-only模式，程序退出")
        return 0
    
    # 处理视频
    process_result = client.process_video(args.query, args.videos)
    if not process_result or process_result.get('status') != 'success':
        print("视频处理失败，退出程序")
        return 1
    
    # 下载视频
    video_url = process_result.get('video_url')
    if video_url:
        # 从URL中提取文件名
        video_filename = video_url.split('/')[-1]
        output_path = client.download_video(video_filename, args.output_dir)
        
        if output_path:
            print(f"\n任务完成!")
            print(f"处理后的视频已保存至: {output_path}")
        else:
            print("下载视频失败")
            return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)