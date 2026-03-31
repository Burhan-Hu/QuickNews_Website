from sqlalchemy import text
from config.db_config import engine
from datetime import datetime
import json

class NewsStorage:
    def __init__(self):
        self.engine = engine
    
    def save_article_with_xml_index(self, article):
        """
        保存文章并构建XML索引（适配新schema）
        流程：1.调用sp_save_news_complete -> 2.调用sp_build_xml_index
        """
        conn = self.engine.connect()
        trans = conn.begin()
        
        try:
            # 步骤1：保存新闻主数据（返回news_id和language）
            result = conn.execute(
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
                    'language': article.get('language', 'zh'),
                    'hint_country': article.get('hint_country'),
                    'hint_category': article.get('hint_category')
                }
            )
            
            # 获取输出参数
            out_result = conn.execute(
                text("SELECT @out_news_id as news_id, @out_status as status")
            ).fetchone()
            
            if not out_result or out_result[1] != 'Success':
                trans.rollback()
                return False, out_result[1] if out_result else 'Insert failed'
            
            news_id = out_result[0]
            detected_lang = article.get('language', 'zh')
            
            # 步骤2：构建XML倒排索引（使用JSON分词结果）
            conn.execute(
                text("CALL sp_build_xml_index(:news_id, :title_terms, :content_terms, :lang)"),
                {
                    'news_id': news_id,
                    'title_terms': article['title_terms_json'],
                    'content_terms': article['content_terms_json'],
                    'lang': detected_lang
                }
            )
            
            # 步骤3：保存媒体文件
            self._save_media(conn, news_id, article)
            
            trans.commit()
            return True, news_id
            
        except Exception as e:
            trans.rollback()
            return False, f'Error: {str(e)}'
        finally:
            conn.close()
    
    def _save_media(self, conn, news_id, article):
        """保存媒体文件到media表"""
        try:
            # 处理图片
            images = article.get('images', [])
            if not images and article.get('image_url'):
                images = [{'url': article['image_url'], 'alt': '', 'caption': ''}]
            
            for idx, img in enumerate(images):
                if isinstance(img, dict):
                    url = img.get('url', '')
                else:
                    url = str(img)
                
                if url:
                    conn.execute(
                        text("""
                            INSERT INTO media (news_id, media_type, media_url, is_cover, created_at)
                            VALUES (:news_id, 'image', :url, :is_cover, NOW())
                        """),
                        {
                            'news_id': news_id,
                            'url': url[:800],
                            'is_cover': (idx == 0)
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
                        {'news_id': news_id, 'url': url[:800]}
                    )
                    
        except Exception as e:
            print(f"[Media] 保存媒体失败: {str(e)[:50]}")
            # 媒体失败不阻断主流程

    def save_articles(self, articles):
        """批量保存：逐条处理以保证XML索引构建"""
        success_count = 0
        failed_count = 0
        
        for article in articles:
            success, msg = self.save_article_with_xml_index(article)
            if success:
                success_count += 1
                if success_count % 10 == 0:
                    print(f"[Storage] 已保存 {success_count} 条...")
            else:
                failed_count += 1
                print(f"[Storage] 跳过: {msg}")
        
        return success_count, failed_count
    
    def cleanup_old_news(self):
        """调用SQL存储过程清理48小时旧数据"""
        conn = self.engine.connect()
        try:
            result = conn.execute(text("CALL sp_cleanup_48h()"))
            row = result.fetchone()
            deleted = row[0] if row else 0
            conn.commit()
            print(f"[Cleanup] 清理了 {deleted} 条旧新闻")
            return deleted
        except Exception as e:
            print(f"[Cleanup] 错误: {e}")
            return 0
        finally:
            conn.close()
            
    def get_unindexed_news(self, hours=6):
        """获取未构建索引的新闻（用于定时任务补充）"""
        conn = self.engine.connect()
        try:
            results = conn.execute(
                text("""
                    SELECT n.news_id, n.title, n.summary, n.language
                    FROM news n
                    LEFT JOIN index_build_logs l ON n.news_id = l.news_id
                    WHERE n.created_at > DATE_SUB(NOW(), INTERVAL :hours HOUR)
                    AND l.log_id IS NULL
                    LIMIT 100
                """),
                {'hours': hours}
            ).fetchall()
            return results
        finally:
            conn.close()