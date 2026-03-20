from sqlalchemy import text
from config.db_config import engine
from datetime import datetime

class NewsStorage:
    def __init__(self):
        self.engine = engine
    
    def save_articles(self, articles):
        """
        批量保存新闻及关联关系（使用TiDB兼容的SQL）
        注意：TiDB支持标准MySQL语法，但建议避免过大的事务
        """
        if not articles:
            return 0
        
        # 过滤None值（来自process_article跳过的空数据）
        articles = [a for a in articles if a is not None]
        if not articles:
            return 0
        
        conn = self.engine.connect()
        transaction = conn.begin()
        
        try:
            saved_count = 0
            
            for article in articles:
                # 再次验证content和summary不能同时为空
                content = (article.get('content') or '').strip()
                summary = (article.get('summary') or '').strip()
                
                if not content and not summary:
                    continue
                
                # 1. 检查是否已存在（基于title + source_url的组合去重，更强）
                check_sql = text("SELECT news_id FROM news WHERE source_url = :url LIMIT 1")
                result = conn.execute(check_sql, {'url': article['source_url']})
                existing = result.fetchone()
                
                if existing:
                    # 已存在则跳过（或更新）
                    continue
                
                # 2. 插入主表
                insert_news_sql = text("""
                    INSERT INTO news (title, summary, content, source_url, source_id, 
                            published_at, language, has_video, created_at)
                    VALUES (:title, :summary, :content, :source_url, :source_id, 
                           :published_at, :language, :has_video, NOW())
                """)
                
                # 确定语言
                lang = 'zh' if any('\u4e00' <= c <= '\u9fff' for c in article['title']) else 'en'
                
                has_video = bool(article.get('videos'))
                result = conn.execute(insert_news_sql, {
                    'title': article['title'][:300],
                    'summary': article['summary'][:1000] if article['summary'] else None,
                    'content': article.get('content', '')[:20000],  # 全文，限制2万字防止过大
                    'source_url': article['source_url'][:800],
                    'source_id': 1,  # 默认source_id，实际应从sources表查询或创建
                    'published_at': article['published_at'],
                    'language': lang,
                    'has_video': has_video
                })
                
                news_id = result.lastrowid
                if not news_id:
                    continue
                
                # 3. 插入国家关联
                for country_code, is_primary, score in article['countries']:
                    nc_sql = text("""
                        INSERT INTO news_countries (news_id, country_code, is_primary, mention_count)
                        VALUES (:news_id, :country_code, :is_primary, :score)
                    """)
                    conn.execute(nc_sql, {
                        'news_id': news_id,
                        'country_code': country_code,
                        'is_primary': is_primary,
                        'score': int(score)
                    })
                
                # 4. 插入分类关联
                for cat_code, confidence in article['categories']:
                    # 查询category_id
                    cat_id_sql = text("SELECT category_id FROM categories WHERE category_code = :code")
                    cat_result = conn.execute(cat_id_sql, {'code': cat_code})
                    cat_row = cat_result.fetchone()
                    
                    if cat_row:
                        cat_sql = text("""
                            INSERT INTO news_categories (news_id, category_id, confidence)
                            VALUES (:news_id, :cat_id, :confidence)
                        """)
                        conn.execute(cat_sql, {
                            'news_id': news_id,
                            'cat_id': cat_row[0],
                            'confidence': confidence
                        })
                
                # 5. 插入媒体（图片/视频）：支持单图、多图、视频流
                cover_set = False

                if article.get('image_url'):
                    media_sql = text("""
                        INSERT INTO media (news_id, media_type, media_url, is_cover)
                        VALUES (:news_id, 'image', :url, TRUE)
                    """)
                    conn.execute(media_sql, {
                        'news_id': news_id,
                        'url': article['image_url'][:800]
                    })
                    cover_set = True

                if article.get('images'):
                    image_items = article['images']
                    if isinstance(image_items, str):
                        image_items = [image_items]

                    for idx, img_item in enumerate(image_items):
                        img_url = ''
                        if isinstance(img_item, str):
                            img_url = img_item.strip()
                        elif isinstance(img_item, dict):
                            img_url = str(img_item.get('url', '') or img_item.get('src', '')).strip()
                        else:
                            continue

                        if not img_url:
                            continue

                        safe_url = img_url[:800]
                        media_sql = text("""
                            INSERT INTO media (news_id, media_type, media_url, is_cover)
                            VALUES (:news_id, 'image', :url, :is_cover)
                        """)
                        conn.execute(media_sql, {
                            'news_id': news_id,
                            'url': safe_url,
                            'is_cover': (not cover_set and idx == 0)
                        })
                        if not cover_set and idx == 0:
                            cover_set = True

                if article.get('videos'):
                    video_items = article['videos']
                    if isinstance(video_items, str):
                        video_items = [video_items]

                    # 去重：收集目标URL列表
                    inserted_videos = set()
                    
                    for vid_item in video_items:
                        vid_url = ''
                        if isinstance(vid_item, str):
                            vid_url = vid_item.strip()
                        elif isinstance(vid_item, dict):
                            vid_url = str(vid_item.get('url', '') or vid_item.get('src', '')).strip()
                        else:
                            continue

                        if not vid_url or vid_url in inserted_videos:
                            continue

                        # 检查数据库中是否已存在
                        check_video_sql = text("""
                            SELECT media_id FROM media 
                            WHERE news_id = :news_id AND media_type = 'video' AND media_url = :url
                        """)
                        existing = conn.execute(check_video_sql, {'news_id': news_id, 'url': vid_url[:800]}).fetchone()
                        if existing:
                            inserted_videos.add(vid_url)
                            continue

                        safe_url = vid_url[:800]
                        media_sql = text("""
                            INSERT INTO media (news_id, media_type, media_url, is_cover)
                            VALUES (:news_id, 'video', :url, FALSE)
                        """)
                        conn.execute(media_sql, {
                            'news_id': news_id,
                            'url': safe_url
                        })
                        inserted_videos.add(vid_url)

                saved_count += 1
                
                # TiDB优化：每50条提交一次，避免大事务
                if saved_count % 50 == 0:
                    transaction.commit()
                    transaction = conn.begin()
            
            transaction.commit()
            print(f"[Storage] 成功保存 {saved_count} 条新闻")
            return saved_count
            
        except Exception as e:
            transaction.rollback()
            print(f"[Storage] 保存失败: {e}")
            raise
        finally:
            conn.close()
    
    def cleanup_old_news(self):
        """
        清理48小时前的新闻（TiDB支持标准DELETE语法）
        """
        conn = self.engine.connect()
        try:
            # 由于外键级联，先删关联表或依赖外键自动删除
            # 注意：TiDB支持外键约束（需确保创建时定义了ON DELETE CASCADE）
            
            # 清理倒排索引（如果已构建）
            conn.execute(text("""
                DELETE FROM inverted_index 
                WHERE news_id IN (
                    SELECT news_id FROM news 
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL 48 HOUR)
                )
            """))
            
            # 清理主表（关联表自动清理）
            result = conn.execute(text("""
                DELETE FROM news 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL 48 HOUR)
            """))
            
            deleted = result.rowcount
            conn.commit()
            print(f"[Cleanup] 清理了 {deleted} 条过期新闻")
            return deleted
            
        except Exception as e:
            print(f"[Cleanup] 清理失败: {e}")
            raise
        finally:
            conn.close()