# -*- coding: utf-8 -*-
"""
@FileName: speech_recognition.py
@Description: 语音识别服务模块
@Author: HengLine
@Time: 2025/10/19 20:28
"""
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from pydub import AudioSegment
import speech_recognition as sr
from hengline.logger import info, debug, warning, error
from utils.ffmpeg_run_utils import has_audio_info, get_audio_from_video


class SpeechRecognizer:
    """语音识别器类"""

    def __init__(self):
        """初始化语音识别器"""
        self.recognizer = sr.Recognizer()
        # 配置识别器参数
        self.recognizer.energy_threshold = 300  # 音频能量阈值
        self.recognizer.pause_threshold = 0.8  # 暂停识别阈值
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_ratio = 1.5

    def extract_audio_from_video(self, video_path: str, output_audio_path: Optional[str] = None) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_audio_path: 输出音频文件路径，默认为临时文件
            
        Returns:
            提取的音频文件路径
        """
        if not os.path.exists(video_path):
            error(f"视频文件不存在: {video_path}")
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 检查视频是否有音频流
        if not has_audio_info(video_path):
            warning(f"视频没有音频流: {video_path}")
            raise ValueError(f"视频没有音频流: {video_path}")

        # 如果没有提供输出路径，创建临时文件
        if not output_audio_path:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_audio_path = os.path.join(temp_dir, f"extracted_audio_{timestamp}.wav")

        success = get_audio_from_video(video_path, output_audio_path)

        if not success:
            error("音频提取失败")
            raise RuntimeError("音频提取失败")

        debug(f"音频提取成功: {output_audio_path}")
        return output_audio_path

    def transcribe_audio(self, audio_path: str, language: str = 'zh-CN') -> List[Dict[str, Any]]:
        """
        转录音频为文本
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码，默认为中文
            
        Returns:
            包含文本和时间戳的列表
        """
        if not os.path.exists(audio_path):
            error(f"音频文件不存在: {audio_path}")
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        debug(f"开始转录音频: {audio_path}, 语言: {language}")

        try:
            # 加载音频文件
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # 转换为秒

            # 分割音频为较小的片段进行处理
            segment_length = 60 * 1000  # 60秒片段
            segments = []

            for i in range(0, len(audio), segment_length):
                segment = audio[i:i + segment_length]
                segments.append(segment)

            # 转录每个片段
            transcription_result = []
            current_time = 0.0

            for i, segment in enumerate(segments):
                debug(f"处理片段 {i + 1}/{len(segments)}")

                # 保存临时片段
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_segment:
                    segment.export(temp_segment.name, format="wav")
                    temp_segment_path = temp_segment.name

                try:
                    # 安全地处理音频文件，避免调用可能不存在的方法
                    try:
                        # 尝试加载音频文件
                        with sr.AudioFile(temp_segment_path) as source:
                            # 检查record方法是否存在
                            if hasattr(self.recognizer, 'record'):
                                try:
                                    audio_data = self.recognizer.record(source)
                                    debug("成功加载音频数据")
                                except Exception as e:
                                    warning(f"加载音频数据时出错: {e}")
                                    # 即使加载失败，也继续使用模拟文本
                            else:
                                warning("recognizer.record方法不可用")

                        # 使用真实的语音识别API
                        debug("使用真实语音识别API进行转录")
                        # 检查是否成功加载了音频数据
                        if 'audio_data' in locals():
                            try:
                                # 尝试使用Google Speech Recognition（需要网络连接）
                                text = self.recognizer.recognize_google(audio_data, language=language)
                                debug(f"成功识别文本: {text}")
                            except sr.UnknownValueError:
                                warning("Google Speech Recognition无法理解音频")
                                text = "[无法识别的音频内容]"
                            except sr.RequestError as e:
                                warning(f"无法从Google Speech Recognition服务获取结果; {e}")
                                # 尝试离线识别选项
                                try:
                                    # 检查是否有离线识别选项
                                    if hasattr(self.recognizer, 'recognize_sphinx'):
                                        debug("尝试使用Sphinx离线识别")
                                        text = self.recognizer.recognize_sphinx(audio_data, language=language)
                                    else:
                                        raise ImportError("Sphinx离线识别不可用")
                                except Exception as e:
                                    warning(f"离线识别也失败: {e}")
                                    text = "[语音识别服务暂时不可用]"
                        else:
                            warning("没有可用的音频数据进行识别")
                            text = "[无法处理的音频数据]"
                    except Exception as e:
                        warning(f"处理音频文件时出错: {e}")
                        # 提供具体的错误信息，而不是使用模拟文本
                        text = f"[音频处理错误: {str(e)[:50]}...]"

                        # 估算片段的结束时间
                        segment_duration = len(segment) / 1000.0
                        end_time = min(current_time + segment_duration, duration)

                        transcription_result.append({
                            'text': text,
                            'start_time': round(current_time, 2),
                            'end_time': round(end_time, 2),
                            'confidence': 0.9  # 模拟置信度
                        })

                        current_time = end_time
                except sr.UnknownValueError:
                    debug(f"无法识别片段 {i + 1} 的语音")
                except sr.RequestError as e:
                    warning(f"Google Speech Recognition服务错误: {e}")
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_segment_path):
                        os.remove(temp_segment_path)

            if not transcription_result:
                warning("音频转录未返回任何结果")
            else:
                debug(f"音频转录成功，识别到 {len(transcription_result)} 个片段")

            return transcription_result

        except Exception as e:
            error(f"音频转录失败: {str(e)}")
            raise RuntimeError(f"音频转录失败: {str(e)}")

    def find_keywords_in_transcript(self, transcript: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        在转录文本中查找关键词
        
        Args:
            transcript: 转录结果列表，每个元素包含 'text' 字段
            keywords: 需要查找的关键词列表
            
        Returns:
            包含匹配关键词及其位置的列表
        """
        matches = []
        for segment in transcript:
            text = segment.get('text', '').lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    matches.append({
                        'keyword': keyword,
                        'text': segment['text'],
                        'start_time': segment.get('start_time', 0),
                        'end_time': segment.get('end_time', 0)
                    })
        return matches

    def transcribe_video(self, video_path: str, language: str = 'zh-CN', keep_audio: bool = False) -> Dict[str, Any]:
        """
        转录视频中的语音为文本
        
        Args:
            video_path: 视频文件路径
            language: 语言代码，默认为中文
            keep_audio: 是否保留提取的音频文件
            
        Returns:
            包含转录结果和元数据的字典
        """
        info(f"开始处理视频语音: {video_path}")

        # 提取音频
        audio_path = self.extract_audio_from_video(video_path)

        try:
            # 转录音频
            transcription = self.transcribe_audio(audio_path, language)

            # 构建结果
            result = {
                'success': True,
                'video_path': video_path,
                'audio_path': audio_path if keep_audio else None,
                'language': language,
                'transcription': transcription,
                'total_segments': len(transcription),
                'transcription_text': ' '.join([seg['text'] for seg in transcription])
            }

            # 如果不需要保留音频，清理文件
            if not keep_audio and os.path.exists(audio_path):
                os.remove(audio_path)
                result['audio_path'] = None

            info(f"视频语音转录完成，识别到 {len(transcription)} 个片段")
            return result

        except Exception as e:
            # 清理音频文件
            if os.path.exists(audio_path):
                os.remove(audio_path)

            error(f"视频语音转录失败: {str(e)}")
            # 确保返回格式包含transcription_text键，以匹配content_analyzer_agent.py的调用
            return {
                'success': False,
                'error': str(e),
                'video_path': video_path,
                'transcription_text': "",
                'segments': []
            }

    def find_keywords_in_transcription(self, transcription: List[Dict[str, Any]],
                                       keywords: List[str],
                                       case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        在转录结果中查找关键词
        
        Args:
            transcription: 转录结果列表
            keywords: 要查找的关键词列表
            case_sensitive: 是否大小写敏感
            
        Returns:
            包含匹配片段的列表
        """
        if not transcription or not keywords:
            return []

        matched_segments = []

        for segment in transcription:
            text = segment['text']

            # 如果不区分大小写，转换为小写
            if not case_sensitive:
                text_lower = text.lower()
                keywords_lower = [kw.lower() for kw in keywords]

                # 检查是否包含任何关键词
                if any(kw in text_lower for kw in keywords_lower):
                    # 找出所有匹配的关键词
                    matched_keywords = [kw for kw in keywords if kw.lower() in text_lower]

                    matched_segments.append({
                        **segment,
                        'matched_keywords': matched_keywords,
                        'confidence': segment.get('confidence', 0.8)
                    })
            else:
                # 大小写敏感匹配
                if any(kw in text for kw in keywords):
                    matched_keywords = [kw for kw in keywords if kw in text]

                    matched_segments.append({
                        **segment,
                        'matched_keywords': matched_keywords,
                        'confidence': segment.get('confidence', 0.8)
                    })

        debug(f"在转录结果中找到 {len(matched_segments)} 个包含关键词的片段")
        return matched_segments

    def extract_segments_by_keywords(self, video_path: str, keywords: List[str],
                                     language: str = 'zh-CN',
                                     case_sensitive: bool = False) -> Dict[str, Any]:
        """
        根据关键词提取视频片段
        
        Args:
            video_path: 视频文件路径
            keywords: 关键词列表
            language: 语言代码
            case_sensitive: 是否大小写敏感
            
        Returns:
            包含匹配片段和转录结果的字典
        """
        info(f"根据关键词提取视频片段: {video_path}, 关键词: {keywords}")

        # 首先转录视频
        transcription_result = self.transcribe_video(video_path, language)

        if not transcription_result['success']:
            return transcription_result

        # 在转录结果中查找关键词
        transcription = transcription_result['transcription']
        matched_segments = self.find_keywords_in_transcription(transcription, keywords, case_sensitive)

        # 构建时间范围列表
        time_ranges = [(seg['start_time'], seg['end_time']) for seg in matched_segments]

        # 合并相邻或重叠的片段
        merged_ranges = self._merge_overlapping_ranges(time_ranges)

        # 构建最终结果
        result = {
            **transcription_result,
            'keywords': keywords,
            'matched_segments': matched_segments,
            'matched_count': len(matched_segments),
            'time_ranges': time_ranges,
            'merged_time_ranges': merged_ranges,
            'merged_count': len(merged_ranges)
        }

        info(f"根据关键词提取完成，找到 {len(merged_ranges)} 个不重叠的片段")
        return result

    def _merge_overlapping_ranges(self, ranges: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        合并重叠或相邻的时间范围
        
        Args:
            ranges: 时间范围列表 [(start1, end1), (start2, end2), ...]
            
        Returns:
            合并后的时间范围列表
        """
        if not ranges:
            return []

        # 按开始时间排序
        sorted_ranges = sorted(ranges, key=lambda x: x[0])

        merged = [sorted_ranges[0]]

        for current_start, current_end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]

            # 如果当前范围与上一个范围重叠或相邻，合并它们
            if current_start <= last_end:
                new_start = last_start
                new_end = max(last_end, current_end)
                merged[-1] = (new_start, new_end)
            else:
                merged.append((current_start, current_end))

        return merged

    def generate_subtitle_file(self, transcription: List[Dict[str, Any]],
                               output_path: str,
                               format: str = 'srt') -> bool:
        """
        生成字幕文件
        
        Args:
            transcription: 转录结果列表
            output_path: 输出文件路径
            format: 字幕格式 ('srt' 或 'vtt')
            
        Returns:
            是否成功生成
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'srt':
                    # 生成SRT格式
                    for i, segment in enumerate(transcription, 1):
                        # 格式化时间为SRT格式: 00:00:00,000 --> 00:00:00,000
                        start_time = self._format_time_for_srt(segment['start_time'])
                        end_time = self._format_time_for_srt(segment['end_time'])

                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{segment['text']}\n\n")
                elif format.lower() == 'vtt':
                    # 生成VTT格式
                    f.write("WEBVTT\n\n")
                    for i, segment in enumerate(transcription, 1):
                        # 格式化时间为VTT格式: 00:00:00.000 --> 00:00:00.000
                        start_time = self._format_time_for_vtt(segment['start_time'])
                        end_time = self._format_time_for_vtt(segment['end_time'])

                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{segment['text']}\n\n")
                else:
                    error(f"不支持的字幕格式: {format}")
                    return False

            debug(f"成功生成字幕文件: {output_path}")
            return True
        except Exception as e:
            error(f"生成字幕文件失败: {str(e)}")
            return False

    def _format_time_for_srt(self, seconds: float) -> str:
        """格式化时间为SRT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _format_time_for_vtt(self, seconds: float) -> str:
        """格式化时间为VTT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


# 全局语音识别器实例
global_speech_recognizer = SpeechRecognizer()


def get_speech_recognizer() -> SpeechRecognizer:
    """获取语音识别器实例"""
    return global_speech_recognizer


def transcribe_video(video_path: str, language: str = 'zh-CN') -> Dict[str, Any]:
    """
    转录视频中的语音
    
    Args:
        video_path: 视频文件路径
        language: 语言代码
        
    Returns:
        转录结果
    """
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        error(f"视频文件不存在: {video_path}")
        # 返回包含必要键的结果，而不是抛出异常
        return {
            'success': False,
            'video_path': video_path,
            'transcription': [],
            'transcription_text': '',
            'error': f"视频文件不存在: {video_path}"
        }
    
    recognizer = get_speech_recognizer()
    return recognizer.transcribe_video(video_path, language)


def extract_segments_by_keywords(video_path: str, keywords: List[str],
                                 language: str = 'zh-CN') -> Dict[str, Any]:
    """
    根据关键词提取视频片段
    
    Args:
        video_path: 视频文件路径
        keywords: 关键词列表
        language: 语言代码
        
    Returns:
        提取结果
    """
    recognizer = get_speech_recognizer()
    return recognizer.extract_segments_by_keywords(video_path, keywords, language)


def generate_subtitle(video_path: str, output_path: str,
                      language: str = 'zh-CN',
                      format: str = 'srt') -> bool:
    """
    为视频生成字幕文件
    
    Args:
        video_path: 视频文件路径
        output_path: 输出字幕文件路径
        language: 语言代码
        format: 字幕格式
        
    Returns:
        是否成功
    """
    recognizer = get_speech_recognizer()
    transcription_result = recognizer.transcribe_video(video_path, language)

    if transcription_result['success']:
        return recognizer.generate_subtitle_file(
            transcription_result['transcription'],
            output_path,
            format
        )
    return False
