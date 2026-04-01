/**
 * 新闻详情页面
 * 显示单条新闻的完整内容，包括标题、时间、正文、图片和视频
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Calendar, Globe, ExternalLink, Image as ImageIcon, Play } from 'lucide-react';
import { getNewsDetail } from '../utils/api';
import { getCountryInfo } from '../utils/countryCoords';

export default function NewsDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);
  const videoRef = useRef(null);

  // 加载新闻详情
  useEffect(() => {
    loadNewsDetail();
  }, [id]);

  const loadNewsDetail = async () => {
    setLoading(true);
    try {
      const data = await getNewsDetail(id);
      setNews(data);
      // 如果有图片，默认选中封面图
      if (data.images && data.images.length > 0) {
        const coverImage = data.images.find(img => img.is_cover) || data.images[0];
        setSelectedImage(coverImage);
      }
    } catch (error) {
      console.error('Load news detail error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 返回上一页
  const handleBack = () => {
    navigate(-1);
  };

  // 格式化日期
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取视频嵌入URL
  const getVideoEmbedUrl = (video) => {
    const { url, type } = video;
    
    if (type === 'youtube') {
      // 提取 YouTube 视频ID
      const match = url.match(/(?:youtube\.com\/embed\/|youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
      if (match) {
        return `https://www.youtube.com/embed/${match[1]}`;
      }
    }
    
    if (type === 'bilibili') {
      // 提取 Bilibili BV号
      const match = url.match(/bv([a-zA-Z0-9]+)/i);
      if (match) {
        return `https://player.bilibili.com/player.html?bvid=BV${match[1]}`;
      }
    }
    
    return url;
  };

  // 渲染视频播放器
  const renderVideoPlayer = (video, index) => {
    const { url, type } = video;
    const embedUrl = getVideoEmbedUrl(video);

    // 外部嵌入视频 (YouTube, Bilibili, etc.)
    if (type === 'youtube' || type === 'bilibili' || type === 'embed') {
      return (
        <div key={index} className="video-embed-container">
          <iframe
            src={embedUrl}
            title={`Video ${index + 1}`}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full aspect-video rounded-xl"
          />
        </div>
      );
    }

    // HLS 视频流
    if (type === 'hls') {
      return (
        <div key={index} className="video-player-container">
          <video
            ref={videoRef}
            controls
            className="w-full rounded-xl"
            poster={news.images?.[0]?.url}
          >
            <source src={url} type="application/x-mpegURL" />
            您的浏览器不支持 HLS 视频播放
          </video>
        </div>
      );
    }

    // 默认 MP4 视频
    return (
      <div key={index} className="video-player-container">
        <video
          ref={videoRef}
          controls
          className="w-full rounded-xl"
          poster={news.images?.[0]?.url}
        >
          <source src={url} type="video/mp4" />
          您的浏览器不支持视频播放
        </video>
      </div>
    );
  };

  // 渲染正文内容（按段落分割）
  const renderContent = (content) => {
    if (!content) return null;
    
    const paragraphs = content.split('\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => (
      <motion.p
        key={index}
        className="text-white/80 leading-relaxed mb-4 text-base"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 + index * 0.05 }}
      >
        {paragraph}
      </motion.p>
    ));
  };

  if (loading) {
    return (
      <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-3 border-[#00d4ff] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-white/60">加载中...</p>
        </div>
      </div>
    );
  }

  if (!news) {
    return (
      <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center">
          <p className="text-white/60 text-lg mb-4">新闻未找到</p>
          <button
            onClick={handleBack}
            className="px-6 py-2 glass rounded-full text-white hover:bg-white/10 transition-all"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  const countryInfo = getCountryInfo(news.country_code);

  return (
    <div className="relative w-full min-h-screen bg-[#0a0a0f]">
      {/* 背景装饰 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#00d4ff]/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#00d4ff]/5 rounded-full blur-3xl" />
      </div>

      {/* 顶部导航栏 */}
      <motion.header
        className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <motion.button
            onClick={handleBack}
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors"
            whileHover={{ x: -5 }}
            whileTap={{ scale: 0.95 }}
          >
            <ArrowLeft size={20} />
            <span>返回</span>
          </motion.button>
          
          <div className="flex items-center gap-4">
            {news.source_url && (
              <a
                href={news.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-[#00d4ff] hover:text-[#00d4ff]/80 transition-colors text-sm"
              >
                <span>查看原文</span>
                <ExternalLink size={14} />
              </a>
            )}
          </div>
        </div>
      </motion.header>

      {/* 主内容区 */}
      <main className="relative z-10 pt-24 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          {/* 新闻标题区 */}
          <motion.section
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* 来源和元信息 */}
            <div className="flex flex-wrap items-center gap-3 mb-4">
              {countryInfo && (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 text-white/70 text-sm">
                  <span className="text-lg">{countryInfo.emoji}</span>
                  <span>{countryInfo.name}</span>
                </span>
              )}
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 text-white/70 text-sm">
                <Globe size={14} />
                <span>{news.source_name}</span>
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 text-white/70 text-sm">
                <Calendar size={14} />
                <span>{formatDate(news.published_at)}</span>
              </span>
            </div>

            {/* 标题 */}
            <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight">
              {news.title}
            </h1>

            {/* 摘要 */}
            {news.summary && news.summary !== news.title && (
              <motion.p
                className="mt-4 text-lg text-white/60 italic border-l-4 border-[#00d4ff]/50 pl-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {news.summary}
              </motion.p>
            )}
          </motion.section>

          {/* 图片画廊 */}
          {news.images && news.images.length > 0 && (
            <motion.section
              className="mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              {/* 主图 */}
              <div className="relative rounded-2xl overflow-hidden glass mb-4">
                {selectedImage ? (
                  <img
                    src={selectedImage.url}
                    alt={selectedImage.caption || news.title}
                    className="w-full max-h-[500px] object-cover"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/800x400?text=Image+Not+Available';
                    }}
                  />
                ) : (
                  <div className="w-full h-64 flex items-center justify-center bg-white/5">
                    <ImageIcon size={48} className="text-white/30" />
                  </div>
                )}
                {selectedImage?.caption && (
                  <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                    <p className="text-white/80 text-sm">{selectedImage.caption}</p>
                  </div>
                )}
              </div>

              {/* 缩略图列表 */}
              {news.images.length > 1 && (
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {news.images.map((img, index) => (
                    <motion.button
                      key={index}
                      onClick={() => setSelectedImage(img)}
                      className={`flex-shrink-0 w-24 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                        selectedImage === img
                          ? 'border-[#00d4ff]'
                          : 'border-transparent hover:border-white/30'
                      }`}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <img
                        src={img.url}
                        alt={img.caption || `Image ${index + 1}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/100x60?text=NA';
                        }}
                      />
                    </motion.button>
                  ))}
                </div>
              )}
            </motion.section>
          )}

          {/* 视频播放器 */}
          {news.videos && news.videos.length > 0 && (
            <motion.section
              className="mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <h3 className="text-white/80 font-medium mb-4 flex items-center gap-2">
                <Play size={20} className="text-[#00d4ff]" />
                相关视频
              </h3>
              <div className="space-y-4">
                {news.videos.map((video, index) => renderVideoPlayer(video, index))}
              </div>
            </motion.section>
          )}

          {/* 正文内容 */}
          <motion.section
            className="glass rounded-2xl p-6 md:p-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <article className="prose prose-invert max-w-none">
              {renderContent(news.content)}
            </article>
          </motion.section>

          {/* 底部信息 */}
          <motion.footer
            className="mt-8 pt-6 border-t border-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4 text-sm text-white/50">
                <span>来源: {news.source_name}</span>
                {news.country_name && (
                  <span>地区: {news.country_name}</span>
                )}
              </div>
              
              {news.source_url && (
                <a
                  href={news.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] hover:bg-[#00d4ff]/30 transition-colors text-sm"
                >
                  <span>阅读原文</span>
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          </motion.footer>
        </div>
      </main>
    </div>
  );
}
