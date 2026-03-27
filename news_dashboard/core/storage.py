from sqlalchemy import text
from config.db_config import engine
from datetime import datetime

class NewsStorage:
    def __init__(self):
        self.engine = engine
    
    def save_article_via_procedure(self, article):
        """
        单条保存：调用超级存储过程完成所有逻辑（校验/识别/索引都在SQL层）
        同时保存media（图片/视频）
        """
        conn = self.engine.connect()
        try:
            # 调用一站式存储过程（长度检查/去重/国家识别/分类/索引都在内部完成）
            conn.execute(
                text("""
                    CALL sp_save_news_complete(
                        :title, :content, :source_url, :source_id, 
                        :published_at, :language, :hint_country, :hint_category,
                        @out_news_id, @out_status
                    )
                """),
                {
                    'title': article['title'],
                    'content': article['content'],
                    'source_url': article['source_url'],
                    'source_id': article['source_id'],
                    'published_at': article['published_at'],
                    'language': article['language'],
                    'hint_country': article.get('hint_country'),
                    'hint_category': article.get('hint_category')
                }
            )
            
            # 获取存储过程返回状态
            out_result = conn.execute(text("SELECT @out_news_id as news_id, @out_status as status")).fetchone()
            
            if out_result and out_result[1] == 'Success':
                news_id = out_result[0]
                
                # 保存media（图片/视频）
                self._save_media(conn, news_id, article)
                
                # 提交事务（关键！否则数据在事务中不可见）
                conn.commit()
                return True, news_id
            else:
                conn.rollback()
                return False, out_result[1] if out_result else 'Unknown error'
                
        except Exception as e:
            conn.rollback()  # 出错时回滚
            return False, f'SQL_Error: {str(e)}'
        finally:
            conn.close()
    
    def _save_media(self, conn, news_id, article):
        """保存媒体文件（图片/视频）到media表"""
        try:
            # 处理图片
            images = article.get('images', [])
            if not images and article.get('image_url'):
                # 如果只有单个image_url，也处理
                images = [{'url': article['image_url'], 'alt': '', 'caption': ''}]
            
            for idx, img in enumerate(images):
                if isinstance(img, dict):
                    url = img.get('url', '')
                    alt = img.get('alt', '') or img.get('caption', '')
                else:
                    url = str(img)
                    alt = ''
                
                if url:
                    conn.execute(
                        text("""
                            INSERT INTO media (news_id, media_type, media_url, is_cover, created_at)
                            VALUES (:news_id, 'image', :url, :is_cover, NOW())
                        """),
                        {
                            'news_id': news_id,
                            'url': url[:800],  # 限制长度
                            'is_cover': (idx == 0)  # 第一张设为封面
                        }
                    )
            
            # 处理视频
            videos = article.get('videos', [])
            for video in videos:
                if isinstance(video, dict):
                    url = video.get('url', '') or video.get('src', '')
                else:
                    url = str(video)
                
                if url:
                    conn.execute(
                        text("""
                            INSERT INTO media (news_id, media_type, media_url, is_cover, created_at)
                            VALUES (:news_id, 'video', :url, FALSE, NOW())
                        """),
                        {
                            'news_id': news_id,
                            'url': url[:800]
                        }
                    )
                    
        except Exception as e:
            print(f"[Media] 保存媒体失败: {str(e)[:50]}")
            # 媒体保存失败不阻断主流程
    
    def save_articles(self, articles):
        """
        批量保存：逐条调用存储过程（利用SQL事务保证单条原子性）
        注意：如需批量事务，需修改存储过程支持多行插入
        """
        success_count = 0
        failed_count = 0
        
        for article in articles:
            success, msg = self.save_article_via_procedure(article)
            if success:
                success_count += 1
            else:
                failed_count += 1
                print(f"[Storage] 跳过: {msg}")
        
        return success_count, failed_count
    
    def delete_news_transaction(self, news_id):
        """
        显式事务删除（大作业要求的"多表删除"演示）
        调用SQL存储过程完成5表级联删除
        """
        conn = self.engine.connect()
        try:
            result = conn.execute(
                text("CALL sp_delete_news_transaction(:news_id, @out_result)"),
                {'news_id': news_id}
            )
            out = conn.execute(text("SELECT @out_result")).fetchone()
            conn.commit()  # 确保提交
            return True, out[0] if out else 'Deleted'
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def cleanup_old_news(self):
        """
        48小时清理：优先使用SQL Event Scheduler自动清理
        此方法作为手动触发备份，调用存储过程
        """
        conn = self.engine.connect()
        try:
            result = conn.execute(text("CALL sp_cleanup_48h()"))
            row = result.fetchone()
            deleted = row[0] if row else 0
            conn.commit()
            print(f"[Cleanup] SQL Event方式清理了 {deleted} 条旧新闻")
            return deleted
        except Exception as e:
            print(f"[Cleanup] SQL Event可能未启用，错误: {e}")
            return 0
        finally:
            conn.close()