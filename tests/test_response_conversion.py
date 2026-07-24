# -*- coding: utf-8 -*-
"""测试响应转换功能的脚本"""
import os
import sys
from hengline.client.ai_client import global_ai_client
from hengline.tool.requirement_analyzer import get_requirement_analyzer
from hengline.client.client_factory import convert_response
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 导入日志模块以便查看详细信息
from hengline.logger import info, debug, error

if __name__ == "__main__":
    info("开始测试响应转换功能...")
    
    # 直接测试convert_response函数
    def test_direct_response():
        info("\n=== 测试1: 直接检查convert_response函数 ===")
        # 获取一些模拟响应进行测试
        info(f"当前AI客户端提供商: {global_ai_client.provider}")
        
        # 简单测试用户输入，获取原始响应
        user_input = "你好，测试简单响应"
        try:
            # 直接获取原始响应
            provider_config = global_ai_client.config.get(global_ai_client.provider, {})
            model = provider_config.get('model', 'qwen-plus')
            messages = [{"role": "user", "content": user_input}]
            raw_response = global_ai_client.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0
            )
            
            info(f"原始响应类型: {type(raw_response)}")
            info(f"原始响应内容: {str(raw_response)}")
            
            # 检查响应的属性
            if hasattr(raw_response, 'choices') and raw_response.choices:
                info(f"choices属性存在: {len(raw_response.choices)}")
                first_choice = raw_response.choices[0]
                info(f"第一个choice类型: {type(first_choice)}")
                
                if hasattr(first_choice, 'message'):
                    info(f"message属性存在")
                    message = first_choice.message
                    info(f"message类型: {type(message)}")
                    
                    if hasattr(message, 'content'):
                        info(f"content属性存在")
                        info(f"content类型: {type(message.content)}")
                        info(f"content值: {message.content}")
                    else:
                        error("message对象没有content属性")
                else:
                    error("choice对象没有message属性")
            else:
                error("响应对象没有有效的choices属性")
            
            # 直接测试convert_response
            converted = convert_response(global_ai_client.provider, raw_response)
            info(f"convert_response结果类型: {type(converted)}")
            info(f"convert_response结果: {str(converted)}")
            
        except Exception as e:
            error(f"直接测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 测试主要功能
    def test_main_functions():
        info("\n=== 测试2: 测试主要功能方法 ===")
        try:
            # 测试AI客户端的分析功能
            info("测试AI客户端的analyze_user_requirement方法...")
            user_input = "我需要剪辑一个10分钟的游戏视频集锦，保留精彩时刻"
            ai_result = global_ai_client.analyze_user_requirement(user_input)
            info(f"AI分析结果类型: {type(ai_result)}")
            info(f"AI分析结果: {ai_result[:100]}..." if ai_result else "AI分析结果为空")
            
            # 测试视频配置生成功能
            info("测试AI客户端的generate_video_config方法...")
            video_config = global_ai_client.generate_video_config(user_input)
            info(f"视频配置生成: {'成功' if video_config else '失败'}")
            
        except Exception as e:
            error(f"主要功能测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    try:
        # 运行测试
        test_direct_response()
        test_main_functions()
        
    except Exception as e:
        error(f"测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()